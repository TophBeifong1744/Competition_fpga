from pathlib import Path
import subprocess,json,hashlib
ROOT=Path('F:/NUEC/r/h3r')
G='C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
SHA='a7f70c5149a6503effdbbf16a9903d42c2d39e6d'
OLD='0abdc91c57787b7c868a797b88f35129de169faf'
P='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/engineering-closeout-20260923/'
def git(*args):return subprocess.check_output([G,'-c','core.longpaths=true','-c','safe.directory='+str(ROOT),'-C',str(ROOT),*args])
changes=git('diff','--name-status',OLD,SHA).decode().splitlines()
assert len(changes)==443 and all(x.startswith('A\t'+P) for x in changes)
def tree(sha):return {line.split('\t',1)[1]:line.split()[2] for line in git('ls-tree','-r',sha,'--',P).decode().splitlines()}
old=tree(OLD);new=tree(SHA)
assert len(old)==75 and all(new[k]==v for k,v in old.items())
for path,blob in new.items():
 data=(ROOT/path).read_bytes()
 assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==blob,path
repair=ROOT/P/'repair-h3-e01-e03'
manifest=json.loads((repair/'SHA256.json').read_text());assert len(manifest)==422
assert {p.relative_to(repair).as_posix() for p in repair.rglob('*') if p.is_file()}==set(manifest)|{'SHA256.json'}
for name,digest in manifest.items():assert hashlib.sha256((repair/name).read_bytes()).hexdigest()==digest,name
assert hashlib.sha256((repair/'SHA256.json').read_bytes()).hexdigest()=='130cf067ca2dcbe21ff3ad3a70fc2d92881bc0aa3948b6d6c4d3dc25988aa6c5'
count=0
cache={}
for binding in (ROOT/P).glob('**/bindings.json'):
 rows=json.loads(binding.read_text())
 if not isinstance(rows,list) or not rows or 'file' not in rows[0]:continue
 for row in rows:
  data=(binding.parent/row['file']).read_bytes()
  assert hashlib.sha256(data).hexdigest()==row['sha256'],row
  if 'commit' in row:
   key=(row['commit'],row['path'])
   if key not in cache:cache[key]=git('show',row['commit']+':'+row['path'])
   assert data==cache[key],row
   assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==row['blob']
   count+=1
result=dict(sha=SHA,additions=len(changes),original_files_unchanged=len(old),manifest_entries=len(manifest),all_commit_blobs_match=True,exact_git_binding_rows=count,unique_pinned_blobs=len(cache))
Path(__file__).with_name('results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
