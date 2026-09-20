"""Validate new closed snapshot, untouched historical mapping, and dependencies."""
from common import ROOT,HERE,load,sha

def verify():
    package=HERE.parent
    manifest=HERE/'SNAPSHOT-SHA256.json'
    expected=load(manifest)['files']
    actual={p.relative_to(package).as_posix():sha(p) for p in sorted(package.rglob('*')) if p.is_file() and p!=manifest}
    if actual!=expected:raise ValueError('current closed snapshot changed/missing/extra')
    original=load(package/'PACKAGE-SHA256.json')['files']
    if any(sha(package/p)!=v for p,v in original.items()):raise ValueError('original 28d5c77 snapshot changed')
    deps=load(HERE/'dependencies.json')
    if any(sha(ROOT/p)!=v for p,v in deps.items()):raise ValueError('dependency changed')
    return dict(current_files=len(actual),historical_files=len(original)+1,dependencies=len(deps))

if __name__=='__main__':print(verify())
