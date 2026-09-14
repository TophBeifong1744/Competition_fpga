import hashlib,json,pathlib,re,subprocess,sys
R=pathlib.Path(__file__).parent;W=pathlib.Path('F:/NUEC/review-worktrees/member-b-to-a-pkg-b-alg');E='results/skill-review/b-rereview-20260914/'
def git(*a):return subprocess.check_output(['git','-c','safe.directory='+str(W),'-C',str(W),*a])
head=git('rev-parse','HEAD').decode().strip()
requests=[]
for manifest,root,sha in [(E+'manifest-all.json',E,head),('task-packages/PKG-A-SKILLS/repair-manifest.json','','a7e1ea976da91ba735af5c0a79fffdc7d10c121f'),('skill/pynq-overlay-dma-validation/repair-manifest.json','skill/pynq-overlay-dma-validation/','3ac597d1d16982e0a5c5a114202ca8568dc28d8f')]:
    m=json.loads(git('show',head+':'+manifest))
    for f in m['files']:requests.append((root+f['path'],f))
raw=subprocess.run(['git','-c','safe.directory='+str(W),'-C',str(W),'cat-file','--batch'],input=('\n'.join(head+':'+p for p,f in requests)+'\n').encode(),capture_output=True,check=True).stdout
pos=0;bad=[]
for path,f in requests:
    end=raw.index(b'\n',pos);header=raw[pos:end].split();assert header[1]==b'blob',header
    size=int(header[2]);data=raw[end+1:end+1+size];pos=end+size+2
    if size!=f['bytes'] or hashlib.sha256(data).hexdigest()!=f['sha256'] or (W/path).read_bytes()!=data:bad.append(path)
identity=[]
for sha,paths in [('a7e1ea976da91ba735af5c0a79fffdc7d10c121f',['skill/fpga-module-verification','task-packages/PKG-A-SKILLS']),('3ac597d1d16982e0a5c5a114202ca8568dc28d8f',['skill/pynq-overlay-dma-validation'])]:
    identity.append(dict(candidate=sha,paths=paths,exact=not git('diff',sha,head,'--',*paths)))
production=git('diff','--name-only','57c50e6c99731cd57e7738ac91b02f985ad229b1',head,'--','rtl','tb','sim','ps','vivado','hardware','deliverables').decode().splitlines()
links=[]
for rel in ['skill/README.md','docs/maintenance/skills-rereview-b-2026-09-14.md',E+'README.md']:
    p=W/rel
    for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if '://' in link or link.startswith('#'):continue
        target=link.split('#')[0]
        if not (p.parent/target).exists():links.append(dict(source=rel,target=link))
o=dict(head=head,manifest_entries=len(requests),bad_bytes=bad,candidate_identity=identity,production_changes=production,missing_local_links=links)
(R/('release-verification-'+sys.argv[1]+'.json')).write_text(json.dumps(o,indent=2)+'\n',encoding='utf-8')
print(json.dumps(o,indent=2));assert not bad and all(i['exact'] for i in identity) and not production and not links
