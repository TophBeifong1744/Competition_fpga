"""Incremental delivery check; retain run05 bytes and old evidence identities."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

BASE = 'dbd7ab5b35c75dfe9779a0452643d4bd2df24657'
PACKAGE = 'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/engineering-closeout-20260921'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(repo, run):
    manifest = json.loads((run/'OUTPUT-SHA256.json').read_text())
    for rel, expected in manifest.items():
        assert sha(run/rel) == expected, rel
    metadata = json.loads((run/'runner.json').read_text())
    assert metadata['exit_code'] == 0
    for rel, expected in metadata['source_sha256'].items():
        assert sha(repo/rel) == expected, rel
    assert sha(repo/PACKAGE/'repair-r1-r2/A-REVIEW-original.md') == '13fab2584b5e16ac9c367a207871723f204f8280d8d142d4e89b13160b25dbd8'
    # Git's blob hash permits one batch tree query instead of one Git process
    # per frozen file. No line-ending normalization or old manifest rewriting.
    entries = subprocess.check_output(['git', 'ls-tree', '-r', BASE, '--', PACKAGE], cwd=repo, text=True).splitlines()
    mutable = {'README.md', 'FLOW.md', 'CONTRACT.md', 'DELIVERY.md', 'A-REVIEW-PROMPT.md', 'trace_scoreboard.py'}
    preserved = 0
    for line in entries:
        header, rel = line.split('\t', 1)
        short = rel[len(PACKAGE)+1:]
        if short in mutable:
            continue
        data = (repo/rel).read_bytes()
        blob = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        assert blob == header.split()[2], rel
        preserved += 1
    result = json.loads((run/'checks/result.json').read_text())
    assert result['status'] == 'AUTHOR_R1_R2_PASS' and not result['unexpected']
    assert result['source_sha256'] == sha(repo/PACKAGE/'trace_scoreboard.py')
    return dict(status='REPAIR_DELIVERY_PASS', preserved_baseline_files=preserved,
                checked_outputs=len(manifest), source_bindings=len(metadata['source_sha256']),
                cases=result['cases'], numeric_evidence='REUSED_NOT_RERUN', original_report='EXACT_BYTES')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    result = verify(a.repo.resolve(), a.run.resolve())
    with a.out.open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps(result))
