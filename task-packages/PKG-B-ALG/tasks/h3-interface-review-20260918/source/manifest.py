"""Verify exact package file set; --create is author-only explicit sealing."""
import argparse
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'PACKAGE-SHA256.json'
def entries():
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(ROOT.rglob('*')) if p.is_file() and p!=MANIFEST}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--create',action='store_true');a=ap.parse_args()
    actual=entries()
    if a.create:
        if MANIFEST.exists():raise FileExistsError('retain old seal before resealing')
        MANIFEST.write_text(json.dumps({'scope':'B handoff candidate, no A approval','files':actual},indent=2)+'\n')
    assert json.loads(MANIFEST.read_text())['files']==actual,'Missing/extra/modified package file'
    print('PACKAGE_PASS',len(actual))
