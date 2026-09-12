"""Reproducible reduced-order physical simulation, not hardware qualification.
Run: python simulate.py --out results
Outputs: parameters.json, cases.csv, traces.npz, verification.json, *.png, run.log.
Next: measure torque, belt stiffness, friction, encoder calibration and brake delay;
replace assumptions and rerun before fabrication acceptance. Python + numpy + matplotlib.
"""
import argparse, csv, json, math, time, platform, hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

D = np.pi/180
SEED = 20260912

def case(name, **kw):
    p = dict(name=name, J=.00662, k=20., c=.025, gap=.10*D,
             friction=.015, visc=.008, cable=.008, bias_torque=0.,
             gravity=.005, phase=.4, torque=.18, damping=.008,
             enc_bias=.10*D, enc_harm=.08*D, delay=.005,
             direction=1., amplitude=90., duration=3., start=0.)
    p.update(kw)
    return p

def generate_cases():
    cc=[case('nominal_1kg'),case('light_50g',J=.00085,friction=.005),
        case('heavy_offset',J=.02,k=8,c=.01,gap=.3*D,friction=.04,
             cable=.02,gravity=.0343,bias_torque=.015,enc_bias=.25*D,enc_harm=.15*D),
        case('reverse_heavy',J=.02,direction=-1,friction=.04,cable=.02,gravity=.0343),
        case('full_range',amplitude=320,duration=10.,J=.02,start=-160)]
    # Deterministic extremes include BOTH light/heavy loads and minimum damping.
    import itertools
    for n,(J,k,fr,sgn) in enumerate(itertools.product([.00075,.02],[8.,40.],[.005,.04],[-1.,1.])):
        cc.append(case(f'corner_{n:02}',J=J,k=k,c=.01,friction=fr,
                       gap=.3*D,cable=.02,gravity=.0343,bias_torque=.015*sgn,
                       enc_bias=.25*D*sgn,enc_harm=.15*D,damping=.003,direction=sgn))
    rng=np.random.default_rng(SEED)
    for n in range(128):
        cc.append(case(f'sweep_{n:03}',J=rng.uniform(.00075,.02),
            k=rng.uniform(8,40),c=rng.uniform(.01,.05),gap=rng.uniform(0,.3)*D,
            friction=rng.uniform(.005,.04),visc=rng.uniform(.003,.015),
            cable=rng.uniform(.002,.02),bias_torque=rng.uniform(-.015,.015),
            gravity=rng.uniform(0,.0343),phase=rng.uniform(-np.pi,np.pi),
            torque=rng.uniform(.18,.27),damping=rng.uniform(.003,.015),
            enc_bias=rng.uniform(-.25,.25)*D,enc_harm=rng.uniform(0,.15)*D,
            delay=float(rng.choice([.002,.005,.010])),direction=float(rng.choice([-1,1]))))
    return cc

