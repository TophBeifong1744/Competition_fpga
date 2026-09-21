import hashlib,json,subprocess
from pathlib import Path
R=Path('F:/NUEC/r/psc');G='C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe';S='fbbaa161098582ba1e5e112b86d39533769bb3e7'
P='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/';D=P+'ps-semantic-bridge-candidate-01/';pack=R/D
def git(*a):return subprocess.check_output([G,'-c','core.longpaths=true','-c','safe.directory='+str(R),'-C',str(R),*a])
changes=git('diff','--name-status',S+'^',S).decode().splitlines();assert all(c.startswith('A\t'+P) for c in changes)
trees=git('ls-tree','-r',S,'--',P).decode().splitlines();blobs={x.split('\t',1)[1]:x.split()[2] for x in trees}
for change in changes:
 p=change.split('\t')[1];data=(R/p).read_bytes();assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==blobs[p]
files=json.loads((pack/'PACKAGE-SHA256.json').read_text())['files'];assert len(files)==1479
actual={p.relative_to(pack).as_posix() for p in pack.rglob('*') if p.is_file()};assert actual==set(files)|{'PACKAGE-SHA256.json','MANIFEST.sha256'}
for name,v in files.items():
 data=(pack/name).read_bytes();assert hashlib.sha256(data).hexdigest()==v['sha256'];assert len(data)==v['bytes']
digest=hashlib.sha256((pack/'PACKAGE-SHA256.json').read_bytes()).hexdigest();assert digest=='e774f248f3995839f952db5c9d18eafeb3b7ece02f3897102cead1a65ace75b2';assert (pack/'MANIFEST.sha256').read_text().split()[0]==digest
cache={};count=0
for binding in pack.glob('evidence/run*/bindings.json'):
 for row in json.loads(binding.read_text()):
  data=(binding.parent/'inputs'/row['snapshot']).read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256']
  if 'commit' in row:
   key=(row['commit'],row['path'])
   if key not in cache:cache[key]=git('show',key[0]+':'+key[1])
   assert data==cache[key];count+=1
result=dict(sha=S,added_files=len(changes),package_files=len(actual),manifest_entries=len(files),publication_extra_files=len(changes)-len(actual),git_bound_snapshots=count,unique_sources=len(cache),old_files_modified=0)
Path(__file__).with_name('results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
