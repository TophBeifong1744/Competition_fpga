"""Pinned incremental SOFTWARE checks. Does not run synthesis/XSim or change projects."""
import argparse,hashlib,importlib.util,json,subprocess,sys,traceback
from pathlib import Path
from fractions import Fraction
import numpy as np
from logic_adapter import Adapter,rne_shift4,phat_mask,commit_decision,MAX_ID

HERE=Path(__file__).resolve().parents[1]
REPO=next(p for p in HERE.parents if (p/'docs/team-workflow.md').is_file())
B='f5a4cea7a7cf7dcccf09720cfff92131e6157752'
A='e4f9eae3fe7e4104ff8a6827937e326954f90a82'
BP='task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/'
AP='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/frame-adapter-bram-candidate-01/'
parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=HERE/'evidence/run01')
out=parser.parse_args().out;out.mkdir(parents=True,exist_ok=False)
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def digest(data):return hashlib.sha256(data).hexdigest()
bindings=[]
def pin(commit,path,name):
    data=subprocess.run(['git','show',commit+':'+path],cwd=REPO,check=True,capture_output=True).stdout
    p=out/name;p.write_bytes(data);bindings.append(dict(commit=commit,path=path,snapshot=name,sha256=digest(data)));return p

checks=[];counterexamples=[]
def check(name,fn):
    try:
        details=fn();checks.append(dict(name=name,status='PASS',details=details))
        print('PASS',name,flush=True)
    except Exception as exc:
        checks.append(dict(name=name,status='FAIL',error=str(exc),traceback=traceback.format_exc()))
        print('FAIL',name,str(exc),flush=True)

