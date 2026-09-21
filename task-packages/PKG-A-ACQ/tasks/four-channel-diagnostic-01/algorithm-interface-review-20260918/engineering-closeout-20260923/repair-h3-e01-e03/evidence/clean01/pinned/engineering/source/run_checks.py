"""Pinned independent math/contract comparisons. No Vivado, board or old full FFT replay."""
import argparse
import ast
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import subprocess
import sys
import traceback
import numpy as np
import engineering_model as em

PINS = dict(main='1f369dc688cc1e49d5b2b51735bce7dc9d1cfb78',
            B='f5a4cea7a7cf7dcccf09720cfff92131e6157752',
            A='f879a54cf40359209895af955bcef92accdf79ea',
            bram='e4f9eae3fe7e4104ff8a6827937e326954f90a82',
            B_new='bb964cbd5b4bee005702bebe6b9cee16d9b885d9',
            B_review='5e343f2d9e9a372ad59bcc618571d4fb0002a7df')
BASE = 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/'
BC = 'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/'


def check(value, message='comparison failed'):
    if not value:
        raise AssertionError(message)


def rejects(fn, text=None):
    try:
        fn()
    except (ValueError, OverflowError) as exc:
        if text:
            check(text in str(exc), str(exc))
        return str(exc)
    raise AssertionError('expected rejection did not occur')


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


def oracle_hann():
    # Independent Decimal Taylor cosine, not the DUT's binary64 math.cos.
    with localcontext() as c:
        c.prec = 65
        pi = Decimal('3.1415926535897932384626433832795028841971693993751058209749445923078')
        result = []
        for i in range(1024):
            x = 2*pi*min(i,1023-i)/1023
            term = total = Decimal(1)
            for k in range(1,90):
                term *= -x*x/((2*k-1)*(2*k))
                total += term
                if abs(term) < Decimal('1e-62'):
                    break
            result.append(int(((1-total)*65536).to_integral_value(rounding=ROUND_HALF_EVEN)))
        return result


