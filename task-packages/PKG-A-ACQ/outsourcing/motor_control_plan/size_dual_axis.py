"""Dual-axis selection budgets, NOT a dual-axis dynamic or hardware simulation.
Run: python size_dual_axis.py --out results-reproduced-dual-axis
Writes selection_budget.json in a NEW directory. Stdlib only.
Next: verify purchased unit's continuous torque, load inertia and brake delay.
"""
import argparse,json,math,platform,sys,itertools
from pathlib import Path
from datetime import datetime,timezone

def pitch_budget(payload,offset,inertia):
    moving_mass=payload+.2
    gravity=moving_mass*9.81*offset
    demand=inertia*math.radians(60)+gravity+.06+.03+.05
    return dict(payload_kg=payload,moving_mass_kg=moving_mass,cg_offset_m=offset,
        inertia_kg_m2=inertia,gravity_Nm=gravity,demand_Nm=demand,
        required_continuous_with_factor_2_Nm=2*demand,
        passes_1Nm_candidate=2*demand<=1)

def stop_budget(J,v_deg,assist,brake,stored_energy):
    if not all(math.isfinite(x) for x in (J,v_deg,assist,brake,stored_energy)) or J<=0 or min(v_deg,assist,brake,stored_energy)<0:
        raise ValueError('finite nonnegative parameters and positive inertia required')
    delay=.03;v=math.radians(v_deg);v1=v+assist/J*delay
    if brake<=assist:return dict(pass_budget=False,reason='brake cannot overcome worst assisting torque')
    rigid=v*delay+.5*assist/J*delay**2+J*v1*v1/(2*(brake-assist))
    total=math.degrees(rigid+stored_energy/(brake-assist))+1.5
    return dict(J_kg_m2=J,initial_speed_deg_s=v_deg,assist_Nm=assist,
        brake_min_Nm=brake,total_delay_s=delay,stored_energy_J=stored_energy,
        rigid_travel_deg=math.degrees(rigid),travel_with_energy_and_tolerance_deg=total,
        available_deg=10,pass_budget=total<10)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    cases=[pitch_budget(m,e,j) for m,e,j in itertools.product([.05,.5,1.],[.005,.01,.02],[.003,.006,.012])]
    worst=max(cases,key=lambda x:x['demand_Nm'])
    yaw=[dict(inertia_kg_m2=j,demand_Nm=j*math.radians(90)+.06+.03+.05) for j in [.01,.025,.04]]
    # Continuous interval: f(J)=c0+c1*J+c2/J is convex for J>0.
    # Its maximum is at an endpoint. Travel increases with speed, assist,
    # delay and stored energy and decreases with brake torque (B>A).
    # Grid records supplement this endpoint proof; they do not replace it.
    pitch_stops=[dict(payload_kg=m,cg_offset_m=e,**stop_budget(j,35,(m+.2)*9.81*e+.14,.8,.01))
        for m,e,j in itertools.product([0,.05,.5,1.],[0,.005,.01,.02],[.004,.006,.012])]
    yaw_stops=[stop_budget(j,65,.14,.6,.01) for j in [.01,.025,.04]]
    historical_stops=[dict(payload_kg=m,cg_offset_m=e,**stop_budget(j,35,(m+.2)*9.81*e+.14,.8,.01))
        for m,e,j in itertools.product([.05,.5,1.],[.005,.01,.02],[.003,.006,.012])]
    stops={'yaw':max(yaw_stops,key=lambda x:x['travel_with_energy_and_tolerance_deg']),
           'pitch':max(pitch_stops,key=lambda x:x['travel_with_energy_and_tolerance_deg'])}
    counterexample=stop_budget(.003,35,.37544,.8,.01)
    negative=pitch_budget(1,.1,.012)
    weak_brake=stop_budget(.012,35,worst['gravity_Nm']+.06+.03+.05,.2,.01)
    passed=all(c['passes_1Nm_candidate'] for c in cases) and all(2*c['demand_Nm']<=1 for c in yaw)
    passed &= all(c['pass_budget'] for c in pitch_stops+yaw_stops)
    passed &= not counterexample['pass_budget'] and abs(counterexample['travel_with_energy_and_tolerance_deg']-10.983614837439264)<1e-9
    passed &= not negative['passes_1Nm_candidate'] and not weak_brake['pass_budget']
    result={'scope':'analytical sizing and conservative energy budgets only; no coupled dynamics, product or hardware qualification',
        'executed_utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,'platform':platform.platform(),
        'stop_envelope':{'yaw_inertia_kg_m2':[.01,.04],'pitch_inertia_kg_m2':[.004,.012],
            'payload_kg':[0,1],'pitch_accessories_kg':.2,'cg_offset_m':[0,.02],
            'proof':'convex in J, so both endpoints bound each continuous interval; worst upper speed, assisting torque, delay, energy and lower brake torque',
            'restrictions':'total effective output inertia including motor/transmission; no guarantee outside interval; 30ms total delay; speed at fault <=65/35 deg/s; assist <=0.14/0.37544 Nm; energy<=0.01J; tolerance<=1.5deg; dynamic brake>=0.6/0.8Nm throughout stop; 10deg remaining clearance'},
        'pitch_stop_cases':pitch_stops,'yaw_stop_cases':yaw_stops,
        'historical_stop_cases':historical_stops,'retained_low_inertia_failure':counterexample,
        'historical_envelope_pass':all(c['pass_budget'] for c in historical_stops),
        'pitch_cases':cases,'yaw_cases':yaw,'worst_pitch':worst,'stops':stops,
        'negative_offset_100mm':negative,'negative_pitch_brake_0p2Nm':weak_brake,'budget_checks_pass':bool(passed)}
    (a.out/'selection_budget.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps({k:result[k] for k in ['worst_pitch','stops','budget_checks_pass']},indent=2))
    if not passed:raise SystemExit(1)
if __name__=='__main__':main()
