"""Read-only publication identity checks; recording mode for W's initial manifest only."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

BASE = Path(__file__).resolve().parent
REL = 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/'
PIN = 'f08556d01821d6c3c8204fdac2c38f53b2107c05'
ORIGINAL = BASE / 'evidence/e-dispatch-20260921-run01'
RERUN = BASE / 'evidence/w-preparation-20260921-run01'
MANIFEST = RERUN / 'publication-check.json'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check(rerun):
    original_result = json.loads((ORIGINAL / 'result.json').read_bytes())
    assert digest(BASE / 'prepare_production_delta.py') == original_result['source_sha256']
    raw = subprocess.check_output(['git', 'show', PIN + ':' + REL + 'service-budget-20260921.json'])
    assert raw == (ORIGINAL / 'pinned-service-budget.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == original_result['input_sha256']
    for name in ('fixed4-prepared-vectors.json', 'pinned-service-budget.json', 'result.json'):
        assert (ORIGINAL / name).read_bytes() == (rerun / name).read_bytes(), name
    assert original_result['vector_count'] == 145
    assert original_result['actual_bounds_known'] == 0
    assert original_result['status'] == 'PREPARATION_ONLY_NOT_RTL_NOT_BOARD'
    assert original_result['realtime'] == 'REALTIME_BLOCKED'
    for key in ('RTL', 'AMD', 'ARM', 'board'):
        assert original_result[key] == 'NOT_RUN'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rerun', type=Path, default=RERUN)
    parser.add_argument('--record', action='store_true')
    args = parser.parse_args()
    check(args.rerun)
    if args.record:
        paths = [BASE / name for name in ('.gitattributes', 'E-CONTINUE-20260921.md',
                 'prepare_production_delta.py', 'PUBLICATION-PREPARATION-20260921.md',
                 'verify_preparation_publication.py')]
        paths += sorted(ORIGINAL.glob('*.json'))
        paths += sorted(p for p in RERUN.glob('*.json') if p != MANIFEST)
        entries = {p.relative_to(BASE).as_posix(): {'sha256': digest(p), 'bytes': p.stat().st_size}
                   for p in paths}
        with MANIFEST.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump({'status': 'W_COMPLETENESS_NOT_B_APPROVAL', 'pin': PIN,
                       'files': entries, 'file_count': len(entries)}, stream, indent=2)
            stream.write('\n')
    data = json.loads(MANIFEST.read_bytes())
    assert data['file_count'] == len(data['files'])
    for name, record in data['files'].items():
        path = BASE / name
        assert digest(path) == record['sha256'], name
        assert path.stat().st_size == record['bytes'], name
    print('W_COMPLETENESS_NOT_B_APPROVAL files=', data['file_count'], 'vectors=145 services=16')

if __name__ == '__main__':
    main()
