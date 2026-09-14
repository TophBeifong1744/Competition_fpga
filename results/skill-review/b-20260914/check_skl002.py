import copy, hashlib, json, pathlib, struct, subprocess, sys
ROOT=pathlib.Path(__file__).parent
SKILL=pathlib.Path(sys.argv[1]).resolve()
OUT=ROOT/'skl002-independent';OUT.mkdir(exist_ok=False)
sys.path.insert(0,str(SKILL/'scripts'))
from dma_session import DmaSession,TransferSpec
from simulate_dma import MockDma,MockClock
from compare_golden import compare_numbers,compare_bytes
from validate_profile import validate
def save(name,obj):
    (OUT/(name+'.json')).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(name,ok,details=None):checks.append(dict(name=name,passed=bool(ok),details=details))
profiles=[]
for ident,part,ip,width,fmt,values in [
 ('thermal','xc7z010clg400-1','temperature_dma',16,'<h',[-32768,-123,0,1,32767,25]*8),
 ('pixel','xczu2cg-sbva484-1-e','pixel_dma',64,'<I',[0,0x12345678,0xffffffff,0xabcdef01]*8)]:
    d=OUT/ident;d.mkdir();data=b''.join(struct.pack(fmt,x) for x in values)
    (d/'golden.bin').write_bytes(data)
    (d/'design.bit').write_bytes(('SYNTHETIC STATIC FIXTURE '+ident).encode())
    ctrl=ident+'_control'
    (d/'design.hwh').write_text('<HW PART="'+part+'"><MODULE INSTANCE="'+ctrl+'"/><MODULE INSTANCE="'+ip+'"/></HW>')
    manifest=dict(build_id='b-'+ident,interface_version=3,vivado_version='2025.2',device_part=part,bit_sha256=h(d/'design.bit'),hwh_sha256=h(d/'design.hwh'))
    (d/'manifest.json').write_text(json.dumps(manifest))
    p=dict(schema_version=1,profile_id='b-'+ident,
      board=dict(board_name='synthetic-'+ident,board_revision='offline',device_part=part,pynq_image='synthetic-not-installed',compatibility_contains=['mock,'+ident]),
      overlay=dict(bit='design.bit',hwh='design.hwh',manifest='manifest.json',build_id='b-'+ident,interface_version=3,vivado_version='2025.2',required_ip=[ctrl,ip]),
      register_contract=dict(ip_name=ctrl,address_span_bytes=256,registers=[dict(name='version',offset=32,width_bits=32,access='ro')],identity=[dict(register='version',expected=3,mask=0xffffffff)]),
      dma_contract=dict(ip_name=ip,mode='simple',mm2s_channel='sendchannel',s2mm_channel='recvchannel',stream_data_width_bits=width,buffer_alignment_bytes=64,length_granularity_bytes=8,max_transfer_bytes=4096,cache_policy=dict(tx='flush',rx='invalidate'),tlast_required=True),
      self_tests=[dict(id='fixture-loopback',kind='loopback',length_bytes=len(data),pattern='counter8',timeout_seconds=1,golden='exact')],
      acceptance=dict(minimum_throughput_bytes_per_second=0,maximum_latency_seconds=1))
    pp=d/'profile.json';pp.write_text(json.dumps(p,indent=2));r,c=validate(pp,None,'offline');save(ident+'-static',r);check(ident+'-static',c==0)
    profiles.append((d,p))
    spec=TransferSpec('receive',len(data),64,8,4096,.02,.01,allow_abort=True,max_polls=100)
    save(ident+'-session-input',dict(transfer=spec.__dict__,payload_format=fmt,values=values,golden_sha256=h(d/'golden.bin')))
    for label,faults in [('normal',()),('cache-stale',('rx-invalidate-noop',)),('partial-stop-fail',('rx-arm-after','abort-raises')),('status-unreadable',('status-read',)),('timeout-stop-fail',('timeout','abort-timeout')),('short',('short-output',)),('release-fail',('rx-release',))]:
        dma=MockDma(mode='receive',capture=data,alignment=64,faults=set(faults));s=DmaSession(dma,clock=MockClock());r=s.run(spec,expected=data)
        trace=list(dma.trace);r['adapter_trace']=trace;r['release_attempts']=[b.release_attempts for b in dma.allocations]
        if faults:
            again=s.run(spec,expected=data);r['next_run']=again
            check(ident+'-'+label,r['status']=='FAIL' and dma.trace==trace and again['session_blocked'])
            if label in ('partial-stop-fail','status-unreadable','timeout-stop-fail'):
                check(ident+'-'+label+'-retain',r['buffer_disposition']=='retained' and all(b.release_attempts==0 for b in dma.allocations) and 'rx.read' not in trace)
            if label=='release-fail':check(ident+'-no-double-free',all(b.release_attempts==1 for b in dma.allocations))
        else:check(ident+'-'+label,r['status']=='PASS' and r['actual_bytes']==len(data) and r['mismatch_count']==0 and not any(t.startswith('tx.') for t in trace))
        save(ident+'-'+label,r)
