"""Verify archived evidence against fixed Git objects without repeating diagnosis."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / '.git').exists())


def git(*args):
    return subprocess.check_output(
        ['git', '-c', f'safe.directory={ROOT.as_posix()}', '-C', str(ROOT), *args]
    )


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(ok, message):
    if not ok:
        raise SystemExit(message)


record = json.loads((HERE / 'REGISTER.json').read_text(encoding='utf-8'))
for name, expected in record['historical_files'].items():
    require(sha((HERE / 'historical-evidence' / name).read_bytes()) == expected, name)
historical = json.loads((HERE / 'historical-evidence/08-independent.json').read_text())
require(historical['review_sha'] == record['source_commit'], 'source commit mismatch')
entries = historical['git_blob_checks']
require(len(entries) == 76, 'expected 76 original publication blobs')
for entry in entries:
    spec = record['source_commit'] + ':' + entry['path']
    raw = git('show', spec)
    require(sha(raw) == entry['sha256'], spec)
    require(git('rev-parse', spec).decode().strip() == entry['git_blob'], spec)
    # The receipt-only update must preserve every originally reviewed file.
    require(git('rev-parse', record['receipt_commit'] + ':' + entry['path']).decode().strip()
            == entry['git_blob'], 'receipt update altered ' + entry['path'])
spec = record['receipt_commit'] + ':' + record['receipt_path']
require(sha(git('show', spec)) == record['receipt_sha256'], spec)
require(git('rev-parse', spec).decode().strip() == record['receipt_git_blob'], spec)
require(record['input_files'] == [e for e in entries if '/captures/' in e['path']],
        'capture identity index mismatch')
require(record['payload_manifest_sha256'] == historical['manifest_sha256'], 'manifest index mismatch')
compile((HERE / 'replay_independent.py').read_text(encoding='utf-8'), 'replay_independent.py', 'exec')
print('PASS: 10 historical evidence hashes; 76 original Git blobs; 76 unchanged receipt-update blobs; receipt identity; capture index; replay syntax')
print('No numerical diagnosis or 64-test historical regression rerun; no hardware acceptance.')
