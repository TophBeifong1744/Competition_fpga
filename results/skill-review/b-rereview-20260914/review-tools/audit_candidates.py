import hashlib,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).parent
def git(w,*args):return subprocess.check_output(['git','-C',str(w),*args])
out=[]
for ident,sha,old,manifest,prefix in [
 ('001','a7e1ea976da91ba735af5c0a79fffdc7d10c121f','c562466805aff08201cd457cc2e6ee7464a3566f','task-packages/PKG-A-SKILLS/repair-manifest.json',''),
 ('002','3ac597d1d16982e0a5c5a114202ca8568dc28d8f','55039cf8bfab2bd6112192c8bd646d427a52a642','skill/pynq-overlay-dma-validation/repair-manifest.json','skill/pynq-overlay-dma-validation/')]:
    w=pathlib.Path('F:/NUEC/review-worktrees')/('b-skl'+ident+'-'+sha[:7]);assert git(w,'rev-parse','HEAD').decode().strip()==sha
    m=json.loads(git(w,'show',sha+':'+manifest));specs=[sha+':'+prefix+f['path'] for f in m['files']]
    raw=git(w,'cat-file','--batch') if False else subprocess.run(['git','-C',str(w),'cat-file','--batch'],input=('\n'.join(specs)+'\n').encode(),capture_output=True,check=True).stdout
    pos=0;items=[]
    for f,spec in zip(m['files'],specs):
        e=raw.index(b'\n',pos);header=raw[pos:e].split();assert header[1]==b'blob',header
        size=int(header[2]);data=raw[e+1:e+1+size];pos=e+size+2
        h=hashlib.sha256(data).hexdigest();local=(w/(prefix+f['path'])).read_bytes()
        items.append(dict(path=prefix+f['path'],bytes=size,sha256=h,git_blob=header[0].decode(),matches_manifest=h==f['sha256'] and size==f['bytes'],worktree_exact=local==data))
    diff=git(w,'diff','--name-only',old,sha).decode().splitlines()
    allowed=['skill/fpga-module-verification/','task-packages/PKG-A-SKILLS/'] if ident=='001' else [prefix]
    o=dict(skill=ident,sha=sha,old_sha=old,manifest=manifest,files=items,changed_paths=diff,outside_scope=[p for p in diff if not any(p.startswith(a) for a in allowed)])
    if ident=='002':o['license_exact']=git(w,'show',sha+':LICENSE')==git(w,'show',sha+':'+prefix+'LICENSE.txt')
    out.append(o)
(ROOT/'candidate-audit.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps([dict(skill=o['skill'],files=len(o['files']),bad=[x for x in o['files'] if not x['matches_manifest'] or not x['worktree_exact']],outside_scope=o['outside_scope'],license_exact=o.get('license_exact')) for o in out],indent=2))
assert all(all(x['matches_manifest'] and x['worktree_exact'] for x in o['files']) and not o['outside_scope'] and o.get('license_exact',True) for o in out)
