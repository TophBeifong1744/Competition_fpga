import hashlib,json,subprocess
from pathlib import Path
E=Path(__file__).resolve().parent
prefix='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/current_build'
def git(root,*args):return subprocess.check_output(['git','-c','core.longpaths=true','-c','safe.directory='+root,'-C',root,*args]).decode().strip()
rows=[]
for root in ['F:/NUEC/develop','F:/NUEC/review-worktrees/member-b-to-a-pkg-b-alg','F:/NUEC/review-worktrees/a-ps-repair-d0ce1c2']:
    status=git(root,'status','--porcelain=v1','--untracked-files=all').splitlines()
    scoped=git(root,'status','--porcelain=v1','--untracked-files=all','--',prefix).splitlines()
    ignored=git(root,'ls-files','--others','--ignored','--exclude-standard','--',prefix).splitlines()
    rows.append(dict(root=root,branch=git(root,'branch','--show-current'),head=git(root,'rev-parse','HEAD'),local_main=git(root,'rev-parse','main'),tracking_main=git(root,'rev-parse','origin/main'),main_tracking_ahead_behind=git(root,'rev-list','--left-right','--count','main...origin/main'),modified_staged_tracked=sum(not x.startswith('??') for x in status),untracked=sum(x.startswith('??') for x in status),scope_status=scoped,scope_ignored=ignored,other_status=status))
report={'main_merge_commit':git(rows[1]['root'],'rev-parse','HEAD'),'snapshots':rows,'a_machine_checked':False,'a_branch_pub_build_dirs_retained':True}
(E/'08-batch-snapshot.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for r in rows:print(r['root'],r['branch'],'tracked differences',r['modified_staged_tracked'],'untracked',r['untracked'],'batch differences',len(r['scope_status']),'batch ignored',len(r['scope_ignored']))
