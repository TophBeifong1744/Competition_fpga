"""Independent read-only B review of the pinned engineering publication."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

AUTHOR='2aed019574683438cd1ddfad0388fecaa7d6af63'
BASE='02a41b4507b4544e2fdf1d20a28996997110c337'
TASK='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    repo=args.repo.resolve();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    git=['git','-c',f'safe.directory={repo}']
    def g(*cmd):return subprocess.check_output(git+list(cmd),cwd=repo)
    names=g('diff','--name-only','-z',BASE,AUTHOR).decode().split('\0');names=[n for n in names if n]
    assert len(names)==195 and all(n.startswith(TASK+'/') for n in names)
    protected={}
    for name in names:
        data=(repo/name).read_bytes();fixed=g('show',f'{AUTHOR}:{name}')
        assert data==fixed,('not author bytes',name)
        protected[name]=hashlib.sha256(data).hexdigest()
    task=repo/TASK
    commands=[
        ('manifest',[sys.executable,'-B',str(task/'verify_delivery_20260912.py')]),
        ('tests',[sys.executable,'-B','-m','unittest','discover','-s',str(task/'source'),'-p','test_*.py','-v']),
        ('archived-rtl-export',[sys.executable,'-B',str(task/'source/check_sim_export.py'),str(task/'evidence/c-adapter-sim01/accepted_words.csv'),str(out/'sim-export')])]
    results=[]
    for name,cmd in commands:
        run=subprocess.run(cmd,cwd=repo,capture_output=True)
        (out/f'{name}.stdout.txt').write_bytes(run.stdout);(out/f'{name}.stderr.txt').write_bytes(run.stderr)
        results.append(dict(name=name,command=cmd,exit_code=run.returncode))
    after={n:hashlib.sha256((repo/n).read_bytes()).hexdigest() for n in names}
    assert protected==after,'Author files changed'
    summary=dict(author_sha=AUTHOR,base_sha=BASE,checkout_sha=g('rev-parse','HEAD').decode().strip(),
        python=sys.version,platform=platform.platform(),protected_files=protected,commands=results,
        status='PASS_SOFTWARE_AND_IDENTITY_ONLY' if all(x['exit_code']==0 for x in results) else 'FAIL',
        limitations=['No new RTL simulation, synthesis, route, board or recording performed',
            'Archived AXIS words reused to test export; does not prove current RTL execution',
            'Original one/recovery/epro2/BSP environmental inputs not accessed'])
    (out/'result.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(summary['status'],len(names),'author files unchanged')
    return 0 if all(x['exit_code']==0 for x in results) else 1

if __name__=='__main__':raise SystemExit(main())
