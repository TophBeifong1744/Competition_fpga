"""Closed new repair manifest; never overwrites a prior manifest."""
import argparse, hashlib, json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');a=p.parse_args()
root=Path(__file__).resolve().parent;dest=root/'SHA256.json'
actual={x.relative_to(root).as_posix():hashlib.sha256(x.read_bytes()).hexdigest() for x in sorted(root.rglob('*')) if x.is_file() and x!=dest and '__pycache__' not in x.parts and '.git' not in x.parts}
if a.verify:
    expected=json.loads(dest.read_bytes())
    assert actual==expected,dict(missing=sorted(expected.keys()-actual.keys()),extra=sorted(actual.keys()-expected.keys()),changed=[n for n in actual.keys()&expected.keys() if actual[n]!=expected[n]])
    print('REPAIR_MANIFEST_PASS',len(actual),hashlib.sha256(dest.read_bytes()).hexdigest())
else:
    with dest.open('x',encoding='utf-8') as f:json.dump(actual,f,indent=2);f.write('\n')
    print('REPAIR_MANIFEST_CREATED',len(actual))
