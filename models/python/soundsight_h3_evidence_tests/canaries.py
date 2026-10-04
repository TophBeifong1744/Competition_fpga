"""Isolated output mutations and controlled runner failure, in real child processes."""
import argparse, json, pathlib, shutil, sys
from .runner import call, save

def main():
    a=argparse.ArgumentParser();a.add_argument('--cases',type=pathlib.Path,required=True);a.add_argument('--runs',type=pathlib.Path,required=True);a.add_argument('--out',type=pathlib.Path,required=True);args=a.parse_args()
    args.out.mkdir(exist_ok=False);cwd=pathlib.Path(__file__).resolve().parents[1]
    summary=[]
    mutants=[
        ('denominator','DENOMINATOR',lambda r:r['counts'].update(requested_views='3')),
        ('equal_count_selector','IDENTITY',lambda r:r['views'][0]['selection'].update(pair_ordinal='1')),
        ('saved_fact','FACTS',lambda r:r['views'][0]['facts'][4]['value'].update(value='24590')),
        ('erase_error','ERRORS',lambda r:r['original_errors'].pop()),
        ('promote_v','NO_ESCALATION',lambda r:r.update(v_status='PASSED')),
        ('erase_gap','MISSING_EVIDENCE',lambda r:r.update(missing=[])),
        ('lost_source','SOURCE',lambda r:r['source_audit'].update(actual_read_set=[])),
        ('undercharge','RESOURCE_ACCOUNTING',lambda r:r['source_audit'].update(distinct_source_bytes='0')),
        ('synthetic_pass','NO_ESCALATION',lambda r:r.update(claim_scope='PRODUCTION_PASS'))]
    for name,category,mutate in mutants:
        dest=args.out/name;shutil.copytree(args.runs/'saved_file',dest)
        p=dest/'dut/report.json';r=json.loads(p.read_text(encoding='utf-8'));mutate(r);save(p,r)
        argv=[sys.executable,'-B','-m','soundsight_h3_evidence_tests.checker','--case',str(args.cases/'saved_file'),'--run',str(dest)]
        code=call(argv,cwd,dest/'canary-checker');err=(dest/'canary-checker.stderr.txt').read_text(encoding='utf-8')
        ok=code!=0 and ('CHECK_REJECTED '+category+':') in err
        summary.append({'name':name,'expected_category':category,'exit':code,'target_hit':ok})
    dest=args.out/'raw_native';shutil.copytree(args.runs/'saved_file',dest)
    report=json.loads((dest/'dut/report.json').read_text(encoding='utf-8'));p=dest/'dut'/report['raw_payloads'][0]['path']
    r=json.loads(p.read_text(encoding='utf-8'));r['events']=[{'invented_native':'SYNTHETIC'}];save(p,r)
    code=call([sys.executable,'-B','-m','soundsight_h3_evidence_tests.checker','--case',str(args.cases/'saved_file'),'--run',str(dest)],cwd,dest/'canary-checker')
    err=(dest/'canary-checker.stderr.txt').read_text(encoding='utf-8');summary.append({'name':'raw_native','expected_category':'RAW_STATUS','exit':code,'target_hit':code!=0 and 'CHECK_REJECTED RAW_STATUS:' in err})
    code=call([sys.executable,'-B','-m','soundsight_h3_evidence_tests.runner','--cases',str(args.cases),'--out',str(args.out/'controlled-runner-output'),'--fail-step'],cwd,args.out/'controlled-runner')
    s=json.loads((args.out/'controlled-runner-output/summary.json').read_text(encoding='utf-8'))
    summary.append({'name':'controlled_runner_failure','expected_category':'RUNNER_FAILURE','exit':code,'child_exit':s['controlled_child_exit'],'target_hit':code!=0 and s['controlled_child_exit']==17})
    ok=all(x['target_hit'] for x in summary);save(args.out/'summary.json',{'rows':summary,'all_target_hits':ok,'claim':'CHECKER_SENSITIVITY_ONLY_NOT_ORACLE_ACCEPTANCE'})
    print(json.dumps({'canaries':len(summary),'all_target_hits':ok}));return 0 if ok else 1
if __name__=='__main__':sys.exit(main())
