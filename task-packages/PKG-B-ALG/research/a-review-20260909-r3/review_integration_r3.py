"""A integration regression. No original evidence is overwritten."""
import json, subprocess, sys
from pathlib import Path
repo,out=map(lambda x:Path(x).resolve(),sys.argv[1:3]);out.mkdir(exist_ok=False)
root=repo/'task-packages/PKG-B-ALG';old=root/'revisions/pr3-repro-01';new=root/'revisions/pr3-input-reference-02'
def git(*a):return subprocess.check_output(['git',*a],cwd=repo)
main='6ea647d5a9b6d27b164fde4c78103d50e5d1e43e';head='6491d1bab04038b71fdd8c22d45a58455aa58ade'
assert not git('diff','--cached','--diff-filter=MD','--name-only').strip()
assert git('show',main+':task-packages/PKG-B-ALG/REVIEW.md')==(root/'REVIEW.md').read_bytes()
names=['tonal-edge-01','narrowband-guard-01','subband-confidence-01','leave-band-out-01','effective-perturbation-01','stable-wrong-01']
commands=[('release',[sys.executable,'-B',str(new/'verify_release.py')]),('reference-tests',[sys.executable,'-B',str(new/'test_reference.py')])]
for stage,package in [('unit','')]+[('tests',n) for n in names]+[('final',n) for n in names[:-1]]:
    key=stage+('-'+package if package else '')
    commands.append((key,[sys.executable,'-B',str(old/'run_all.py'),'--stage',stage,'--package',package,'--out',str(out/key)]))
commands.append(('live',[sys.executable,'-B',str(new/'run_all.py'),'--out',str(out/'live')]))
results=[]
for name,cmd in commands:
    print('RUN',name,flush=True)
    with (out/(name+'.log')).open('w',encoding='utf-8') as f:
        cp=subprocess.run(cmd,cwd=root,stdout=f,stderr=subprocess.STDOUT)
    results.append(dict(name=name,command=cmd,returncode=cp.returncode))
    (out/'stages.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    print('PASS' if cp.returncode==0 else 'FAIL',name,flush=True)
data=dict(status='PASS' if all(r['returncode']==0 for r in results) else 'FAIL',reviewed_sha=head,main_sha=main,existing_main_files_preserved=True,root_review_preserved=True,stages=results)
(out/'result.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
assert data['status']=='PASS'
