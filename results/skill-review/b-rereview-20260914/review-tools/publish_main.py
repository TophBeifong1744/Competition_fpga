"""Publish a locally reviewed commit, verifying Git object identity and non-force ancestry.
Only main is updated. API payloads and replies are retained; no credential output.
"""
import base64,concurrent.futures,datetime,json,pathlib,re,subprocess,sys
R=pathlib.Path(__file__).parent
W='F:/NUEC/review-worktrees/member-b-to-a-pkg-b-alg'
BASE=sys.argv[1]; CANDIDATE=sys.argv[2] if len(sys.argv)>2 else None
API='repos/TophBeifong1744/Competition_fpga/'
def git(*a):return subprocess.check_output(['git','-c','safe.directory='+W,'-C',W,*a])
TARGET=git('rev-parse','HEAD').decode().strip()
OUT=R/'main-publication-api'/TARGET;OUT.mkdir(parents=True,exist_ok=True)
def api(path,body=None,label=None,method=None):
    cmd=['gh','api',API+path]
    if body is not None:
        f=OUT/((label or path.replace('/','_'))+'-request.json');f.write_text(json.dumps(body,ensure_ascii=False),encoding='utf-8');cmd+=['--method',method or 'POST','--input',str(f)]
    r=subprocess.run(cmd,capture_output=True)
    if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace'))
    if label:(OUT/(label+'-response.json')).write_bytes(r.stdout)
    return json.loads(r.stdout)
def remote(branch,label=None):return api('git/ref/heads/'+branch,label=label)['object']['sha']
assert git('branch','--show-current').decode().strip()=='main'
assert not git('status','--porcelain=v1'), 'Local main must be clean before publication'
assert remote('main','main-before')==BASE,'Remote main moved; do not overwrite it'
git('merge-base','--is-ancestor',BASE,TARGET)
raw=git('cat-file','commit',TARGET).decode();headers,message=raw.split('\n\n',1)
fields={};parents=[]
for line in headers.splitlines():
    key,value=line.split(' ',1)
    if key=='parent':parents.append(value)
    else:fields[key]=value
assert parents[0]==BASE and set(fields)=={'tree','author','committer'}
allowed=['AGENTS.md','skill/README.md','docs/maintenance/skills-publication-2026-09-14.md','docs/maintenance/skills-rereview-b-2026-09-14.md','results/skill-review/b-rereview-20260914/']
if CANDIDATE:
    if CANDIDATE=='3ac597d1d16982e0a5c5a114202ca8568dc28d8f':branch='codex/toph/skl002-pynq-validation-20260914';scope=['skill/pynq-overlay-dma-validation/']
    elif CANDIDATE=='a7e1ea976da91ba735af5c0a79fffdc7d10c121f':branch='codex/toph/skl001-module-verification-20260914';scope=['skill/fpga-module-verification/','task-packages/PKG-A-SKILLS/']
    else:raise ValueError('Unapproved candidate')
    assert parents==[BASE,CANDIDATE]
    assert remote(branch,'candidate-before')==CANDIDATE,'Candidate moved'
    assert not git('diff',CANDIDATE,TARGET,'--',*scope),'Candidate scope was changed in integration'
    allowed+=scope
else:assert parents==[BASE]
changed=git('diff-tree','--no-commit-id','--name-only','-r',BASE,TARGET).decode().splitlines()
assert all(any(p.startswith(a) if a.endswith('/') else p==a for a in allowed) for p in changed),changed
def tree(sha):
    entries={}
    for row in git('ls-tree','-rz',sha).split(b'\0'):
        if not row:continue
        head,path=row.split(b'\t',1);mode,kind,oid=head.decode().split();entries[path.decode()]=(mode,kind,oid)
    return entries
target_tree=tree(TARGET);known=set()
for parent in parents:known.update(v[2] for v in tree(parent).values())
entries=[];wanted=set()
for path in changed:
    if path in target_tree:
        mode,kind,oid=target_tree[path];assert kind=='blob';entries.append(dict(path=path,mode=mode,type=kind,sha=oid))
        if oid not in known:wanted.add(oid)
    else:entries.append(dict(path=path,mode='100644',type='blob',sha=None))
wanted=sorted(wanted)
proc=subprocess.run(['git','-c','safe.directory='+W,'-C',W,'cat-file','--batch'],input=('\n'.join(wanted)+'\n').encode(),capture_output=True,check=True)
pos=0;blobs=[]
for oid in wanted:
    end=proc.stdout.index(b'\n',pos);head=proc.stdout[pos:end].split();assert head[0].decode()==oid and head[1]==b'blob'
    n=int(head[2]);content=proc.stdout[end+1:end+1+n];pos=end+n+2;blobs.append((oid,content))
def send_blob(item):
    oid,content=item;label='blob-'+oid;cache=OUT/(label+'-response.json')
    result=json.loads(cache.read_bytes()) if cache.exists() else api('git/blobs',dict(content=base64.b64encode(content).decode(),encoding='base64'),label)
    assert result['sha']==oid
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(send_blob,blobs))
print('Uploaded and verified new blobs:',len(blobs),flush=True)
tr=api('git/trees',dict(base_tree=git('rev-parse',BASE+'^{tree}').decode().strip(),tree=entries),'tree');assert tr['sha']==fields['tree']
def identity(line):
    m=re.fullmatch(r'(.*?) <(.*?)> (\d+) ([+-]\d{4})',line);assert m
    name,email,stamp,zone=m.groups();sign=1 if zone[0]=='+' else -1
    tz=datetime.timezone(sign*datetime.timedelta(hours=int(zone[1:3]),minutes=int(zone[3:5])))
    return dict(name=name,email=email,date=datetime.datetime.fromtimestamp(int(stamp),tz).isoformat())
c=api('git/commits',dict(message=message,tree=tr['sha'],parents=parents,author=identity(fields['author']),committer=identity(fields['committer'])),'commit');assert c['sha']==TARGET
assert remote('main')==BASE
if CANDIDATE:assert remote(branch)==CANDIDATE
u=api('git/refs/heads/main',dict(sha=TARGET,force=False),'update',method='PATCH');assert u['object']['sha']==TARGET
assert remote('main','main-after')==TARGET
git('update-ref','refs/remotes/origin/main',TARGET,BASE)
print('Published exact main:',TARGET,flush=True)