def run(cc,dt=.0002,T=4.5,profile='normal',log=print):
    p={k:np.array([v[k] for v in cc]) for k in cc[0] if k!='name'}
    n=len(cc); jm=5.4e-6*16+2e-5; eta=.9; ratio=4; teeth=50
    # x = rotor angle / ratio, q = output angle. Both in output-shaft radians.
    y=np.zeros((4,n)); off=np.zeros(n); vel=np.zeros(n); cmd=np.zeros(n)
    y[0]=p['start']*D; y[2]=p['start']*D; cmd=p['start']*D
    pulse=D*1.8/16/ratio; enc=2*np.pi/16384
    ctrl=.001; tick=round(ctrl/dt); delay=np.rint(p['delay']/ctrl).astype(int)
    hist=np.zeros((max(delay)+1,n)); hp=0; maxphase=np.zeros(n)
    hist[:]=p['start']*D
    holding=np.zeros(n,dtype=bool)
    maxbelt=np.zeros(n); maxtorque=np.zeros(n)
    st=[]; sy=[]; sr=[]; sc=[]; sb=[]; se=[]; sm=[]
    def forces(z,command):
        x,v,q,w=z
        delta=x-q
        contact=np.maximum(np.abs(delta)-p['gap']/2,0)*np.sign(delta)
        belt=p['k']*contact + np.where(np.abs(delta)>p['gap']/2,p['c']*(v-w),0)
        # Effective dynamic torque envelope is an ASSUMPTION, not holding torque.
        # Conservative roll-off beyond rated simulation range (40 motor rpm).
        rpm=np.abs(v)*ratio*60/(2*np.pi)
        cap=p['torque']*np.minimum(1,40/np.maximum(rpm,40))
        tm=eta*ratio*cap*np.sin(teeth*ratio*(command-x))
        resistance=p['friction']*np.tanh(w/.002)+p['visc']*w+p['cable']*q
        resistance+=p['bias_torque']+p['gravity']*np.sin(q+p['phase'])
        return belt,tm,resistance
    def rhs(z,command):
        belt,tm,res=forces(z,command)
        return np.array([z[1],(tm-belt-p['damping']*z[1])/jm,
                         z[3],(belt-res)/p['J']])
    for i in range(round(T/dt)+1):
        t=i*dt
        trajectory_duration=np.full(n,3.) if profile=='stop' else p['duration']
        u=np.minimum(t/trajectory_duration,1)
        ref=p['start']*D+p['direction']*p['amplitude']*D*(10*u**3-15*u**4+6*u**5)
        refvel=p['direction']*p['amplitude']*D/trajectory_duration*(30*u**2-60*u**3+30*u**4)
        if profile=='reversal':
            if t<4: begin,end,t0,duration=0,90,0,3
            elif t<11: begin,end,t0,duration=90,-90,4,6
            else: begin,end,t0,duration=-90,0,11,3
            s=np.clip((t-t0)/duration,0,1)
            ref=np.full(n,(begin+(end-begin)*(10*s**3-15*s**4+6*s**5))*D)
            refvel=np.full(n,(end-begin)/duration*(30*s*s-60*s**3+30*s**4)*D)
        if profile=='stop' and t>=1.5:
            s=min(t-1.5,56.25/90)
            ref=np.full(n,(45+56.25*s-.5*90*s*s)*D)
            refvel=np.full(n,(56.25-90*s)*D)
        if i%tick==0:
            meas=y[2]+p['enc_bias']+p['enc_harm']*np.sin(2*y[2]+p['phase'])
            # Bounded deterministic sensor noise; avoids dt-dependent random draws.
            meas+=.015*D*np.sin(2*np.pi*73*t+np.arange(n))
            meas=np.round(meas/enc)*enc
            hist[hp]=meas
            delayed=hist[(hp-delay)%len(hist),np.arange(n)]
            hp=(hp+1)%len(hist)
            err=ref-delayed
            holding &= np.abs(err)<.5*D
            holding |= (t>=p['duration']) & (np.abs(err)<.4*D) & (np.abs(vel)<.5*D)
            corr=np.where(np.abs(err)>.08*D,np.clip(1.5*err,-2*D,2*D),0)
            corr=np.where(holding,0,corr)
            off=np.clip(off+corr*ctrl,-2*D,2*D)
            desired=ref+off
            # Pulse command velocity/acceleration limiter also bounds feedback action.
            vd=np.clip(refvel+20*(desired-cmd),-60*D,60*D)
            vd=np.where(holding,0,vd)
            vel+=np.clip(vd-vel,-90*D*ctrl,90*D*ctrl)
        cmd=cmd+vel*dt
        quant=np.round(cmd/pulse)*pulse
        belt,tm,res=forces(y,quant)
        phase=np.abs(teeth*ratio*(quant-y[0]))
        maxphase=np.maximum(maxphase,phase)
        maxbelt=np.maximum(maxbelt,np.abs(belt)); maxtorque=np.maximum(maxtorque,np.abs(tm))
        if i%tick==0:
            st.append(t);sy.append(y.copy());sr.append(ref.copy());sc.append(quant.copy())
            sb.append(belt.copy());se.append(phase.copy());sm.append(tm.copy())
        if i<round(T/dt):
            a=rhs(y,quant);b=rhs(y+dt*a/2,quant);c=rhs(y+dt*b/2,quant);d=rhs(y+dt*c,quant)
            y+=dt*(a+2*b+2*c+d)/6
    arr=dict(t=np.array(st),state=np.array(sy),ref=np.array(sr),cmd=np.array(sc),
             belt=np.array(sb),phase=np.array(se),motor_output_torque=np.array(sm))
    rows=[]
    for j,c in enumerate(cc):
        q=arr['state'][:,2,j]/D;w=arr['state'][:,3,j]/D
        target=c['start']+c['direction']*c['amplitude']
        if profile=='reversal':target=0
        if profile=='stop':target=45+56.25**2/180
        end=arr['t']>=T-.5
        good=(np.abs(q-target)<=1)&(np.abs(w)<=1)
        bad=np.flatnonzero(~good); idx=bad[-1]+1 if len(bad) else 0
        settle=float(arr['t'][idx]) if idx<len(good) and arr['t'][-1]-arr['t'][idx]>=.25 else None
        rows.append(dict(name=c['name'],J=c['J'],final_error_deg=float(q[-1]-target),
            last_500ms_max_error_deg=float(np.max(np.abs(q[end]-target))),
            last_500ms_ripple_deg=float(np.ptp(q[end])),settle_s=settle,
            peak_velocity_deg_s=float(np.max(np.abs(w))),
            max_electrical_lag_deg=float(maxphase[j]/D),
            max_belt_torque_Nm=float(maxbelt[j]),max_motor_output_torque_Nm=float(maxtorque[j]),
            model_sync_margin_ok=bool(maxphase[j]<np.pi/2),
            pass_position=bool(np.max(np.abs(q[end]-target))<=1),
            pass_settle=bool(settle is not None and settle<=c['duration']+.5)))
    return arr,rows

