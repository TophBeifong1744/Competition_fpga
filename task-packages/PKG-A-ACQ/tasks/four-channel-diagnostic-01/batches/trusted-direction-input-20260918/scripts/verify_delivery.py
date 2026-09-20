"""Read-only payload/hash checks and H1 reader replay; new output directory only."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    repo = next(p for p in root.parents if (p / 'docs/team-workflow.md').is_file())
    manifest = json.loads((root / 'evidence/background-confirmation-20260920-01/CURRENT-DATA-SHA256.json').read_text(encoding='utf-8'))
    bad = []
    captures = []
    for rel, expected in manifest.items():
        path = root / rel
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest().lower() != expected.lower():
            bad.append(rel)
        if path.name == 'metadata.json':
            captures.append(path.parent)
    assert not bad, bad
    assert len(captures) == 8
    assert all('received-20260920-01' not in str(p) for p in captures)
    rows = []
    for index, capture in enumerate(sorted(captures)):
        command = [sys.executable, '-B', str(repo / 'task-packages/PKG-B-ALG/payload/model/python/h1_reader.py'), str(capture)]
        result = subprocess.run(command, capture_output=True)
        (args.out / f'{index}-stdout.txt').write_bytes(result.stdout)
        (args.out / f'{index}-stderr.txt').write_bytes(result.stderr)
        ok = result.returncode == 0 and b'PASS_FORMAT_ONLY' in result.stdout
        rows.append(dict(capture=capture.relative_to(root).as_posix(), command=command, returncode=result.returncode, format_pass=ok))
    summary = dict(manifest_files=len(manifest), hash_mismatches=bad, captures=rows,
                   status='PASS_PUBLICATION_FORMAT_ONLY' if all(r['format_pass'] for r in rows) else 'FAIL',
                   limitations='Not independent B review, calibrated direction/activity truth, audio gain or H3 acceptance')
    (args.out / 'result.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(summary['status'], len(manifest), len(rows))
    return 0 if summary['status'].startswith('PASS') else 1

if __name__ == '__main__':
    raise SystemExit(main())
