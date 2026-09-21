import subprocess,pathlib,hashlib,json,tarfile,io
root=pathlib.Path('F:/NUEC/r/psr'); out=pathlib.Path('F:/NUEC/review-evidence/ps-repair-ca512a8/standards')
g='C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
def git(*a):return subprocess.check_output([g,'-c','safe.directory='+str(root),*a],cwd=root)
old='fbbaa161098582ba1e5e112b86d39533769bb3e7'; new='ca512a8be7978ab6ca2ade3d5e0b922e53a89c79'; prefix='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/'; fix=prefix+'ps-semantic-bridge-repair-01/'; orig=prefix+'ps-semantic-bridge-candidate-01/'
diff=git('diff','--name-status',old,new).decode().splitlines(); assert len(diff)==517; assert all(x.startswith('A\t'+fix) for x in diff)
def archived(commit,path):
 with tarfile.open(fileobj=io.BytesIO(git('archive',commit,path))) as t:return {m.name:t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
newbytes=archived(new,fix); oldbytes=archived(old,orig)
bad=[]
for row in diff:
 p=row.split('\t')[1]
 if newbytes[p]!=(root/p).read_bytes():bad.append(p)
assert not bad
assert not git('diff',old,new,'--',orig)
files=git('ls-tree','-r','--name-only',old,'--',orig).decode().splitlines(); assert len(files)==1481
badold=[p for p in files if oldbytes[p]!=(root/p).read_bytes()]; assert not badold
bindings=[]
for f in [(root/fix/'evidence/run01/bindings.json')]:
 vals=json.loads(f.read_bytes())
 for row in vals:
  blob=git('show',row['commit']+':'+row['path']); assert hashlib.sha256(blob).hexdigest()==row['sha256']; assert blob==(f.parent/row['file']).read_bytes()
  bindings.append({'commit':row['commit'],'path':row['path']})
report={'head':git('rev-parse','HEAD').decode().strip(),'added':len(diff),'changed_outside':0,'new_working_bytes_match':True,'original_files':len(files),'original_unchanged_and_working_bytes_match':True,'archived_pins_checked':len(bindings),'pins':bindings}
(out/'byte-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='pins'}))


