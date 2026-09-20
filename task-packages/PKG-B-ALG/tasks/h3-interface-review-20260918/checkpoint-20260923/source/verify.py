"""Validate new closed snapshot, untouched historical mapping, and dependencies."""
from common import ROOT,HERE,load,sha

def check_mapping(root, expected, label, exact_set=False):
    failures=[]
    for name,want in expected.items():
        p=root/name
        got=sha(p) if p.is_file() else 'MISSING'
        if got!=want: failures.append(f'{name}: expected SHA256={want}; actual SHA256={got}')
    if failures:
        raise ValueError(label+' byte mismatch:\n'+'\n'.join(failures)+
            '\nUse source/prepare_exact.py --commit <review SHA> --out <NEW external directory>; '
            'do not normalize files or change manifests. A mismatch alone does not prove CRLF conversion.')

def verify():
    package=HERE.parent
    manifest=HERE/'SNAPSHOT-SHA256.json'
    expected=load(manifest)['files']
    actual={p.relative_to(package).as_posix():sha(p) for p in sorted(package.rglob('*')) if p.is_file() and p!=manifest}
    check_mapping(package,expected,'current closed snapshot')
    if actual.keys()!=expected.keys():raise ValueError('snapshot extra paths: '+str(sorted(actual.keys()-expected.keys())))
    original=load(package/'PACKAGE-SHA256.json')['files']
    check_mapping(package,original,'original 28d5c77 snapshot')
    deps=load(HERE/'dependencies.json')
    check_mapping(ROOT,deps,'dependency')
    return dict(current_files=len(actual),historical_files=len(original)+1,dependencies=len(deps))

if __name__=='__main__':print(verify())
