"""Create once, or verify, the incremental delivery file hashes."""
import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parent
manifest = root / 'PREPARATION-SHA256.json'
def hashes():
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file() and p != manifest}

if sys.argv[1:] == ['--create']:
    with manifest.open('x', encoding='utf-8') as stream:
        json.dump({'scope': 'increment only; manifest itself excluded',
                   'status': 'PREPARED_HOST_TESTED_NOT_INSTALLED_NOT_ARM_NOT_BOARD',
                   'files': hashes()}, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
elif sys.argv[1:]:
    raise SystemExit('Usage: preparation_manifest.py [--create]')
expected = json.loads(manifest.read_text(encoding='utf-8'))['files']
if hashes() != expected:
    raise SystemExit('HASH_CHECK_FAILED: missing, changed, or added file')
print('HASH_CHECK_PASS files=' + str(len(expected)))
