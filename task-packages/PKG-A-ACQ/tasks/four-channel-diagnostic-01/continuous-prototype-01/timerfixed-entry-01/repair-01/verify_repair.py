"""New manifest plus original-evidence mapping; never rewrites old evidence."""
import hashlib
import json
from pathlib import Path
import sys
entry=Path(__file__).resolve().parents[1]
manifest=entry/'repair-01/REPAIR-SHA256.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def current():
    return {p.relative_to(entry).as_posix():sha(p) for p in sorted(entry.rglob('*'))
            if p.is_file() and p!=manifest}
old=json.loads((entry/'DELIVERY-SHA256.json').read_text())['files']
changed={'check_entry.py','load_timerfixed.tcl','README.md'}
for name,digest in old.items():
    p=entry/('repair-01/originals/'+name if name in changed else name)
    assert sha(p)==digest, 'Original evidence changed: '+name
if sys.argv[1:]==['--create']:
    with manifest.open('x',encoding='utf-8') as f:
        json.dump(dict(base='bbe39c38dc36ccb4c0492f492b86f6c46d885fbe',
            feedback='53018f9256cd209136183679d28b8949b04536f2',
            old_file_mapping={name:'repair-01/originals/'+name for name in sorted(changed)},
            status='AUTHOR_REPAIR_TESTED_NOT_B_APPROVED_NOT_BOARD',
            files=current()),f,indent=2)
elif sys.argv[1:]:
    raise SystemExit('Usage: verify_repair.py [--create]')
expected=json.loads(manifest.read_text())['files']
assert current()==expected, 'Missing/modified/extra repair files'
print('REPAIR_HASH_PASS original_entries='+str(len(old))+' current_entries='+str(len(expected)))