def checks():
    # Independent RK4 validation: undamped oscillator, and free constant acceleration.
    def rk(f,z,h):
        a=f(z);b=f(z+h*a/2);c=f(z+h*b/2);d=f(z+h*c)
        return z+h*(a+2*b+2*c+d)/6
    z=np.array([1.,0.]);h=.0002;om=100.
    for _ in range(5000):z=rk(lambda a:np.array([a[1],-om**2*a[0]]),z,h)
    oscillator_error=abs(z[0]-math.cos(100))
    z=np.array([0.,0.])
    for _ in range(5000):z=rk(lambda a:np.array([a[1],2.]),z,h)
    acceleration_error=abs(z[0]-1)
    assert oscillator_error<1e-6 and acceleration_error<1e-10
    return dict(oscillator_error=oscillator_error,constant_acceleration_error=acceleration_error)

def stops():
    # Independent one-axis worst-case energy model, no helpful friction assumed.
    # Guard speed 65 deg/s covers physical overshoot above 60 deg/s command.
    # Output spring-applied brake torque >= .40 Nm, delay <= 30 ms.
    J=.0201064; v=65*D; assist=.12; delay=.03; brake=.40
    v1=v+assist/J*delay
    xdelay=v*delay+.5*assist/J*delay**2
    xbrake=J*v1*v1/(2*(brake-assist))
    records=[]
    for b in [0,.12,.24,.40,.50]:
        q=0.;w=v;dt=.0001;maxq=0.;stop=None
        series=[]
        for i in range(20001):
            t=i*dt;series.append([t,q/D,w/D]);maxq=max(maxq,q)
            if w>0:
                a=(assist-(b if t>=delay else 0))/J
                wn=max(0,w+a*dt)
                q+=(w+wn)*dt/2;w=wn
                if w==0 and stop is None:stop=t+dt
        records.append(dict(brake_Nm=b,stop_s=stop,travel_deg=maxq/D,trace=series))
    controlled_delay=.01; decel=90*D
    return dict(J=J,initial_speed_deg_s=65,assist_Nm=assist,brake_min_Nm=brake,delay_s=delay,
        analytic_travel_deg=(xdelay+xbrake)/D,
        analytic_stop_s=delay+J*v1/(brake-assist),
        elastic_energy_bound_J=.006,
        elastic_extra_travel_deg=.006/(brake-assist)/D,
        total_with_elastic_and_1p5deg_tolerance=(xdelay+xbrake+.006/(brake-assist))/D+1.5,
        controlled_stop_travel_deg=(v*controlled_delay+v*v/(2*decel))/D,
        records=records)

