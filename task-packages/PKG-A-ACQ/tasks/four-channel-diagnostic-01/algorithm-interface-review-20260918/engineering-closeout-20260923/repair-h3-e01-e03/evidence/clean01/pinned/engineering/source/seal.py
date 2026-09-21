"""Create once / verify an exact local delivery manifest; no Git mutations."""
import argparse
import hashlib
import json
from pathlib import Path

root=Path(__file__).resolve().parent.parent
excluded={'PACKAGE-SHA256.json','MANIFEST.sha256'}


def inventory():
    return {p.relative_to(root).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
            for p in sorted(root.rglob('*')) if p.is_file() and p.relative_to(root).as_posix() not in excluded}


ap=argparse.ArgumentParser();ap.add_argument('--verify',action='store_true');args=ap.parse_args()
target=root/'PACKAGE-SHA256.json'
if args.verify:
    saved=json.loads(target.read_text(encoding='utf-8'))
    if saved['files']!=inventory():raise SystemExit('MANIFEST_MISMATCH')
    actual=hashlib.sha256(target.read_bytes()).hexdigest()
    if (root/'MANIFEST.sha256').read_text().split()[0]!=actual:raise SystemExit('MANIFEST_DIGEST_MISMATCH')
    print('PACKAGE_VERIFY_PASS',len(saved['files']),actual)
else:
    if target.exists() or (root/'MANIFEST.sha256').exists():raise SystemExit('REFUSE_OVERWRITE')
    data=dict(scope='engineering-closeout-20260923 only; author self-check, not approval',files=inventory())
    target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    digest=hashlib.sha256(target.read_bytes()).hexdigest()
    (root/'MANIFEST.sha256').write_text(digest+'  PACKAGE-SHA256.json\n',encoding='ascii')
    print('PACKAGE_SEALED',len(data['files']),digest)