for name,expected,actual,atol,rtol,n in [('big-one',[2**120],[2**120+1],0.,0.,1),('big-tol',[2**120],[2**120+1],1.,0.,0),('overflow',[1e308],[-1e308],0.,1.9,1),('short',[2**100,4],[2**100],0.,0.,1)]:
    r=compare_numbers(expected,actual,atol,rtol);save(name,dict(inputs=[expected,actual,atol,rtol],result=r));check(name,r['mismatch_count']==n)
check('short-bytes',compare_bytes(b'1234',b'123')['mismatch_count']==1)
d,p=profiles[0]
for name,mutation in [('missing-dma-ip',lambda x:x['dma_contract'].update(ip_name='not_in_hwh')),('missing-control-ip',lambda x:x['register_contract'].update(ip_name='not_in_hwh'))]:
    q=copy.deepcopy(p);mutation(q);pp=d/(name+'.json');pp.write_text(json.dumps(q,indent=2));r,c=validate(pp,None,'offline');save(name,r);check(name,c!=0,dict(actual_status=r['status'],expected='FAIL; contracted IP absent from HWH'))
ev=dict(evidence_level='mock',overlay_downloaded=False,artifact_hashes=dict(bit=h(d/'design.bit'),hwh=h(d/'design.hwh')),register_reads=dict(version=3),performance=dict(minimum_throughput_bytes_per_second=1,maximum_latency_seconds=.1))
good=dict(id='fixture-loopback',length_bytes=96,timed_out=False,dma_error=False,mm2s_completed=True,s2mm_completed=True,tlast_observed=True,cache_operations=['tx.flush','rx.invalidate'],mismatch_count=0)
ev['dma_runs']=[dict(good,timed_out=True,mismatch_count=4),good]
ep=d/'duplicate-evidence.json';ep.write_text(json.dumps(ev,indent=2));r,c=validate(d/'profile.json',ep,'offline');save('duplicate-evidence',r);check('duplicate-run-id',c!=0,dict(actual_status=r['status'],expected='FAIL; duplicate ID must not mask earlier failed run'))
cmd=[sys.executable,'-B',str(SKILL/'scripts/pynq_probe.py'),'--profile',str(d/'profile.json'),'--download','--output',str(OUT/'must-not-exist.json')]
pr=subprocess.run(cmd,capture_output=True);(OUT/'board-guard.stdout').write_bytes(pr.stdout);(OUT/'board-guard.stderr').write_bytes(pr.stderr)
check('board-guard',pr.returncode!=0 and b'BOARD_RUNNER_NOT_QUALIFIED' in pr.stderr and not (OUT/'must-not-exist.json').exists(),dict(command=cmd,exit_code=pr.returncode))
save('checks',checks)
print(json.dumps(checks,indent=2))
