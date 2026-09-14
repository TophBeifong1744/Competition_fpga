import datetime,json,pathlib,subprocess,sys
R=pathlib.Path(__file__).parent;W='F:/NUEC/review-worktrees/member-b-to-a-pkg-b-alg';API='repos/TophBeifong1744/Competition_fpga/'
def git(w,*a):return subprocess.check_output(['git','-c','safe.directory='+w,'-C',w,*a],text=True).strip()
def ref(branch,missing=False):
    r=subprocess.run(['gh','api',API+'git/ref/heads/'+branch],capture_output=True)
    if missing:
        assert r.returncode and b'404' in r.stderr;return dict(branch=branch,deleted=True,http_status=404)
    assert r.returncode==0,r.stderr
    return json.loads(r.stdout)['object']['sha']
out=dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actual_main_worktree=W,local_main=git(W,'rev-parse','main'),origin_main=git(W,'rev-parse','origin/main'),direct_remote_main=ref('main'),ahead_behind=git(W,'rev-list','--left-right','--count','main...origin/main'),main_status=git(W,'status','--porcelain=v1','--untracked-files=all'),feedback_ref=ref('review/member-b-skills-20260914'),closed=[])
for branch in ['codex/toph/skl001-module-verification-20260914','codex/toph/skl002-pynq-validation-20260914']:out['closed'].append(ref(branch,True))
out['dirty_develop']=dict(branch=git('F:/NUEC/develop','branch','--show-current'),head=git('F:/NUEC/develop','rev-parse','HEAD'),local_main=git('F:/NUEC/develop','rev-parse','main'),origin_main=git('F:/NUEC/develop','rev-parse','origin/main'),status_count=len(git('F:/NUEC/develop','status','--porcelain=v1','--untracked-files=all').splitlines()))
assert out['local_main']==out['origin_main']==out['direct_remote_main']==out['dirty_develop']['local_main']==out['dirty_develop']['origin_main']
assert not out['main_status']
(R/('refs-'+sys.argv[1]+'.json')).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,indent=2))