def norm_oracle(z):
    with localcontext() as ctx:
        ctx.prec = 80
        mag = Decimal(z[0]*z[0]+z[1]*z[1]).sqrt()
        return tuple(int((Decimal(x)*(1<<23)/mag).to_integral_value(rounding=ROUND_HALF_EVEN)) for x in z)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--inspect-ps', help='Optional existing continuous source directory; read-only snapshot')
    args = ap.parse_args()
    root = Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip())
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    snap = out/'inputs'; snap.mkdir()
    rows, bindings = [], []
    def save(name, obj):
        (out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    def get(pin, path, name):
        data = subprocess.check_output(['git','show',PINS[pin]+':'+path],cwd=root)
        target = snap/name; target.write_bytes(data)
        bindings.append(dict(commit=PINS[pin],path=path,snapshot=name,sha256=hashlib.sha256(data).hexdigest()))
        return target
    def test(name, fn, method='software_integer_or_model'):
        try:
            detail = fn()
            rows.append(dict(name=name,result='PASS',method=method,detail=detail))
        except Exception:
            rows.append(dict(name=name,result='FAIL',method=method,traceback=traceback.format_exc()))
        (out/'raw.log').open('a',encoding='utf-8').write(json.dumps(rows[-1],ensure_ascii=False,default=str)+'\n')
        print(rows[-1]['result'],name, flush=True)
    save('command.json',dict(argv=sys.argv,python=sys.version,numpy=np.__version__,cwd=str(Path.cwd()),pins=PINS,
         source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')}))
    fixed = module(get('B','task-packages/PKG-B-ALG/tasks/h3-complete-20260918/source/fixed_golden.py','fixed_golden.py'),'pinned_fixed')
    phat = module(get('B','task-packages/PKG-B-ALG/tasks/phat-fixed-03/phat_model.py','phat_model.py'),'pinned_phat')
    get('B',BC+'B-RESPONSE-20260923.md','B-response.md')
    get('B_new',BC+'checkpoint-20260923/H3-ALGORITHM-CONTRACT.md','B-new-contract.md')
    get('B_review','docs/reviews/b-checkpoint-bb964cb/REVIEW.md','B-new-review.md')
    gate_path=get('B_new',BC+'checkpoint-20260923/source/integer_gate.py','integer_gate.py')
    get('A',BASE+'increment-20260923/README.md','A-published-README.md')
    get('A',BASE+'increment-20260923/PACKAGE-SHA256.json','A-published-manifest.json')
    if args.inspect_ps:
        for name in ('continuous_core.c','continuous_core.h','main_continuous.c','scene_store.c','scene_store.h'):
            path=Path(args.inspect_ps)/name
            data=path.read_bytes();(snap/('actual-ps-'+name)).write_bytes(data)
            bindings.append(dict(path=str(path),kind='actual_working_source_not_proven_loaded',sha256=hashlib.sha256(data).hexdigest(),snapshot='actual-ps-'+name))
    save('bindings.json',bindings)

    def old_unchanged():
        files = subprocess.check_output(['git','ls-tree','-r','--name-only',PINS['A'],'--',BASE+'increment-20260923'],cwd=root,text=True).splitlines()
        report = []
        for path in files:
            expected = subprocess.check_output(['git','show',PINS['A']+':'+path],cwd=root)
            current = (root/path).read_bytes()
            # Git byte identity ignores working-tree CRLF only for text paths.
            eq = current == expected or (b'\0' not in current and current.replace(b'\r\n',b'\n') == expected.replace(b'\r\n',b'\n'))
            report.append(dict(path=path,git_sha256=hashlib.sha256(expected).hexdigest(),working_sha256=hashlib.sha256(current).hexdigest(),git_content_equal=eq))
        save('f879-preservation.json',report)
        check(all(x['git_content_equal'] for x in report))
        return dict(files=len(report),note='CRLF normalization explicitly permitted; raw hashes retained')
    test('published_increment_preserved',old_unchanged)

    def hann():
        expected = oracle_hann()
        check(fixed.hann_u18f17().tolist() == expected)
        save('hann-oracle.json',expected)
        return dict(coefficients=1024,oracle='65-digit Decimal Taylor cosine + ties-even')
    test('hann_coefficients_independent',hann)
    def window():
        rng = np.random.default_rng(230923)
        x = rng.integers(-(1<<23),1<<23,size=(4,1024),dtype=np.int64)
        x[0] = -(1<<23); x[1] = (1<<23)-1
        coeff = oracle_hann()
        got,ov = fixed.window_pcm(x,np.array(coeff))
        expected = [[round(Fraction(int(x[c,i])*coeff[i],1<<17)) for i in range(1024)] for c in range(4)]
        check(np.array_equal(got,expected) and ov == 0)
        rejects(lambda: fixed.window_pcm(np.full((4,1024),1<<23)))
        rejects(lambda: fixed.window_pcm(x,np.full(1024,(1<<17)+1)))
        return dict(products=4096,negative_cases=2,oracle='Fraction.__round__')
    test('hann_products_and_range',window)
    def crosses():
        rng = random.Random(513)
        cases = [(-(1<<24),-(1<<24),(1<<24)-1,(1<<24)-1)]
        cases += [tuple(rng.randrange(-(1<<24),1<<24) for _ in range(4)) for _ in range(4096)]
        for ar,ai,br,bi in cases:
            # Multiplication matrix independently represents a*conj(b).
            expected = (sum(a*b for a,b in zip((ar,ai),(br,bi))), sum(a*b for a,b in zip((ar,ai),(-bi,br))))
            check(phat.cross((ar,ai),(br,bi)) == expected)
        rejects(lambda: phat.cross((1<<24,0),(1,0)))
        return dict(cases=len(cases),exact=True)
    test('cross_s25_wide_products',crosses)
    def normalization():
        rng = random.Random(474)
        cases = [(1,0),(0,-1),(3,4),(-3,-4),((1<<49),1),(1,(1<<49))]
        cases += [tuple(rng.randrange(-(1<<49),1<<49) for _ in range(2)) for _ in range(2048)]
        maximum=0; histogram={}
        for z in cases:
            got,status = phat.normalize(z)
            expected = norm_oracle(z)
            error = max(abs(a-b) for a,b in zip(got,expected))
            maximum=max(maximum,error); histogram[error]=histogram.get(error,0)+1
            check(error <= 1, f'{z}: {got} != {expected}, error={error}')
            sq=z[0]*z[0]+z[1]*z[1]
            with localcontext() as ctx:
                ctx.prec=80
                mag=int(Decimal(sq*(1<<48)).sqrt().to_integral_value(rounding=ROUND_HALF_EVEN))
            check(status['magnitude_code']==mag)
        check(phat.normalize((0,0))[1]['valid'] is False)
        return dict(cases=len(cases),max_ideal_code_error=maximum,error_histogram=histogram,
                    meaning='sqrt exact; reciprocal approximation versus ideal unit vector, NOT AMD bit equivalence')
    test('phat_sqrt_and_normalize_independent',normalization)
    def phat_invalid():
        a=[(1,0)]*513; band=[7<=i<=85 for i in range(513)]
        check(phat.phat_pair(a,a,band,True)['reason']=='UPSTREAM_IP_OVERFLOW')
        few=[7<=i<18 for i in range(513)]
        check(not phat.phat_pair(a,a,few)['valid'])
        check(phat.phat_pair(a,a,[7<=i<19 for i in range(513)])['valid'])
        check(phat.EPSILON_CODES==Fraction(1<<26,10**15))
        return dict(overflow_rejected=True,epsilon_units='cross amplitude code',min_bins=12)
    test('phat_invalid_pair_state',phat_invalid)
    def conjugate():
        half=np.zeros((513,2),dtype=np.int64)
        half[1:512,0]=np.arange(511); half[1:512,1]=-np.arange(511)
        full=fixed.conjugate_complete(half)
        check(np.array_equal(full[513:,0],half[1:512,0][::-1]))
        check(np.array_equal(full[513:,1],-half[1:512,1][::-1]))
        # Preserve observed missing endpoint validation; do not silently patch B.
        half[0,1]=1
        observed=fixed.conjugate_complete(half)
        check(observed[0,1]==1)
        save('endpoint-counterexample.json',dict(result='EXPECTED_CONTRACT_GAP_REPRODUCED',input_dc_imag=1,output_dc_imag=int(observed[0,1]),required='adapter must reject non-real DC/Nyquist before IFFT'))
        half[:]=0; half[1,1]=-(1<<24)
        bad=fixed.conjugate_complete(half)
        rejects(lambda:fixed.fixed_fft(bad,inverse=True,width=25))
        return dict(mirrored_bins=511,expected_endpoint_gap=True,negative_min_conjugate_rejected_at_fft=True)
    test('ifft_conjugate_and_rejection',conjugate)
    def guard():
        half=[[0,0] for _ in range(513)]
        em.validate_ifft_half(half)
        half[0][1]=1;rejects(lambda:em.validate_ifft_half(half),'NONREAL_ENDPOINT')
        half[0][1]=0;half[512][1]=-1;rejects(lambda:em.validate_ifft_half(half),'NONREAL_ENDPOINT')
        half[512][1]=0;half[7][1]=-(1<<24);rejects(lambda:em.validate_ifft_half(half),'CONJUGATE_OVERFLOW')
        half[7][1]=-(1<<24)+1;em.validate_ifft_half(half)
        return dict(legal=2,rejected=3,scope='new proposed software boundary guard, not B modification')
    test('proposed_ifft_guard',guard)
    def ifft_basis():
        stats=[]
        for index in (0,256,512):
            x=np.zeros((1024,2),dtype=np.int64);x[index,0]=1<<20
            y,status=fixed.fixed_fft(x,inverse=True,width=25)
            # Independent analytic 1024-point inverse basis, no DUT-produced expected.
            expected=np.array([(round(1024*math.cos(2*math.pi*index*n/1024)),round(1024*math.sin(2*math.pi*index*n/1024))) for n in range(1024)])
            check(np.array_equal(y,expected) and status['overflow_count']==0)
            stats.append(dict(bin=index,exact_components=2048))
        return dict(new_inverse_only_cases=stats,forward_fft_reruns=0)
    test('ifft_inverse_scaling_basis',ifft_basis)
    def ifft_overflow():
        values=np.array([((1 if math.cos(2*math.pi*k/1024)>=0 else -1)*((1<<24)-1),
                          (-1 if math.sin(2*math.pi*k/1024)>=0 else 1)*((1<<24)-1)) for k in range(1024)],dtype=np.int64)
        analytic=np.fft.ifft(values[:,0]+1j*values[:,1])
        check(np.max(np.abs(analytic.real))>(1<<24)-1)
        _,status=fixed.fixed_fft(values,inverse=True,width=25)
        check(status['overflow_count']>0)
        return dict(overflow_count=status['overflow_count'],required_action='invalidate pair/frame; do not use saturated output',oracle='independent inverse DFT dynamic-range witness')
    test('ifft_overflow_observed_not_repaired',ifft_overflow)
    def lag():
        cases=0
        for ls in (1,2):
            limit=fixed.physical_limit_q12(ls)
            check(limit*limit*343**2 <= 1920**2*ls*4096**2 < (limit+1)**2*343**2)
            for peak in range(-8,9):
                for left,right in ((7,7),(6,9),(9,6)):
                    c=np.zeros(1024,dtype=np.int64);c[peak%1024]=20;c[(peak-1)%1024]=left;c[(peak+1)%1024]=right
                    r=fixed.lag_q12(c,ls)
                    if abs(peak) <= math.ceil(math.sqrt(ls)*1920/343):
                        delta=round(Fraction(left-right,2*(left-40+right))*4096)
                        check(r['tau_q12']==peak*4096+delta)
                        check(r['valid']==(abs(peak*4096+delta)<=limit))
                    cases+=1
        return dict(cases=cases,oracle='rational parabola and squared physical inequality')
    test('lag_physical_and_interpolation',lag)
    def doa():
        cases=[]
        for deg in (-90,-45,0,45,90):
            ux,uy=math.cos(math.radians(deg)),math.sin(math.radians(deg))
            tau=[round((dx*ux+dy*uy)*1920/343*4096) for dx,dy in fixed.PAIR_DELTAS]
            r=fixed.doa_q20([dict(valid=True,tau_q12=t) for t in tau])
            # Independent Fraction Gaussian elimination, not DUT's closed form.
            a=sum(Fraction(dx*dx) for dx,dy in fixed.PAIR_DELTAS)
            b=sum(Fraction(dx*dy) for dx,dy in fixed.PAIR_DELTAS)
            c=sum(Fraction(dy*dy) for dx,dy in fixed.PAIR_DELTAS)
            d=sum(Fraction(dx*t*343,1920*4096) for (dx,dy),t in zip(fixed.PAIR_DELTAS,tau))
            e=sum(Fraction(dy*t*343,1920*4096) for (dx,dy),t in zip(fixed.PAIR_DELTAS,tau))
            y=(e-b*d/a)/(c-b*b/a);x=(d-b*y)/a
            check((r['ux_q20'],r['uy_q20'])==(round(x*(1<<20)),round(y*(1<<20))))
            check(r['valid'] and abs(r['azimuth_q8_deg']/256-deg)<0.02)
            cases.append(r)
        check(not fixed.doa_q20([dict(valid=False)]*6)['valid'])
        check(not fixed.doa_q20([dict(valid=True,tau_q12=0)]*6)['valid'])
        return dict(cases=cases,angle_tolerance_deg=0.02,meaning='math comparison, not measured direction accuracy')
    test('doa_rational_solution_and_angle',doa)
    def das():
        rng=np.random.default_rng(39);x=rng.integers(-(1<<23),1<<23,size=(4,257),dtype=np.int64)
        delays=[0,2048,-6144,32768];got,status=fixed.das_block(x,delays)
        expected=[]
        for n in range(257):
            total=Fraction(0)
            for ch,d in enumerate(delays):
                p=Fraction(n)-Fraction(d,4096);lo=math.floor(p);f=p-lo
                a=int(x[ch,lo]) if 0<=lo<257 else 0
                b=int(x[ch,lo+1]) if 0<=lo+1<257 else 0
                total += (1-f)*a+f*b
            expected.append(round(total/4))
        check(got.tolist()==expected and status['saturation_count']==0)
        return dict(samples=257,oracle='Fraction piecewise-linear interpolation',edge_policy='zero extension; not valid continuous interior')
    test('das_fractional_signed_delay',das)
    def gate_state():
        tree=ast.parse(gate_path.read_text(encoding='utf-8'))
        node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='IntegerActivity')
        namespace={};exec(compile(ast.Module(body=[node],type_ignores=[]),str(gate_path),'exec'),namespace)
        cfg=dict(on_power_ratio=4,off_power_ratio=2,attack_frames=3,release_frames=3,minimum_active_channels=3,band_rms_floor_codes=512)
        cls=namespace['IntegerActivity'];model=cls([512**2]*4,cfg)
        on=[4*512**2]*3+[0];off=[2*512**2-1]*4
        check([model.update(on) for _ in range(3)]==[False,False,True])
        check([model.update(off) for _ in range(3)]==[True,True,False])
        for _ in range(3): model.update(on)
        check(model.update(on,invalid=True) is False and model.attack==model.release==0)
        large=cls([(1<<64)-1]*4,cfg)
        check([large.update([(1<<64)-1]*4) for _ in range(3)]==[False]*3)
        rejects(lambda:model.update([1<<64]*4),'U64')
        return dict(origin='exact pinned class extracted by AST; stage/FFT not executed',negative_cases=2,
                    expected='explicit 3-on/3-off transition table, widened threshold cannot wrap')
    test('new_B_gate_threshold_state_only',gate_state)

    def owner():
        x=em.Ownership(1);p=bytearray(b'original');x.arm(0);x.complete(0);x.copy(0,p);p[0]=0
        check(x.queue[0]==b'original')
        x.arm(1);x.complete(1);rejects(lambda:x.copy(1,b'next'),'QUEUE_OVERFLOW')
        check(x.slots[1]=='CPU' and x.queue==[b'original'])
        rejects(lambda:x.arm(0),'OWNERSHIP')
        return dict(overwrite_prevented=True,failure_retained=x.failed)
    test('dma_copy_ownership_and_full',owner)
    def epochs():
        m=em.Results(epoch_limit=2);m.start();k=m.submit(0,1023,512,'configA')
        check(m.finish(k,1535,'configA',status=True)=='COMMITTED')
        check(m.finish(k,1535,'configA',status=True)=='NO_COMMIT')
        m.barrier('STOP');m.start();k2=m.submit(0,1023,512,'configA')
        check(m.finish(k,1024,'configA',status=True)=='NO_COMMIT')
        check(m.finish(k2,1536,'configA',status=True)=='EXPIRED')
        m.barrier('STOP');rejects(m.start,'OVERFLOW')
        return dict(equal_ttl_valid=True,old_epoch_rejected=True,finite_key_no_wrap=True)
    test('epoch_ttl_and_duplicate_commit',epochs)
    def priority():
        m=em.Results();m.start();k=m.submit(0,1023,512,'A')
        check(m.finish(k,1024,'A',status=True,stop=True)=='REVOKED')
        m.start();k=m.submit(0,1023,512,'A');check(m.finish(k,None,'A',status=True)=='WAIT')
        check(m.finish(k,1024,'A',status=True)=='COMMITTED')
        check(m.finish(k,1024,'A',status=True,error=True)=='REVOKED' and m.failed)
        rejects(m.start)
        return dict(stop_wins=True,late_status_fail_stop=True,audit=m.audit)
    test('control_priority_and_late_fault',priority)
    def clock():
        check(em.sample_upper_bound(100,1000000,2)==48102)
        check(em.sample_upper_bound(100,1,0)==101)
        rejects(lambda:em.sample_upper_bound(em.MAX_ID,1,0))
        return dict(rate_hz=48000,note='bound requires measured timer+sampling anchor uncertainty; stale last-received ID is not current time')
    test('sample_clock_ttl_bound',clock)
    def identities():
        m=em.Results();m.start();k=m.submit(0,1023,512,'A')
        check(m.finish(k,100,'A',status=True)=='INVALID_TIME')
        check(m.finish(k,1024,'B',status=True)=='REVOKED')
        rejects(lambda:m.submit(1,em.MAX_ID,1,'A'),'TTL_OVERFLOW')
        rejects(lambda:m.submit(1<<32,0,1,'A'),'IDENTITY')
        m.barrier('DISCONTINUITY');m.barrier('DISCONTINUITY');check(m.interval==0)
        rejects(lambda:m.submit(1,2047,512,'A'),'IDENTITY')
        m.begin_clean_interval();check(m.interval==1)
        m.interval=(1<<32)-1;m.barrier('DISCONTINUITY');rejects(m.begin_clean_interval,'INTERVAL_OVERFLOW');check(m.failed)
        return dict(config_mismatch=True,ttl_overflow=True,frame_overflow=True,interval_overflow=True,consecutive_errors_no_empty_interval=True)
    test('identity_and_counter_rejections',identities)
    def queues():
        check(em.queue_trace(range(0,1000,10),10,1)==1)
        rejects(lambda:em.queue_trace(range(0,1000,10),11,2),'QUEUE_FULL')
        rejects(lambda:em.queue_trace([0],None,8),'UNBOUNDED')
        rejects(lambda:em.serial_schedule([em.Stage('B','RAM',1,('A',))]),'DEPENDENCY')
        rows=em.serial_schedule([em.Stage('a','RAM',10,()),em.Stage('b','RAM',20,())])
        check(rows[1]['begin']==10)
        return dict(boundary_pass=True,overbudget_full_and_unbounded_rejected=True,shared_ram_serialized=True)
    test('queue_and_dependency_counterexamples',queues)
    def budgets():
        serial=em.budget();fast=em.budget(1,4,9,50000);unknown=em.budget(external_wait=None)
        check(not serial['conditional_deadline_met'])
        check(fast['conditional_deadline_met'])
        check(all(x['total']=='REALTIME_BLOCKED' for x in (serial,fast,unknown)))
        memory=em.memory_plan();check(memory['fits'])
        check(em.validate_layout(memory['regions'],1<<20))
        rejects(lambda:em.validate_layout(memory['regions'],memory['logical_bytes']-1),'MEMORY_LAYOUT')
        rejects(lambda:em.validate_layout([dict(offset=0,end=128),dict(offset=64,end=192)],1000),'MEMORY_LAYOUT')
        rejects(lambda:em.validate_layout([dict(offset=1,end=65)],1000),'MEMORY_LAYOUT')
        check(all(a['end']<=b['offset'] for a,b in zip(memory['regions'],memory['regions'][1:])))
        for name,x in [('budget-serial.json',serial),('budget-parallel-assumptions.json',fast),('budget-unbounded.json',unknown),('memory.json',memory)]:save(name,x)
        return dict(serial=serial['conditional_cycles'],parallel_conditional=fast['conditional_cycles'],hop=serial['hop_cycles'],logical_bytes=memory['logical_bytes'],production='REALTIME_BLOCKED')
    test('conditional_budget_and_memory',budgets,'arithmetic_conditional_model')
    save('results.json',dict(tests=rows,passed=sum(r['result']=='PASS' for r in rows),failed=sum(r['result']=='FAIL' for r in rows),
         exit_code=int(any(r['result']=='FAIL' for r in rows)),AMD_IP='NOT_RUN',implementation='NOT_RUN',board='NOT_RUN',approval='NOT_REQUESTED_NOT_GRANTED'))
    print('SUMMARY',len(rows),'tests,',sum(r['result']=='FAIL' for r in rows),'failures')
    return int(any(r['result']=='FAIL' for r in rows))


if __name__=='__main__':
    raise SystemExit(main())
