"""Collect A's existing run without regenerating or changing frozen evidence."""
import hashlib
import json
from pathlib import Path
import sys

run, exact = map(Path, sys.argv[1:3])
out = Path(__file__).parent / 'evidence'
out.mkdir(exist_ok=False)
mapping = {str(run): '<OUT>', str(exact): '<EXACT>'}
commands = json.loads((run / 'commands.json').read_text())
mapping[commands[0]['argv'][0]] = '<PY312>'
records = {}
for name in ['json-comparison.json', 'result.json', 'commands.json',
             'repair-tests-stderr.txt', 'repair-tests-stdout.txt',
             'tests-stderr.txt', 'tests-stdout.txt',
             'study-stdout.txt', 'study-stderr.txt',
             'golden-stdout.txt', 'golden-stderr.txt']:
    raw = (run / name).read_bytes()
    text = raw.decode('utf-8')
    for value, alias in mapping.items():
        text = text.replace(json.dumps(value)[1:-1], alias).replace(value, alias)
    public = text.encode('utf-8')
    (out / name).write_bytes(public)
    records[name] = {'original_sha256': hashlib.sha256(raw).hexdigest(),
                     'public_sha256': hashlib.sha256(public).hexdigest(),
                     'path_redacted': raw != public}
raw = (exact / 'EXACT-EXPORT.json').read_bytes()
(out / 'EXACT-EXPORT.json').write_bytes(raw)
records['EXACT-EXPORT.json'] = {'sha256': hashlib.sha256(raw).hexdigest()}
(out / 'PROVENANCE.json').write_text(json.dumps(records, indent=2)+'\n', encoding='utf-8')
print('COLLECTED', len(records), 'original files retained')
