"""Write/verify SHA-256 for this independent package, never edit payload files."""
import argparse
import hashlib
import json
from pathlib import Path


def files(root):
    return {p.relative_to(root).as_posix():p for p in sorted(root.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and p.name != 'SHA256SUMS.json'}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('mode',choices=['write','check'])
    ap.add_argument('--package',type=Path,default=Path(__file__).resolve().parent.parent)
    a=ap.parse_args()
    payload=files(a.package)
    actual={n:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
            for n,p in payload.items()}
    target=a.package/'SHA256SUMS.json'
    if a.mode=='write':
        if target.exists():
            raise SystemExit('Refusing to overwrite existing final manifest')
        target.write_text(json.dumps(actual,indent=2)+'\n',encoding='utf-8')
    else:
        expected=json.loads(target.read_bytes())
        assert actual==expected, {'missing':sorted(set(expected)-set(actual)),
                                  'extra':sorted(set(actual)-set(expected)),
                                  'changed':[n for n in actual.keys()&expected.keys() if actual[n]!=expected[n]]}
    print(f'PASS SHA256 {a.mode}: {len(actual)} files, {sum(r["bytes"] for r in actual.values())} bytes')


if __name__=='__main__':
    main()
