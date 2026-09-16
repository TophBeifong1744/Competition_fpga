"""B batch state; read-only, including direct remote refs."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
GIT='C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
roots={'shared':'F:/NUEC/develop','review':'F:/NUEC/review-worktrees/timerfixed-repair-17afe32','feedback':'F:/NUEC/review-worktrees/timerfixed-b-feedback'}
out=Path(sys.argv[1])
assert not out.exists()
results=[]
for name,root in roots.items():
    commands=[['rev-parse','HEAD'],['branch','--show-current'],['status','--porcelain=v1','--untracked-files=all'],['ls-files','--others','--ignored','--exclude-standard']]
    if name=='shared':
        commands += [['rev-parse','main','origin/main'],['rev-list','--left-right','--count','main...origin/main'],['ls-remote','origin','refs/heads/main','refs/heads/codex/toph/timerfixed-entry-20260916','refs/heads/review/member-b-timerfixed-bbe39c3']]
    for args in commands:
        argv=[GIT,'-c','safe.directory='+root,'-C',root,*args]
        env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='Never',GIT_HTTP_LOW_SPEED_LIMIT='1',GIT_HTTP_LOW_SPEED_TIME='20')
        with out.with_suffix('.stdout.tmp').open('w+b') as stdout, out.with_suffix('.stderr.tmp').open('w+b') as stderr:
            try:
                p=subprocess.run(argv,stdout=stdout,stderr=stderr,env=env,timeout=45)
                rc=p.returncode
            except subprocess.TimeoutExpired:
                rc=124
            stdout.seek(0);stderr.seek(0)
            results.append(dict(root=name,argv=argv,returncode=rc,stdout=stdout.read().decode('utf-8','replace'),stderr=stderr.read().decode('utf-8','replace')))
        out.write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),results=results),indent=2),encoding='utf-8')
report=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),results=results)
out.write_text(json.dumps(report,indent=2),encoding='utf-8')
for r in results:
    print(r['root'],r['argv'][5:],r['returncode'],r['stdout'][:500],r['stderr'][:500])
