"""Verify new exact manifest and all prior evidence via explicit original mapping."""
import hashlib
import json
from pathlib import Path
import sys

ENTRY = Path(__file__).resolve().parents[1]
MANIFEST = ENTRY / 'repair-02/R1-SHA256.json'
MAPPING = {name: 'repair-02/originals/' + name for name in ('command_contract.py', 'README.md')}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_map(root, entries):
    for name, expected in entries.items():
        path = root / name
        if sha(path) != expected:
            raise ValueError('Original bytes changed: ' + str(path))


def main():
    old_path = ENTRY / 'repair-01/REPAIR-SHA256.json'
    if sha(old_path) != 'c13f2f73a2cb9432e3fd26e16be5f772d50e3af310a4c305e679ccdbfe539544':
        raise ValueError('17afe32 manifest itself changed')
    old = json.loads(old_path.read_text())['files']
    verify_map(ENTRY, {MAPPING.get(name, name): digest for name, digest in old.items()})
    original = ENTRY / 'DELIVERY-SHA256.json'
    if sha(original) != '2e27be4ae9677252d8b4b0a46fb52ce587103e1b8ce20c0b7b955e71fd49af93':
        raise ValueError('bbe39c3 original manifest itself changed')
    oldest = json.loads(original.read_text())['files']
    old_changed = {'check_entry.py', 'load_timerfixed.tcl', 'README.md'}
    verify_map(ENTRY, {('repair-01/originals/' + name if name in old_changed else name): digest
                       for name, digest in oldest.items()})
    inputs = ENTRY / 'repair-02/review-inputs'
    provenance = json.loads((inputs / 'PROVENANCE.json').read_text())
    if provenance['feedback_commit'] != 'd1fd9d1db2be7ed292c17faf9dc9d27d407c9009':
        raise ValueError('Wrong B feedback commit')
    verify_map(inputs, provenance['files'])
    current = {p.relative_to(ENTRY).as_posix(): sha(p) for p in sorted(ENTRY.rglob('*'))
               if p.is_file() and p != MANIFEST}
    if sys.argv[1:] == ['--create']:
        with MANIFEST.open('x', encoding='utf-8') as stream:
            json.dump({'base': '17afe32cebcff742bb2f9486388e91d9403f83dd',
                       'feedback': provenance['feedback_commit'], 'original_mapping': MAPPING,
                       'status': 'AUTHOR_R1_REPAIR_TESTED_NOT_B_APPROVED_NOT_BOARD',
                       'files': current}, stream, indent=2)
    elif sys.argv[1:]:
        raise SystemExit('Usage: verify_repair.py [--create once by author]')
    expected = json.loads(MANIFEST.read_text())['files']
    if current != expected:
        raise ValueError('Missing/modified/extra current files')
    print('R1_HASH_PASS current_entries=' + str(len(expected)) +
          ' prior_entries=' + str(len(old)) + ' oldest_entries=' + str(len(oldest)))


if __name__ == '__main__':
    main()
