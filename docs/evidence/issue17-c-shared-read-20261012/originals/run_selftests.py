"""中文用途：在独立目录执行冻结候选的XSim回归，严格验证首个负例失败。
Command: python codex_out/i17-evidence-shared-read-20261012/run_selftests.py
Outputs: sim_*/run.json, native logs, selftest-summary.json.
Next: qualified non-author reviews exact product/test hashes and raw logs.
"""
import hashlib,json,pathlib,re,subprocess,sys,time
from runner_environment import TOOLS,env
ROOT=pathlib.Path(__file__).resolve().parent
freeze=json.loads((ROOT/'product-freeze.json').read_text(encoding='utf8'))
product=pathlib.Path(freeze['product_path'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(product)==freeze['product_sha256']
cases=[('evidence','tb_evidence',None),('legacy_canary','tb_evidence','CANARY_DATA'),
       ('shared','tb_shared_read',None),('shared_canary','tb_shared_read','CANARY_SHARED'),
       ('miter_canary','tb_shared_read','CANARY_MITER')]
if len(sys.argv)>1:cases=[c for c in cases if c[0] in sys.argv[1:]]
assert cases
summary=[]
for name,top,plus in cases:
    folder=ROOT/f'sim_{name}';folder.mkdir(exist_ok=False)
    baseline='i17_vio_evidence_before.sv' if top=='tb_evidence' else 'i17_vio_evidence_baseline.sv'
    sources=[product,ROOT/'selftest'/baseline,ROOT/'selftest'/f'{top}.sv']
    meta={'candidate_sha256':sha(product),'case':name,'tool':'Vivado XSim 2025.2',
          'seed':17010,'cwd':str(folder),'sources':{str(p):sha(p) for p in sources},
          'runner_sha256':sha(pathlib.Path(__file__)),'environment_recipe_sha256':sha(ROOT/'runner_environment.py'),
          'commands':[],'status':'RUNNING'}
    log=''
    for tool,args in [('xvlog',['--sv',*sources]),('xelab',[f'work.{top}','--snapshot','test','--debug','off']),
        ('xsim',['test','--runall','--onerror','quit','--onfinish','quit','--sv_seed','17010']+(['--testplusarg',plus] if plus else []))]:
        cmd=[str(TOOLS/'bin/unwrapped/win64.o'/f'{tool}.exe'),*map(str,args)]
        start=time.monotonic()
        try:
            cp=subprocess.run(cmd,cwd=folder,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=300)
            log=cp.stdout.decode('utf8',errors='replace');exit_code=cp.returncode
        except subprocess.TimeoutExpired as ex:
            log=(ex.stdout or b'').decode('utf8',errors='replace');exit_code=None
            meta['status']='TIMEOUT_HANG'
        (folder/f'{tool}-stdout.log').write_text(log,encoding='utf8')
        meta['commands'].append({'argv':cmd,'exit':exit_code,'elapsed_s':round(time.monotonic()-start,3),
                                 'log':str(folder/f'{tool}-stdout.log')})
        (folder/'run.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
        if exit_code!=0:
            if meta['status']=='RUNNING':meta['status']='COMPILE_ELAB_FAIL' if tool!='xsim' else 'TOOL_ENV_FAIL'
            break
    else:
        fatals=re.findall(r'^Fatal:.*$',log,re.M)
        completed=any(x in log for x in ['PUBLIC_READ_COMPLETE','EVIDENCE_COMPLETE','SHARED_COMPLETE'])
        if plus:
            wanted={
              'CANARY_DATA':'Fatal: DATA_CHECK cycle=79 DUMP content kind=3 word=17 exp=90060060 got=90060160',
              'CANARY_SHARED':'DUMP_BUSY_CONTENT word=0 exp=d0e0f001 got=d0e0f101',
              'CANARY_MITER':'all19 mismatch'}[plus]
            ok=len(fatals)==1 and wanted in fatals[0] and not completed
            if plus=='CANARY_SHARED':ok=ok and fatals[0].startswith('Fatal: SHARED_CHECK')
            if plus=='CANARY_MITER':ok=ok and fatals[0].startswith('Fatal: SHARED_MITER')
            meta.update(expected_first_failure=wanted,observed_first_failure=fatals[0] if fatals else None,
                        completion_marker_absent=not completed)
            meta['status']='EXPECTED_CANARY_REJECTION' if ok else 'CANARY_FAILED_TO_DETECT_EXACT_FAILURE'
        else:
            marker='PUBLIC_READ_COMPLETE reads=6656' if top=='tb_evidence' else 'SHARED_COMPLETE'
            ok=marker in log and 'pending=0' in log and not fatals and 'TIMEOUT_HANG' not in log
            meta['status']='AUTHOR_CHECKS_COMPLETE_PENDING_REVIEW' if ok else 'CHECK_FAILED'
            meta['completion_lines']=[l for l in log.splitlines() if '_COMPLETE' in l]
        meta['fatals']=fatals
    meta['log_hashes']={p.name:sha(p) for p in folder.glob('*.log')}
    (folder/'run.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
    summary.append(meta)
    (ROOT/'selftest-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
    print(name,meta['status'],log[-650:],flush=True)
    if meta['status'] not in ('EXPECTED_CANARY_REJECTION','AUTHOR_CHECKS_COMPLETE_PENDING_REVIEW'):sys.exit(1)