def plot(arr,rows,out,stop,conv):
    plt.rcParams.update({'font.size':10,'axes.grid':True,'grid.alpha':.22,'figure.dpi':140})
    fig,ax=plt.subplots(2,2,figsize=(11,7),constrained_layout=True)
    for j in range(min(4,len(rows))):
        ax[0,0].plot(arr['t'],arr['state'][:,2,j]/D,label=rows[j]['name'])
        ax[0,1].plot(arr['t'],(arr['state'][:,2,j]-arr['ref'][:,j])/D)
        ax[1,0].plot(arr['t'],arr['state'][:,3,j]/D)
        ax[1,1].plot(arr['t'],arr['belt'][:,j])
    ax[0,0].set(ylabel='Output angle (deg)',title='Nonlinear two-inertia physical model')
    ax[0,0].legend(fontsize=8);ax[0,1].set(ylabel='Reference tracking error (deg)',ylim=(-3,3))
    ax[1,0].set(ylabel='Output velocity (deg/s)',xlabel='Time (s)')
    ax[1,1].set(ylabel='Belt torque (N m)',xlabel='Time (s)')
    fig.savefig(out/'motion.png');plt.close(fig)
    fig,ax=plt.subplots(1,2,figsize=(11,4),constrained_layout=True)
    x=[r['J'] for r in rows];y=[r['last_500ms_max_error_deg'] for r in rows]
    ax[0].scatter(x,y,s=18,c=['#12846b' if r['pass_position'] else '#ca483a' for r in rows])
    ax[0].axhline(1,color='r',ls='--',label='1 deg limit');ax[0].legend()
    ax[0].set(xlabel='Load inertia (kg m2)',ylabel='Final 0.5 s max error (deg)',title=f'{len(rows)} deterministic + seeded cases')
    for rec in stop['records']:
        s=np.array(rec['trace']);ax[1].plot(s[:,0],s[:,1],label=f"Brake {rec['brake_Nm']:.2f} N m")
    ax[1].axhline(10,color='r',ls='--');ax[1].set(xlabel='Time after power loss (s)',ylabel='Travel (deg)',ylim=(0,40),xlim=(0,.8),title='Worst-case power-loss stopping')
    ax[1].legend(fontsize=8);fig.savefig(out/'robustness.png');plt.close(fig)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='results');a=ap.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True);start=time.time()
    logs=[]
    def log(s): print(s,flush=True);logs.append(s)
    cc=generate_cases();(out/'parameters.json').write_text(json.dumps(cc,indent=2),encoding='utf-8')
    log(f'Python {platform.python_version()}; numpy {np.__version__}; seed {SEED}; reduced-order simulation')
    v=checks();log('Independent integrator checks PASS')
    normal=[c for c in cc if c['name']!='full_range']
    arr,rows=run(normal);log(f'Motion cases completed: {len(rows)}')
    full,rr=run([cc[4]],T=11.5);log('320 degree travel completed')
    # Refine time step with identical 1 ms sensor/control clock and noise function.
    fine,fr=run(normal[:3],dt=.0001)
    conv=float(np.max(np.abs(arr['state'][:,2,:3]-fine['state'][:,2,:3]))/D)
    v['dt_refinement_max_angle_difference_deg']=conv
    v['dt_refinement_pass']=conv<.05
    reversal,revrows=run([case('reversal_light',J=.00075,k=40,c=.01,damping=.003,friction=.005,duration=14),case('reversal_heavy',J=.02,gap=.3*D,duration=14)],T=15,profile='reversal')
    stopmotion,stoprows=run([case('controlled_stop',J=.02,duration=2.125)],T=3.5,profile='stop')
    v['reversal_cases']=revrows;v['controlled_stop_case']=stoprows[0]
    np.savez_compressed(out/'reversal.npz',**reversal)
    np.savez_compressed(out/'controlled_stop.npz',**stopmotion)
    # A deliberately weak motor is a negative control; must fail synchronism or positioning.
    neg,negrows=run([case('negative_underpowered',J=.02,torque=.015,friction=.04,cable=.02)])
    v['negative_control']=negrows[0]
    v['negative_control_detected']=not(negrows[0]['model_sync_margin_ok'] and negrows[0]['pass_position'])
    stop=stops();v['stopping']={k:x for k,x in stop.items() if k!='records'}
    v['stopping']['cases']=[{k:x for k,x in r.items() if k!='trace'} for r in stop['records']]
    br=stop['records'][3];v['stopping']['numeric_vs_analytic_deg']=abs(br['travel_deg']-stop['analytic_travel_deg'])
    allrows=rows+rr
    v['case_count']=len(allrows);v['position_pass_count']=sum(r['pass_position'] for r in allrows)
    v['settle_pass_count']=sum(r['pass_settle'] for r in allrows)
    v['sync_margin_pass_count']=sum(r['model_sync_margin_ok'] for r in allrows)
    v['worst_final_error_deg']=max(r['last_500ms_max_error_deg'] for r in allrows)
    v['worst_settle_s_90deg']=max((r['settle_s'] or 999) for r in rows)
    v['worst_electrical_lag_deg']=max(r['max_electrical_lag_deg'] for r in allrows)
    v['worst_belt_torque_Nm']=max(r['max_belt_torque_Nm'] for r in allrows)
    v['model_parameters_are_unmeasured']=True
    v['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with (out/'cases.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=allrows[0].keys());w.writeheader();w.writerows(allrows)
    np.savez_compressed(out/'traces.npz',**arr)
    np.savez_compressed(out/'full_range.npz',**full)
    np.savez_compressed(out/'negative_control.npz',**neg)
    for n in range(4):
        np.savetxt(out/f'trace_{normal[n]["name"]}.csv',np.column_stack([arr['t'],arr['ref'][:,n]/D,arr['state'][:,2,n]/D,arr['state'][:,3,n]/D,arr['belt'][:,n]]),delimiter=',',header='time_s,reference_deg,output_deg,velocity_deg_s,belt_torque_Nm',comments='')
    plot(arr,rows,out,stop,conv)
    (out/'verification.json').write_text(json.dumps(v,indent=2),encoding='utf-8')
    log(json.dumps(v,indent=2));log(f'Elapsed {time.time()-start:.1f} s')
    (out/'run.log').write_text('\n'.join(logs),encoding='utf-8')

if __name__=='__main__':main()
