"""Record actual subprocess outcomes and propagate checker/substep failures."""
import argparse, datetime, json, pathlib, subprocess, sys
from .checker import binding
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def call(argv,cwd,prefix):
    start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:p=subprocess.run(argv,cwd=cwd,capture_output=True,timeout=60)
    except subprocess.TimeoutExpired as e:
        prefix.with_suffix('.stdout.txt').write_bytes(e.stdout or b'');prefix.with_suffix('.stderr.txt').write_bytes(e.stderr or b'')
        save(prefix.with_suffix('.command.json'),{'argv':argv,'cwd':str(cwd),'exit':124,'timeout':True,'start':start});return 124
    prefix.with_suffix('.stdout.txt').write_bytes(p.stdout);prefix.with_suffix('.stderr.txt').write_bytes(p.stderr)
    save(prefix.with_suffix('.command.json'),{'argv':argv,'cwd':str(cwd),'exit':p.returncode,'start':start,'finish':datetime.datetime.now(datetime.timezone.utc).isoformat()});return p.returncode
def main():
    a=argparse.ArgumentParser();a.add_argument('--cases',type=pathlib.Path,required=True);a.add_argument('--out',type=pathlib.Path,required=True);a.add_argument('--case',action='append');a.add_argument('--fail-step',action='store_true');args=a.parse_args()
    args.out.mkdir(exist_ok=False);cwd=pathlib.Path(__file__).resolve().parents[1];summary=[]
    if args.fail_step:
        code=call([sys.executable,'-B','-c','import sys;sys.exit(17)'],cwd,args.out/'controlled-child')
        save(args.out/'summary.json',{'controlled_child_exit':code,'runner_exit':1 if code else 0,'type':'RUNNER_FAILURE_CANARY'});return 1 if code else 0
    manifest=json.loads((args.cases/'fixture-manifest.json').read_text(encoding='utf-8'))
    for rel,h in manifest['files'].items():
        if binding(args.cases/rel)!=h:raise RuntimeError('FROZEN_FIXTURE_DRIFT:'+rel)
    names=args.case or manifest['cases'];overall=0
    for name in names:
        case=args.cases/name;r=args.out/name;r.mkdir();e=json.loads((case/'expected.json').read_text(encoding='utf-8'));out=r/'dut'
        sentinel=None
        if e.get('existing'):
            out.mkdir();(out/'sentinel.bin').write_bytes(b'OWNED_BY_PREVIOUS_RUN\x00');sentinel=binding(out/'sentinel.bin')
        module='soundsight_h3_evidence_tests.injected' if e.get('internal_injection') else 'soundsight_h3_evidence'
        argv=[sys.executable,'-B','-m',module,'producer','--access-map',str(case/'access-map.json'),'--selection',str(case/'selection.json'),'--registry',str(case/'registry.json'),'--out',str(out)]
        code=call(argv,cwd,r/'dut-run')
        (r/'stdout.txt').write_bytes((r/'dut-run.stdout.txt').read_bytes());(r/'stderr.txt').write_bytes((r/'dut-run.stderr.txt').read_bytes())
        save(r/'invocation.json',{'exit':code,'entry':module,'kind':'INTERNAL_INJECTION' if e.get('internal_injection') else 'REAL_MODULE_CLI','sentinel_before':sentinel})
        check=call([sys.executable,'-B','-m','soundsight_h3_evidence_tests.checker','--case',str(case),'--run',str(r)],cwd,r/'checker')
        row={'case':name,'dut_exit':code,'expected_exit':e['exit'],'checker_exit':check,'kind':'INTERNAL_INJECTION' if e.get('internal_injection') else 'REAL_MODULE_CLI'};summary.append(row)
        if check:
            overall=1
            if not (args.out/'FIRST-FAILURE.json').exists():save(args.out/'FIRST-FAILURE.json',row)
        print(json.dumps(row))
    save(args.out/'summary.json',{'rows':summary,'runner_exit':overall,'failures':sum(x['checker_exit']!=0 for x in summary),'claim':'INDEPENDENT_BOUNDED_CHECKS_NOT_ASSET_SELF_ACCEPTANCE'})
    return overall
if __name__=='__main__':sys.exit(main())
