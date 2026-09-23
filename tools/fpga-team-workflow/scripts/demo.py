"""Small, fully local demonstration. Synthetic member facts never become approval."""
import argparse
from pathlib import Path
import sys
sys.dont_write_bytecode=True
from ftw_common import (PACKAGE, Refusal, digest, emit, file_hash, guard_main, no_links, read, result, run, write_json)
from model_policy import recommend
from workflow_ops import delivery_gate, handoff, snapshot, evidence_inspect
from skill_maintenance import propose, candidate, install_plan, install, rollback, verify_package

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--destination',required=True);a=ap.parse_args()
    dest=no_links(a.destination)
    if dest.exists():raise Refusal('Demo requires a new destination')
    dest.mkdir(parents=True)
    repo=dest/'repo';repo.mkdir()
    cfg=read(PACKAGE/'assets/project.example.yaml');cfg['project']['id']='public-synthetic-demo'
    cfg['project']['repository']='EXAMPLE/NOT_A_REAL_REMOTE'
    write_json(dest/'team-workflow.yaml',cfg)
    for args in (['init','-b','main'],['config','user.name','Fixture Author'],['config','user.email','fixture@example.invalid']):
        run(['git','-C',repo,*args])
    # Original contract is the independent source; the implementation below is deliberately faulty.
    (repo/'contract.md').write_text('Signed 8-bit saturating addition. Output range [-128,127].\n',encoding='utf-8')
    (repo/'author-result.json').write_text('{"input":[120,20],"dut":-116,"reference":-116,"author_self_test":"PASS"}\n',encoding='utf-8')
    run(['git','-C',repo,'add','.']);run(['git','-C',repo,'commit','-m','synthetic fixture input'])
    head=run(['git','-C',repo,'rev-parse','HEAD']).stdout.decode().strip()
    task={'schema_version':1,'task_ref':'fixture:#42','actor_ref':'fixture-author','phase':'implementation',
          'activity':'implementation','contract_trusted':True,'execution_kind':'model_assisted','base_commit':head}
    write_json(dest/'task.json',task)
    recommendation=recommend(cfg,task);write_json(dest/'recommendation.json',recommendation)
    snap=snapshot(repo,{'schema_version':1,'files':['contract.md','author-result.json']})
    write_json(dest/'snapshot.json',snap)
    expected=127
    observed=read(repo/'author-result.json')['dut']
    basis={'input':[120,20],'original_requirement':'signed 8-bit saturation','independent_expected':expected,
           'observed':observed,'conclusion':'REPAIR_REQUIRED' if observed!=expected else 'NO_COUNTEREXAMPLE'}
    write_json(dest/'independent-counterexample.json',basis)
    facts={'schema_version':1,'author':'fixture-author','head_commit':head,'evidence_commit':head,
           'candidate_commit':head,'tested_candidate_commit':head,'scope':'synthetic numerical review',
           'completed':'Author result delivered; independent counterexample blocks acceptance',
           'independent_basis_ref':'contract.md + independent-counterexample.json','required_checks_status':'FAIL',
           'blocking_findings':['F-01 wrong overflow assumption'],'reviews':[],
           'new_checks':[basis],'limitations':['Synthetic fixture, no human approval, no FPGA/tool acceptance'],
           'evidence_refs':['snapshot.json','independent-counterexample.json']}
    report=handoff(facts,cfg,{**task,'phase':'review','activity':'review'})
    (dest/'handoff.md').write_text(report['markdown'],encoding='utf-8')
    write_json(dest/'integration-gate.json',delivery_gate(facts))
    feedback={'schema_version':1,'kind':'outer_rule','base_release':(PACKAGE/'VERSION').read_text().strip(),
              'problem':'Demonstrate explicit local candidate maintenance','requested_behavior':'Add a demo-only release note without changing installed rules'}
    write_json(dest/'proposal.json',propose(feedback))
    from ftw_common import tree
    request={**feedback,'base_tree_sha256':digest(tree(PACKAGE)),
             'scope':{'include':['CHANGELOG.md']},'protected_invariants':['No fake approvals','No model settings change'],
             'acceptance':['Only changelog differs'],
             'changes':[{'path':'CHANGELOG.md','base_sha256':file_hash(PACKAGE/'CHANGELOG.md'),
                         'content':(PACKAGE/'CHANGELOG.md').read_text(encoding='utf-8')+'\nDemo-only candidate annotation.\n'}]}
    candidate_dir=dest/'candidate';change=candidate(PACKAGE,request,candidate_dir,True)
    write_json(dest/'candidate-change.json',change)
    verification=verify_package(candidate_dir)
    target=dest/'sandbox-skills/fpga-team-workflow'
    first=install(install_plan(PACKAGE,target),True,'demo:local-fixture-install')
    upgrade=install(install_plan(candidate_dir,target),True,'demo:local-fixture-update')
    rolled=rollback(upgrade['transaction'],True,'demo:local-fixture-rollback')
    write_json(dest/'maintenance.json',{'schema_version':1,'candidate_verification':verification,
               'first_install':first,'upgrade':upgrade,'rollback':rolled})
    return emit(result(destination=str(dest),counterexample=basis,model_actual='UNKNOWN',
                       acceptance='BLOCKED_AS_EXPECTED',human_approval=False,
                       maintenance_verified=verification['status']=='OK' and rolled['verified']))

if __name__=='__main__':guard_main(main)