try:
    module_path=pin(A,AP+'model/framing_model.py','frozen_framing_model.py')
    pin(A,AP+'rtl/pcm4_overlap_framer_bram.v','frozen_rtl.v')
    golden_path=pin(B,BP+'golden/framing.json','b-framing.json')
    arrays_path=pin(B,BP+'golden/synthetic-frames.npz','b-synthetic-frames.npz')
    pin(B,BP+'source/framing_review.py','b-framing-source.py')
    pin(B,BP+'B-RESPONSE-20260923.md','b-response.md')
    spec=importlib.util.spec_from_file_location('frozen_a',module_path)
    core=importlib.util.module_from_spec(spec);sys.modules[spec.name]=core;spec.loader.exec_module(core)
    G=core.Group
    def g(i,**kw):return G(i,(1,-2,3,-4),**kw)
    golden=json.loads(golden_path.read_text(encoding='utf-8'))
    arrays=np.load(arrays_path,allow_pickle=False)

    def compare_case(case):
        name=case['session_id'];n=case['groups'];groups=[]
        for j in range(n):
            ident=(1<<53)+17+j+(7 if name=='gap4000' and j>=1500 else 0)
            groups.append(G(ident,(j-20000,3*j+40000,-5*j+100000,7*j-150000),4 if name=='clip3500' and j==1250 else 0))
        import struct
        raw=b''.join(struct.pack('<IIiiiiII',x.sample_id&0xffffffff,x.sample_id>>32,*x.pcm,x.flags,0) for x in groups)
        assert digest(raw)==case['raw_sha256'],'Input differs from frozen B'
        adapter=Adapter(core,name)
        # Model accept order crosses exactly the existing 250-group packet boundary.
        for offset in range(0,n,250):
            for x in groups[offset:offset+250]:adapter.push(x)
        adapter.stop();assert len(adapter.frames)==len(case['frames'])
        for actual,expected in zip(adapter.frames,case['frames']):
            for field in ('interval_id','frame_id','reset_before','row_start','row_stop'):
                assert actual[field]==expected[field],(name,field,actual[field],expected[field])
            assert actual['first_id']==expected['first_sample_id'] and actual['last_id']==expected['last_sample_id']
            pcm=np.array(actual['pcm'],dtype='<i4').T.copy()
            assert np.array_equal(pcm,arrays[name+'_frame_'+str(actual['frame_id'])])
            assert digest(pcm.tobytes())==expected['pcm_channel_major_i32_sha256']
        return dict(groups=n,frames=len(adapter.frames),all_pcm_and_descriptors_exact=True)
    for case in golden['cases']:
        if case['session_id']!='s1':check('B-golden/'+case['session_id'],lambda c=case:compare_case(c))

    def divergences():
        f=core.Framer();f.start(1)
        for j in range(1024):f.push(g(j,flags=1 if j==511 else 0))
        assert len(f.frames)==1
        a=Adapter(core)
        for j in range(1024):a.push(g(j,flags=1 if j==511 else 0))
        assert len(a.frames)==0
        counterexamples.append(dict(case='clip-in-window',unadapted_frames=1,adapted_frames=0,expected_mismatch=True))
        f=core.Framer();f.start(1)
        for x in [g(100),g(103),g(105),g(106)]:f.push(x)
        a=Adapter(core)
        for x in [g(100),g(103),g(105),g(106)]:a.push(x)
        assert [e.sample_id for e in f.events]==[103]
        assert [e['id'] for e in a.events]==['103','105']
        counterexamples.append(dict(case='repeated-gap',unadapted_error_ids=['103'],adapted_error_ids=['103','105'],expected_mismatch=True))
        return counterexamples
    check('preserve-original-counterexamples',divergences)

    def recover(seq,error_ids,segments):
        a=Adapter(core)
        for x in seq:a.push(x)
        a.stop();assert [e['id'] for e in a.events]==list(map(str,error_ids))
        assert a.interval+1==segments
        return dict(events=a.events,nonempty_intervals=a.interval+1)
    check('clip-recovery',lambda:recover([g(100),g(101,flags=1),g(102)],[101],2))
    check('drop-recovery',lambda:recover([g(100),g(103),g(104)],[103],2))
    check('drop-clip-drop',lambda:recover([g(100),g(103,flags=1),g(105),g(106)],[103,105],2))
    check('consecutive-errors-no-empty-interval',lambda:recover([g(100),g(101,flags=1),g(102,flags=2),g(103)],[101,102],2))
    check('last-drop-no-invented-interval',lambda:recover([g(100),g(103)],[103],1))
    check('all-errors-no-interval',lambda:recover([g(1,flags=1),g(2,flags=2)],[1,2],0))
    def fatal(seq,expected,queue=False):
        a=Adapter(core)
        for i,x in enumerate(seq):a.push(x,queue_overflow=queue and i==len(seq)-1)
        assert a.fault and expected<=set(a.events[-1]['reasons'])
        try:a.push(g(1000))
        except ValueError:pass
        else:raise AssertionError('Fatal session accepted another row')
        return a.events[-1]
    for name,seq,reasons in [
        ('duplicate',[g(100),g(100)],{'ID_DUPLICATE'}),
        ('clip-reverse',[g(100,flags=1),g(99)],{'ID_REVERSE'}),
        ('wrap',[g(MAX_ID),g(0)],{'ID_WRAP'}),
        ('flags',[g(1,flags=16)],{'INVALID_FLAGS'}),
        ('reserved',[g(1,reserved=1)],{'INVALID_RESERVED'}),
        ('range',[G(1,(1<<23,0,0,0))],{'PCM_RANGE'}),
        ('upstream',[g(1,integrity_error=True)],{'UPSTREAM_ERROR'}),
        ('reason-union',[g(1),g(1,flags=17,reserved=1,integrity_error=True)],{'UPSTREAM_ERROR','ID_DUPLICATE','INVALID_FLAGS','INVALID_RESERVED','CLIP'})]:
        check('fatal/'+name,lambda s=seq,r=reasons:fatal(s,r))
    check('fatal/queue',lambda:fatal([g(1)],{'QUEUE_OVERFLOW'},True))
    def boundaries():
        result=[]
        for n in (0,1023,1024,1535,1536,2048):
            a=Adapter(core,str(n))
            for j in range(n):a.push(g(j))
            a.stop();expected=max(0,1+(n-1024)//512);assert len(a.frames)==expected
            result.append([n,expected])
        # Adjacent IDs across two explicit sessions must not concatenate.
        for start in (0,600):
            a=Adapter(core,str(start))
            for j in range(start,start+600):a.push(g(j))
            a.stop();assert not a.frames
        return result
    check('frame-boundaries-and-session-isolation',boundaries)

    def numeric():
        values=list(range(-131072,131073))+list(range((1<<28)-128,1<<28))+list(range(-(1<<28),-(1<<28)+128))
        saturated=0
        for x in values:
            want=round(Fraction(x,16));expected=max(-(1<<24),min((1<<24)-1,want))
            got,clip=rne_shift4(x);assert got==expected and clip==(want!=expected)
            if not clip:assert abs(Fraction(got)-Fraction(x,16))<=Fraction(1,2)
            saturated+=clip
        assert all(rne_shift4(x)==(0,False) for x in range(-8,9))
        for x in (-(1<<28)-1,1<<28):
            try:rne_shift4(x)
            except ValueError:pass
            else:raise AssertionError('Out of range accepted')
        return dict(integer_cases=len(values),saturations=saturated,oracle='Fraction exact rational nearest-even',profile='fixed4 software only')
    check('fixed4-exact-rational-boundaries',numeric)
    def masks():
        assert not phat_mask(0,0)
        assert phat_mask(1,2500) and not phat_mask(1,2501) and phat_mask(1,2499)
        assert Fraction(2**26,10**15)<1
        maximum=(1<<102)-1
        threshold=(maximum+2499)//2500
        assert phat_mask(threshold,maximum) and not phat_mask(threshold-1,maximum)
        # Same four-channel shift does not protect the weakest retained bin from zeroing.
        assert rne_shift4(8)[0]==0 and rne_shift4(9)[0]==1
        assert sum(phat_mask(1,1) for _ in range(11))<12
        assert sum(phat_mask(1,1) for _ in range(12))>=12
        return dict(mask='square>0 and 2500*square>=max',epsilon_unit='cross-spectrum magnitude codes',hardware_overflow='NOT_TESTED Python unbounded integers')
    check('zero-weak-mask-epsilon-units',masks)
    def lifecycle():
        base=dict(last_id=100,ttl=20,available=120)
        assert commit_decision(**base)=='COMMIT_RESEARCH_ONLY'
        for key,want in [('control','INVALID_AND_CLEAR_HOLD'),('fatal','INVALID_AND_CLEAR_HOLD'),('frame_error','INVALID')]:
            assert commit_decision(**base,**{key:True})==want
        assert commit_decision(last_id=100,ttl=20,available=121)=='RESULT_EXPIRED'
        assert commit_decision(**base,already_committed=True)=='NO_SECOND_COMMIT'
        assert commit_decision(**base,status_complete=False)=='WAIT_STATUS'
        assert commit_decision(**base,session_match=False)=='INVALID_IDENTITY'
        assert commit_decision(**base,interval_match=False)=='INVALID_IDENTITY'
        assert commit_decision(last_id=MAX_ID,ttl=1,available=MAX_ID)=='INVALID_TTL_OVERFLOW'
        assert commit_decision(last_id=100,ttl=20,available=None)=='REALTIME_ELIGIBILITY_UNKNOWN'
        assert commit_decision(**base,already_committed=True,frame_error=True)=='RETROSPECTIVE_FAULT_FAIL_STOP'
        return dict(assertions=11,scope='Decision predicates only; no hardware state-machine proof')
    check('commit-priority-TTL',lifecycle)
except Exception as exc:
    checks.append(dict(name='harness',status='FAIL',error=str(exc),traceback=traceback.format_exc()))
finally:
    save(out/'bindings.json',bindings)
    save(out/'source-sha256.json',{p.name:digest(p.read_bytes()) for p in sorted(Path(__file__).parent.glob('*.py'))})
    save(out/'expected-counterexamples.json',counterexamples)
    save(out/'checks.json',dict(passed=sum(c['status']=='PASS' for c in checks),failed=sum(c['status']=='FAIL' for c in checks),checks=checks,
        level='SOFTWARE_FUNCTIONAL_ONLY',rtl_xsim='NOT_RUN',amd_new_simulation='NOT_RUN',board='NOT_RUN',argv=sys.argv))
    save(out/'SHA256.json',{p.name:digest(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file()})
    print('SUMMARY',sum(c['status']=='PASS' for c in checks),'PASS',sum(c['status']=='FAIL' for c in checks),'FAIL')
sys.exit(any(c['status']=='FAIL' for c in checks))
