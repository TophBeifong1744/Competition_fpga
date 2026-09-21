import hashlib,json,subprocess
from pathlib import Path
G='C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
base='1f369dc688cc1e49d5b2b51735bce7dc9d1cfb78'
prefix='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/'
out=[]
for short,sha,dirname in [('logic-f879a54','f879a54cf40359209895af955bcef92accdf79ea','increment-20260923'),('engineering-0abdc91','0abdc91c57787b7c868a797b88f35129de169faf','engineering-closeout-20260923')]:
 root=Path('F:/NUEC/review-worktrees/review-h3-'+short); pack=root/prefix/dirname
 def git(*args):return subprocess.check_output([G,'-c','core.longpaths=true','-c','safe.directory='+str(root),'-C',str(root),*args])
 changes=git('diff','--name-status',base,sha).decode().splitlines()
 extras={'A\t'+prefix+'.gitattributes','A\t'+prefix+'PUBLICATION-INCREMENT-20260923.md'} if dirname.startswith('increment') else set()
 assert all(x.startswith('A\t'+prefix+dirname+'/') or x in extras for x in changes),changes
 files=json.loads((pack/'PACKAGE-SHA256.json').read_text())['files']
 listed=set(files); actual={x.relative_to(pack).as_posix() for x in pack.rglob('*') if x.is_file()}
 assert actual-listed==({'PACKAGE-SHA256.json'} if dirname.startswith('increment') else {'PACKAGE-SHA256.json','MANIFEST.sha256'})
 for name,v in files.items():
  data=(pack/name).read_bytes(); expected=v if isinstance(v,str) else v['sha256']
  assert hashlib.sha256(data).hexdigest()==expected,name
  if isinstance(v,dict):assert len(data)==v['bytes'],name
 for x in actual:assert (pack/x).read_bytes()==git('show',sha+':'+prefix+dirname+'/'+x),x
 snapshots=0;local=0
 for binding in pack.glob('evidence/run*/bindings.json'):
  for row in json.loads(binding.read_text()):
   snapshot=binding.parent/row['snapshot']
   if not snapshot.exists():snapshot=binding.parent/'inputs'/row['snapshot']
   data=snapshot.read_bytes()
   assert hashlib.sha256(data).hexdigest()==row['sha256'],row
   if 'commit' in row:assert data==git('show',row['commit']+':'+row['path']),row;snapshots+=1
   else:local+=1
 if (pack/'MANIFEST.sha256').exists():assert (pack/'MANIFEST.sha256').read_text().split()[0]==hashlib.sha256((pack/'PACKAGE-SHA256.json').read_bytes()).hexdigest()
 source_record=pack/'evidence/run02/source-sha256.json'
 sources=json.loads(source_record.read_text()) if source_record.exists() else json.loads((pack/'evidence/run03/command.json').read_text())['source_sha256']
 for name,digest in sources.items():assert hashlib.sha256((pack/'source'/name).read_bytes()).hexdigest()==digest,name
 out.append(dict(sha=sha,added_files=len(changes),manifest_entries=len(files),all_bytes_match_commit=True,git_bound_snapshots=snapshots,local_only_snapshots=local,scope_only=True))
Path(__file__).with_name('results.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
