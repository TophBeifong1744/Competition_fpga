"""Publish B scripts/results separately from frozen E1 and reusable input copies."""
import hashlib,json,shutil
from pathlib import Path
src=Path(__file__).resolve().parent
dst=Path('F:/NUEC/review-worktrees/endurance-main-5606e1a/docs/reviews/endurance-5606e1a')
dst.mkdir(parents=True,exist_ok=False)
selected=[]
for p in src.rglob('*'):
    if not p.is_file():continue
    rel=p.relative_to(src)
    if 'historical-dependencies' in rel.parts or p.suffix.lower() in ('.exe','.bit','.xsa','.elf','.obj'):
        continue
    selected.append(p)
inventory={p.relative_to(src).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),published=p in selected)
           for p in sorted(src.rglob('*')) if p.is_file()}
(src/'LOCAL-MATERIALS.json').write_bytes((json.dumps(dict(root=str(src),files=inventory,
    recovery='Historical dependencies are extracted from fixed bbe39c38 Git objects. Host executables rebuild using recorded argv. Full B evidence will have one external verified ZIP before cleanup.'),indent=2)+'\n').encode())
selected.append(src/'LOCAL-MATERIALS.json')
for p in selected:
    q=dst/p.relative_to(src);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
    assert p.read_bytes()==q.read_bytes()
(dst/'.gitattributes').write_bytes(b'* -text\n')
manifest={p.relative_to(dst).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(dst.rglob('*')) if p.is_file()}
(dst/'B-EVIDENCE-SHA256.json').write_bytes((json.dumps(dict(scope='B fixed review scripts/results listed here; later BATCH-CLOSEOUT/state receipts are explicitly separate',review_sha='5606e1a9d9a6183ceff7cffc1bb4f8aac44bb79c',files=manifest),indent=2)+'\n').encode())
print('Published B evidence files',len(manifest)+1)
