"""Explicit scope inventory; never includes unrelated task materials."""
import hashlib,json,sys
from pathlib import Path
root=Path(__file__).resolve().parent
dest=root/'E-PREPARATION-SHA256.json'
names=['E-CONTINUE-20260921.md','E-HANDOFF-20260921.md','prepare_production_delta.py','audit_scene_dependency_20260921.py','seal_e_preparation.py']
paths=[root/n for n in names]
for folder in ('e-dispatch-20260921-run01','scene-dependency-20260921-01','scene-dependency-20260921-02'):
    paths.extend(p for p in (root/'evidence'/folder).rglob('*') if p.is_file())
rows={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
if '--verify' in sys.argv:
    assert rows==json.loads(dest.read_text()),'MANIFEST_MISMATCH'
    print('PREPARATION_MANIFEST_VERIFIED',len(rows))
else:
    if dest.exists():raise FileExistsError('REFUSE_OVERWRITE')
    dest.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    print('PREPARATION_MANIFEST_CREATED',len(rows))
print(hashlib.sha256(dest.read_bytes()).hexdigest())
