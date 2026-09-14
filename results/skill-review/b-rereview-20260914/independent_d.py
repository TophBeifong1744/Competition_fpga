import copy, hashlib, json, pathlib, shutil, struct, subprocess, sys, time
ROOT=pathlib.Path(__file__).parent
OLD=pathlib.Path('F:/NUEC/review-worktrees/b-skills-main-20260914/results/skill-review/b-20260914')
SKILL=pathlib.Path(sys.argv[1]).resolve()
assert subprocess.check_output(['git','-C',str(SKILL),'rev-parse','HEAD'],text=True).strip()=='3ac597d1d16982e0a5c5a114202ca8568dc28d8f'
OUT=ROOT/'d-independent'; OUT.mkdir(exist_ok=False)
sys.path.insert(0,str(SKILL/'scripts'))
from dma_session import DmaSession, TransferSpec
from simulate_dma import MockDma, MockClock
from compare_golden import compare_numbers, compare_bytes
checks=[]
def save(p,o): p.write_text(json.dumps(o,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def check(name,ok,details=None):
    checks.append(dict(name=name,passed=bool(ok),details=details))
def cli(label,profile,evidence=None,code=None):
    d=OUT/label;d.mkdir()
    cmd=[sys.executable,'-B',str(SKILL/'scripts/validate_profile.py'),'--profile',str(profile),'--mode','offline','--output',str(d/'result.json')]
    if evidence: cmd+=['--evidence',str(evidence)]
    t=time.time();r=subprocess.run(cmd,cwd=SKILL,capture_output=True)
    (d/'stdout.log').write_bytes(r.stdout);(d/'stderr.log').write_bytes(r.stderr)
    save(d/'command.json',dict(command=cmd,cwd=str(SKILL),exit_code=r.returncode,started_unix=t))
    result=json.loads((d/'result.json').read_text());encoded=json.dumps(result)
    check(label, (r.returncode!=0 and result['status']=='FAIL' and code in encoded) if code else (r.returncode==0 and result['status']=='PASS'),dict(exit_code=r.returncode,status=result['status'],required_code=code))
    return result

for ident in ('thermal','pixel'):
    shutil.copytree(OLD/'skl002-independent'/ident,OUT/ident)
    d=OUT/ident
    for p in d.iterdir(): check('original-bytes-'+ident+'-'+p.name,h(p)==h(OLD/'skl002-independent'/ident/p.name))
    cli(ident+'-valid',d/'profile.json')
    original=OLD/'skl002-independent'/(ident+'-session-input.json')
    shutil.copyfile(original,OUT/original.name)
    inp=json.loads(original.read_text());data=b''.join(struct.pack(inp['payload_format'],v) for v in inp['values'])
    check(ident+'-independent-packing',data==(d/'golden.bin').read_bytes() and hashlib.sha256(data).hexdigest()==inp['golden_sha256'])
    spec=TransferSpec(**inp['transfer'])
    for label,faults in [('normal',()),('cache-stale',('rx-invalidate-noop',)),('partial-stop-fail',('rx-arm-after','abort-raises')),('status-unreadable',('status-read',)),('timeout-stop-fail',('timeout','abort-timeout')),('short',('short-output',)),('release-fail',('rx-release',))]:
        dma=MockDma(mode='receive',capture=data,alignment=64,faults=set(faults));session=DmaSession(dma,clock=MockClock());r=session.run(spec,expected=data)
        trace=list(dma.trace);r['adapter_trace']=trace;r['release_attempts']=[b.release_attempts for b in dma.allocations]
        if faults:
            again=session.run(spec,expected=data);r['next_run']=again
            check(ident+'-'+label,r['status']=='FAIL' and dma.trace==trace and again['session_blocked'])
            if label in ('partial-stop-fail','status-unreadable','timeout-stop-fail'):
                check(ident+'-'+label+'-retain',r['buffer_disposition']=='retained' and all(b.release_attempts==0 for b in dma.allocations) and 'rx.read' not in trace)
            if label=='release-fail':check(ident+'-no-double-free',all(b.release_attempts==1 for b in dma.allocations))
        else: check(ident+'-'+label,r['status']=='PASS' and r['actual_bytes']==len(data) and r['mismatch_count']==0 and not any(t.startswith('tx.') for t in trace))
        save(OUT/(ident+'-'+label+'.json'),r)

d=OUT/'thermal'
for name in ('missing-dma-ip','missing-control-ip'):cli(name,d/(name+'.json'),code='HWH_CONTRACT_IP')
cli('original-duplicate',d/'profile.json',d/'duplicate-evidence.json','DMA_RUN_DUPLICATE')
original=json.loads((d/'duplicate-evidence.json').read_text())
bad,good=original['dma_runs']
for label,runs in [('bad-good',[bad,good]),('good-bad',[good,bad]),('good-good',[good,good]),('bad-bad',[bad,bad]),('good-bad-good',[good,bad,good]),('unique-good',[good])]:
    ev=copy.deepcopy(original);ev['dma_runs']=runs;ep=d/(label+'.json');save(ep,ev)
    cli(label,d/'profile.json',ep,None if label=='unique-good' else 'DMA_RUN_DUPLICATE')

profile=json.loads((d/'profile.json').read_text())
for label,xml,ctrl,dma,ok in [
 ('port-alias','<MODULE INSTANCE="real"/><PORT NAME="temperature_dma"/><MODULE INSTANCE="thermal_control"/>','thermal_control','temperature_dma',False),
 ('parameter-alias','<MODULE INSTANCE="real"><PARAMETER NAME="temperature_dma"/></MODULE><MODULE INSTANCE="thermal_control"/>','thermal_control','temperature_dma',False),
 ('module-type','<MODULE INSTANCE="real" MODULENAME="temperature_dma"/><MODULE INSTANCE="thermal_control"/>','thermal_control','temperature_dma',False),
 ('hierarchy-tail','<MODULE INSTANCE="temperature_dma" FULLNAME="/sub/temperature_dma"/><MODULE INSTANCE="thermal_control" FULLNAME="/sub/thermal_control"/>','thermal_control','temperature_dma',False),
 ('hierarchy-full','<MODULE INSTANCE="temperature_dma" FULLNAME="/sub/temperature_dma"/><MODULE INSTANCE="thermal_control" FULLNAME="/sub/thermal_control"/>','sub/thermal_control','sub/temperature_dma',True),
 ('hierarchy-leading-slash','<MODULE INSTANCE="temperature_dma" FULLNAME="/sub/temperature_dma"/><MODULE INSTANCE="thermal_control" FULLNAME="/sub/thermal_control"/>','/sub/thermal_control','/sub/temperature_dma',True),
]:
    case=OUT/('input-'+label);case.mkdir();shutil.copyfile(d/'design.bit',case/'design.bit')
    (case/'design.hwh').write_text('<HW PART="xc7z010clg400-1">'+xml+'</HW>',encoding='utf-8')
    m=json.loads((d/'manifest.json').read_text());m['hwh_sha256']=h(case/'design.hwh');save(case/'manifest.json',m)
    p=copy.deepcopy(profile);p['register_contract']['ip_name']=ctrl;p['dma_contract']['ip_name']=dma
    p['overlay']['required_ip']=['sub/thermal_control','sub/temperature_dma'] if ok else ['thermal_control'] if label!='hierarchy-tail' else ['sub/thermal_control']
    save(case/'profile.json',p);cli(label,case/'profile.json',code=None if ok else 'HWH_CONTRACT_IP')
for name,expected,actual,atol,rtol,n in [('big-one',[2**120],[2**120+1],0.,0.,1),('big-tol',[2**120],[2**120+1],1.,0.,0),('overflow',[1e308],[-1e308],0.,1.9,1),('short',[2**100,4],[2**100],0.,0.,1)]:
    r=compare_numbers(expected,actual,atol,rtol);save(OUT/(name+'.json'),dict(inputs=[expected,actual,atol,rtol],result=r));check(name,r['mismatch_count']==n)
check('short-bytes',compare_bytes(b'1234',b'123')['mismatch_count']==1)
cmd=[sys.executable,'-B',str(SKILL/'scripts/pynq_probe.py'),'--profile',str(d/'profile.json'),'--download','--output',str(OUT/'must-not-exist.json')]
r=subprocess.run(cmd,cwd=SKILL,capture_output=True);(OUT/'board-guard.stdout').write_bytes(r.stdout);(OUT/'board-guard.stderr').write_bytes(r.stderr)
check('board-guard',r.returncode!=0 and b'BOARD_RUNNER_NOT_QUALIFIED' in r.stderr and not (OUT/'must-not-exist.json').exists(),dict(command=cmd,exit_code=r.returncode))
save(OUT/'checks.json',checks)
print(json.dumps(dict(checks=len(checks),failed=[c for c in checks if not c['passed']]),indent=2))
sys.exit(any(not c['passed'] for c in checks))
