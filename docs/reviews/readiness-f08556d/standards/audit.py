import subprocess,pathlib,hashlib,json,tarfile,io,re
root=pathlib.Path('F:/NUEC/r/ready');out=pathlib.Path('F:/NUEC/review-evidence/readiness-f08556d/standards'); g='C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
def git(*a):return subprocess.check_output([g,'-c','safe.directory='+str(root),*a],cwd=root)
old='cf026cf29518488f8c7275b825f3487a8d892f80';new='f08556d01821d6c3c8204fdac2c38f53b2107c05'; prefix='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/'
diff=git('diff','--name-status',old,new).decode().splitlines();assert len(diff)==29 and all(x.startswith('A\t'+prefix) for x in diff)
paths=[x.split('\t')[1] for x in diff]
with tarfile.open(fileobj=io.BytesIO(git('archive',new,*paths))) as t:
 for m in t.getmembers():
  if m.isfile():assert t.extractfile(m).read()==(root/m.name).read_bytes(),m.name
count=0; pins={}; sources=[];links=[]
for run in ['run01','run02','clean02']:
 d=root/prefix/'evidence'/('readiness-20260921-'+run)
 manifest=json.loads((d/'OUTPUT-SHA256.json').read_bytes()); assert len(manifest)==6
 for f,h in manifest.items():assert hashlib.sha256((d/f).read_bytes()).hexdigest()==h;count+=1
 for row in json.loads((d/'bindings.json').read_bytes()):
  key=row['commit']+':'+row['path']
  if key not in pins:pins[key]=git('show',key)
  assert hashlib.sha256(pins[key]).hexdigest()==row['sha256'] and len(pins[key])==row['bytes']
  assert git('rev-parse',key).decode().strip()==row['blob']
 if run!='run01':
  for n,h in json.loads((d/'source-sha256.json').read_bytes()).items():assert hashlib.sha256((root/prefix/n).read_bytes()).hexdigest()==h;sources.append(run+':'+n)
for p in paths:
 if p.endswith('.md'):
  for target in re.findall(r'\]\(([^)]+)\)',(root/p).read_text(encoding='utf-8')):
   if not target.startswith(('http','#')):assert (root/p).parent.joinpath(target).exists(),target;links.append(target)
failure=json.loads((root/prefix/'evidence/readiness-20260921-clean-failed01/FAILURE.json').read_bytes()); assert '128' in str(failure)
result={'head':git('rev-parse','HEAD').decode().strip(),'added':29,'modified_or_deleted':0,'new_git_bytes_match':True,'output_manifest_items':count,'unique_pinned_sources':len(pins),'final_source_hashes':len(sources),'relative_links_checked':len(links),'failed_git_128_preserved':True}
(out/'audit.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result))

