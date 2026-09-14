import datetime,json,pathlib,subprocess
R=pathlib.Path(__file__).parent;W='F:/NUEC/review-worktrees/member-b-to-a-pkg-b-alg';API='repos/TophBeifong1744/Competition_fpga/'
def git(*a):return subprocess.check_output(['git','-c','safe.directory='+W,'-C',W,*a])
def api(path,method='GET'):
    r=subprocess.run(['gh','api',API+path,'--method',method],capture_output=True)
    if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace'))
    return json.loads(r.stdout) if r.stdout.strip() else None
head=git('rev-parse','HEAD').decode().strip();assert head=='d2cff38c19e06238bed9d4a195f72640527a1c12'
assert api('git/ref/heads/main')['object']['sha']==head
assert git('rev-parse','origin/main').decode().strip()==head
assert not git('status','--porcelain=v1')
out=dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),main=head,closed=[])
for branch,sha in [('codex/toph/skl002-pynq-validation-20260914','3ac597d1d16982e0a5c5a114202ca8568dc28d8f'),('codex/toph/skl001-module-verification-20260914','a7e1ea976da91ba735af5c0a79fffdc7d10c121f')]:
    before=api('git/ref/heads/'+branch);assert before['object']['sha']==sha
    git('merge-base','--is-ancestor',sha,head)
    assert not git('branch','--list',branch), 'Unexpected local author branch; do not delete without audit'
    api('git/refs/heads/'+branch,'DELETE')
    r=subprocess.run(['gh','api',API+'git/ref/heads/'+branch],capture_output=True);assert r.returncode!=0 and b'404' in r.stderr
    tracking='refs/remotes/origin/'+branch
    exists=subprocess.run(['git','-c','safe.directory='+W,'-C',W,'show-ref','--verify','--quiet',tracking])
    if exists.returncode==0:git('update-ref','-d',tracking,sha)
    out['closed'].append(dict(branch=branch,sha=sha,remote_deleted=True,remote_verified_404=True,local_branch_existed=False,tracking_removed=exists.returncode==0,recovery='Reachable as reviewed parent of main merge commit'))
assert api('git/ref/heads/main')['object']['sha']==head
(R/'branch-cleanup.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,indent=2))
