"""Seal new repair only; refuses overwriting its manifest."""
import hashlib
import json
from pathlib import Path
root=Path(__file__).resolve().parent.parent
dest=root/'SHA256.json'
if dest.exists(): raise FileExistsError('REFUSE_OVERWRITE')
rows={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
      for p in sorted(root.rglob('*')) if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts}
dest.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
print('REPAIR_MANIFEST',len(rows),hashlib.sha256(dest.read_bytes()).hexdigest())
