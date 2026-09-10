"""Seal once; verify bytes without modifying the package. Stdlib only."""
import argparse
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest = root / 'SHA256.json'
parser = argparse.ArgumentParser()
parser.add_argument('command', choices=['seal', 'verify'])
args = parser.parse_args()
if args.command == 'seal':
    if manifest.exists():
        raise ValueError('Refuse to replace existing manifest')
    entries = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
    manifest.write_text(json.dumps(entries, indent=2) + '\n', encoding='utf-8')
else:
    entries = json.loads(manifest.read_text(encoding='utf-8'))
    for name, expected in entries.items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('SHA mismatch: ' + name)
print(f'SHA256_PASS {len(entries)} files; manifest itself excluded; extra files not authenticated')
