import subprocess, json, sys
from pathlib import Path
git='C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
scope=['task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/center-target-20260914','docs/reviews/center-target-f9768b8']
roots=['F:/NUEC/develop','F:/NUEC/review-worktrees/member-b-to-a-pkg-b-alg','F:/NUEC/review-worktrees/center-target-f9768b8']
out={}
for r in roots:
    def g(*a): return subprocess.check_output([git,'-c','safe.directory='+r,'-C',r,*a]).decode().strip()
    status=g('status','--porcelain=v1','--untracked-files=all').splitlines()
    out[r]={'head':g('rev-parse','HEAD'),'branch':g('rev-parse','--abbrev-ref','HEAD'),
        'local_main':g('rev-parse','main'),'tracking_main':g('rev-parse','origin/main'),
        'ahead_behind':g('rev-list','--left-right','--count','main...origin/main'),
        'tracked_changes':sum(not s.startswith('??') for s in status),'untracked':sum(s.startswith('??') for s in status),
        'scope_status':g('status','--porcelain=v1','--untracked-files=all','--',*scope).splitlines(),
        'scope_ignored':g('ls-files','--others','--ignored','--exclude-standard','--',*scope).splitlines(),
        'status_inventory':status}
    if r.endswith('f9768b8'): out[r]['all_ignored']=g('ls-files','--others','--ignored','--exclude-standard').splitlines()
Path(sys.argv[1]).write_text(json.dumps(out,indent=2),encoding='utf-8')
for v in out.values(): v.pop('status_inventory')
print(json.dumps(out,indent=2))


