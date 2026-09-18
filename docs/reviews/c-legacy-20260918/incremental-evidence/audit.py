import subprocess, pathlib, hashlib, json, re, posixpath, sys
repo = pathlib.Path(sys.argv[1])
out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=False)
sha = '62a252081d52b3aa9d9dc142f7cc2bf298d9c34d'
base = 'bff9369a5c7f166344c02095df61e91e1c2f4681'
def git(*args): return subprocess.check_output(['git','-C',str(repo),*args])
def blob(rev,path): return git('show',rev+':'+path)
def h(data): return hashlib.sha256(data).hexdigest()
def save(name,data): (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
paths = git('diff','--name-only',base,sha).decode().splitlines()
tree = set(git('ls-tree','-r','--name-only',sha).decode().splitlines())
arc='archive/2026-09-07-before-materials-cleanup/'
p='docs/work-packages-2026-09-06.md'
snap='task-packages/WP-A0/evidence/reference-snapshots/'+arc
manifest=json.loads(blob(sha,arc+'MANIFEST.json'))
items=[dict(path=x['path'],expected=x['sha256'],actual=h(blob(sha,snap+x['path']))) for x in manifest['files']]
old=blob('f0f397f',arc+p); merged=blob('1e7e091',arc+p); current=blob(sha,arc+p); packaged=blob(sha,snap+p)
facts={'candidate':sha,'baseline':base,'changed_paths':paths,'original_blob':git('rev-parse','f0f397f:'+arc+p).decode().strip(),'original_sha256':h(old),'merge_sha256':h(merged),'current_sha256':h(current),'package_sha256':h(packaged),'checkout_sha256':h((repo/arc/p).read_bytes()),'merge_parents':git('show','-s','--format=%P','1e7e091').decode().strip(),'line_count':len(current.splitlines()),'current_equals_merge':current==merged,'crlf_conversion_equals_package':current.replace(b'\n',b'\r\n')==packaged,'only_status_changed':old.replace('未开始'.encode(),'待复核'.encode(),1)==merged,'manifest_unchanged_since_original':blob('f0f397f',arc+'MANIFEST.json')==blob(sha,arc+'MANIFEST.json'),'snapshot_matches':sum(x['expected']==x['actual'] for x in items),'snapshot_total':len(items),'snapshot_items':items}
# Exact byte checks; no reliance on checkout normalization.
assert facts['original_sha256']=='f0ceb76c937931238a16644c5ba41f6337910951744267431df4faee4d0971b4'
assert facts['merge_sha256']=='f188fa64f6bf11a38a2e5d2454471693f1b591faf9406bb12294fbb3fa70b310'
assert facts['package_sha256']=='541e04d6d7bcd43c8bf838b568844eb227f2430812dcb8d8eb1fd6595ed42f5c'
assert facts['snapshot_matches']==24 and len(items)==25
facts['only_status_changed'] = old.replace(b'| WP-C1 |'+old.split(b'| WP-C1 |')[1].split(b'\n')[0], (b'| WP-C1 |'+old.split(b'| WP-C1 |')[1].split(b'\n')[0]).replace('未开始'.encode(),'待复核'.encode()))==merged
save('partial.json',facts)
assert all(facts[k] for k in ['current_equals_merge','crlf_conversion_equals_package','only_status_changed','manifest_unchanged_since_original'])
meeting=next(x for x in manifest['files'] if 'meeting-' in x['path'])
facts['meeting_original_git_hash']=h(blob('f0f397f',arc+meeting['path']))
facts['meeting_manifest_hash']=meeting['sha256']
facts['historical_diff']=git('diff','f0f397f','1e7e091','--',arc+p).decode()
facts['active_status_diff']=git('show','f2df726','--','docs/work-packages-2026-09-06.md').decode()
links=[]
for path in paths:
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',blob(sha,path).decode()):
        if re.match(r'\w+://',target): continue
        file,_,anchor=target.partition('#')
        resolved=posixpath.normpath(posixpath.join(posixpath.dirname(path),file)) if file else path
        exists=resolved in tree
        anchor_ok=True
        if exists and anchor:
            content=blob(sha,resolved).decode()
            headings=re.findall(r'^#{1,6}\s+(.+)$',content,re.M)
            slugs=[re.sub(r'[^\w\- ]','',x.lower()).replace(' ','-') for x in headings]
            anchor_ok=anchor in slugs or ('id="'+anchor+'"') in content
        links.append(dict(source=path,target=target,resolved=resolved,exists=exists,anchor_ok=anchor_ok))
facts['links']=links
assert all(x['exists'] and x['anchor_ok'] for x in links), [x for x in links if not x['exists'] or not x['anchor_ok']]
check=subprocess.run(['git','-C',str(repo),'diff','--check',base,sha],capture_output=True)
facts['diff_check']={'exit':check.returncode,'stdout':check.stdout.decode(),'stderr':check.stderr.decode()}; assert check.returncode==0
# Export only exact package bytes and referenced original paths for existing checker.
export=out/'exact'; export.mkdir()
selected={'task-packages/verify-toph-handoffs.ps1'}
for package in ['WP-A0','3D-P4']:
    prefix='task-packages/'+package+'/'
    selected.update(x for x in tree if x.startswith(prefix))
    fm=json.loads(blob(sha,prefix+'evidence/files.json'))
    selected.update(x['path'] for x in fm['references'] if x['path'] in tree)
for path in selected:
    dest=export/path; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(blob(sha,path))
facts['checks']=[]
for package in ['WP-A0','3D-P4']:
    cmd=['pwsh','-NoProfile','-ExecutionPolicy','Bypass','-File',str(export/'task-packages/verify-toph-handoffs.ps1'),'-PackageId',package]
    run=subprocess.run(cmd,capture_output=True)
    (out/(package+'.stdout.txt')).write_bytes(run.stdout); (out/(package+'.stderr.txt')).write_bytes(run.stderr)
    facts['checks'].append(dict(command=cmd,cwd=str(pathlib.Path.cwd()),exit=run.returncode,stdout=run.stdout.decode('utf-8',errors='replace'),stderr=run.stderr.decode('utf-8',errors='replace')))
    assert run.returncode==0
save('audit.json',facts)
print(json.dumps({k:v for k,v in facts.items() if k not in ['snapshot_items','links','historical_diff','active_status_diff','checks']},ensure_ascii=False,indent=2))
print('LINKS',len(links),'PASS')
for x in facts['checks']: print(x['stdout'])
