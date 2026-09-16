"""Capture exact B feedback Git blobs once; no changes to B's branch or files."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

SHA = 'd1fd9d1db2be7ed292c17faf9dc9d27d407c9009'
PREFIX = 'docs/reviews/timerfixed-repair-17afe32/'
OUT = Path(__file__).resolve().parent / 'review-inputs'
OUT.mkdir(exist_ok=False)
files = {}
for name in ('B-REVIEW.md', 'spec/REVIEW.md', 'spec/check_arguments.py', 'spec/extra_link_flags.py',
             'spec/run01/result.json', 'spec/extra01/result.json'):
    raw = subprocess.check_output(['git', '-c', 'core.longpaths=true', '-C', sys.argv[1],
                                   'cat-file', 'blob', SHA + ':' + PREFIX + name])
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(raw)
    files[name] = hashlib.sha256(raw).hexdigest()
with (OUT / 'PROVENANCE.json').open('x', encoding='utf-8') as stream:
    json.dump({'feedback_commit': SHA, 'prefix': PREFIX, 'files': files}, stream, indent=2)
print('B_RAW_BLOBS_CAPTURED', len(files), SHA)
