"""Verify preserved evidence then run selected arithmetic nodes; no full transforms."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    root = Path(__file__).resolve().parent
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    results = []
    for group, script in [('b1b3', 'verify_gate.py'), ('b2b4', 'verify_nodes.py'), ('b5b6', 'verify_nodes.py')]:
        folder = root / group
        for name, expected in json.loads((folder / 'WORK-SHA256.json').read_text(encoding='utf-8')).items():
            actual = hashlib.sha256((folder / name).read_bytes()).hexdigest()
            if actual != expected:
                raise RuntimeError(f'Historical bytes mismatch: {group}/{name}: expected {expected}, got {actual}; use raw-byte checkout, do not rewrite evidence')
        command = [sys.executable, '-B', str(folder / script), '--repo', str(a.repo.resolve()), '--out', str(out / group)]
        with (out / f'{group}.log').open('wb') as log:
            run = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        results.append({'group': group, 'command': command, 'returncode': run.returncode})
    (out / 'runner.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps(results, indent=2))
    return int(any(item['returncode'] for item in results))


if __name__ == '__main__':
    sys.exit(main())
