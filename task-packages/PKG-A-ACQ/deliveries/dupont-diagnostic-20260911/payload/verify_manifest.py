"""Check every declared payload hash; report extras (e.g. later review outputs)."""
import hashlib
import json
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
entries = json.loads((root/'MANIFEST.sha256.json').read_text(encoding='utf-8'))
for name,expected in entries.items():
    path = (root/name).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Manifest escapes package root')
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError(f'SHA mismatch: {name}')
print('PASS_MANIFEST',len(entries),'files; additional files are not certified')
