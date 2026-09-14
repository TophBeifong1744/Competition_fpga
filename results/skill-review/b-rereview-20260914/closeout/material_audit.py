import datetime,hashlib,json,pathlib,subprocess,sys
R=pathlib.Path(__file__).parent;OUT=R/('materials-'+sys.argv[1]+'.json');assert not OUT.exists()
W=pathlib.Path('F:/NUEC/review-worktrees/member-b-to-a-pkg-b-alg')
scopes=['skill/fpga-module-verification','skill/pynq-overlay-dma-validation','task-packages/PKG-A-SKILLS']
def git(w,*a):return subprocess.check_output(['git','-c','safe.directory='+str(w),'-C',str(w),*a])
out=dict(timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),worktrees=[])
for w in [W,pathlib.Path('F:/NUEC/develop')]+[pathlib.Path('F:/NUEC/review-worktrees')/n for n in ['b-skl001-a7e1ea9','b-skl002-3ac597d','b-skl001-c562466','b-skl002-55039cf','b-skills-main-20260914']]:
    if not w.exists():out['worktrees'].append(dict(path=str(w),exists=False));continue
    state=git(w,'status','--porcelain=v1','--untracked-files=all').decode().splitlines()
    scope=git(w,'status','--porcelain=v1','--untracked-files=all','--ignored','--',*scopes).decode().splitlines()
    o=dict(path=str(w),exists=True,head=git(w,'rev-parse','HEAD').decode().strip(),branch=git(w,'branch','--show-current').decode().strip(),status_count=len(state),scoped_status=scope,ignored_scoped_count=sum(s.startswith('!!') for s in scope),files=[])
    if str(w).replace('\\','/').endswith('/develop'):
        for row in scope:
            if not row.startswith('?? '):continue
            path=row[3:];p=w/path
            if not p.is_file():continue
            b=p.read_bytes();old=git(w,'show','57c50e6c99731cd57e7738ac91b02f985ad229b1:'+path)
            o['files'].append(dict(path=path,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),matches_historical_main_after_crlf=b.replace(b'\r\n',b'\n')==old.replace(b'\r\n',b'\n'),disposition='Pre-existing old baseline in dirty unrelated algorithm worktree; retain without switching/resetting. Recoverable at historical main 57c50e6.'))
    else:
        for row in scope:
            if not row.startswith('?? '):continue
            path=row[3:];p=w/path
            if not p.is_file():continue
            b=p.read_bytes();matches=[]
            for root in [W/'results/skill-review/b-rereview-20260914',pathlib.Path('F:/NUEC/review-worktrees/b-skills-main-20260914/results/skill-review/b-20260914')]:
                for q in root.rglob(p.name):
                    if q.is_file() and q.read_bytes()==b:matches.append(str(q))
            o['files'].append(dict(path=path,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),archived_exact_matches=matches))
    out['worktrees'].append(o)
out['local_main']=git(W,'rev-parse','main').decode().strip();out['origin_main']=git(W,'rev-parse','origin/main').decode().strip()
out['ahead_behind']=git(W,'rev-list','--left-right','--count','main...origin/main').decode().strip()
OUT.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps([dict(path=w['path'],status_count=w.get('status_count'),scoped=len(w.get('scoped_status',[])),ignored=w.get('ignored_scoped_count'),missing_archive=[f['path'] for f in w.get('files',[]) if 'archived_exact_matches' in f and not f['archived_exact_matches']],old_baseline_mismatch=[f['path'] for f in w.get('files',[]) if f.get('matches_historical_main_after_crlf') is False]) for w in out['worktrees']],indent=2))
