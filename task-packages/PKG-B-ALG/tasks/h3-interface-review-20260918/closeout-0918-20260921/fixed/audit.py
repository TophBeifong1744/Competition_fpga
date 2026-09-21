"""Read-only fixed-commit evidence audit; no algorithm/FFT/audio execution."""
import argparse
import ast
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np

ROOT = Path('F:/NUEC/review-worktrees/algorithm-closeout-20260923')
WORK = Path('F:/NUEC/validation/b-0918-fixed-contract-work')
SHA = 'fe67547635ff254f9f91c7f917e8dedb6daf3363'
TASKS = 'task-packages/PKG-B-ALG/tasks/'
PARENT = TASKS + 'h3-interface-review-20260918/'
CP = PARENT + 'checkpoint-20260923/'
FIXED = TASKS + 'h3-complete-20260918/'

def git(*args):
    return subprocess.check_output(['git', '-c', 'safe.directory='+ROOT.as_posix(),
                                    '-C', str(ROOT), *args],
                                   env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))

def blob(path):
    return git('cat-file', 'blob', SHA + ':' + path)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def data(path):
    return json.loads(blob(path))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if WORK.resolve() not in out.parents:
        raise ValueError('output must be a new child of the authorized work directory')
    out.mkdir(parents=True, exist_ok=False)
    before = git('status', '--porcelain', '--untracked-files=all').decode()
    assert git('rev-parse', 'HEAD').decode().strip() == SHA
    identities = {}
    errors = []

    def identity(path, expected=None):
        raw = blob(path)
        actual = digest(raw)
        local = ROOT / path
        row = dict(blob_sha256=actual, bytes=len(raw), expected_sha256=expected,
                   expected_match=expected is None or expected == actual,
                   working_sha256=digest(local.read_bytes()) if local.exists() else None)
        row['working_matches_blob'] = row['working_sha256'] == actual
        identities[path] = row
        if not row['expected_match']:
            errors.append('manifest mismatch: ' + path)
        return raw

    dependencies = data(CP + 'dependencies.json')
    for path, expected in dependencies.items():
        identity(path, expected)
    snapshot = data(CP + 'SNAPSHOT-SHA256.json')['files']
    for path, expected in snapshot.items():
        identity(PARENT + path, expected)
    selected = [
        'AGENTS.md', 'docs/phases/2026-09-13-to-10-01/B.md',
        'docs/team-workflow.md', 'docs/templates/review-brief.md',
        CP+'SNAPSHOT-SHA256.json',
        FIXED+'source/fixed_golden.py', FIXED+'source/budget.py',
        FIXED+'tests/test_h3_candidate.py', FIXED+'evidence/run05/golden-check.json',
        'docs/reviews/h3-run05-7a17edd/B-REVIEW.md',
        'docs/reviews/h3-run05-7a17edd/POSTMERGE-SUPPLEMENT.md',
        TASKS+'fft-bitexact-01/README.md',
        TASKS+'phat-fixed-03/closeout-01/a29-coverage-review-01/B-REVIEW.md',
        'docs/reviews/fixed-closeout-6cb76d1/review.md',
    ]
    for path in selected:
        identity(path)
    anchors = {}
    for path in identities:
        if path.endswith('.py'):
            tree = ast.parse(blob(path).decode('utf-8-sig'))
            anchors[path] = [dict(name=n.name, line=n.lineno, end=n.end_lineno)
                             for n in ast.walk(tree)
                             if isinstance(n, (ast.FunctionDef, ast.ClassDef))]

    golden = data(CP+'evidence/golden02/summary.json')
    for name, expected in data(CP+'evidence/golden02/SHA256.json').items():
        identity(CP+'evidence/golden02/'+name, expected)
    arrays = []
    for report in golden['reports']:
        with np.load(io.BytesIO(blob(CP+'evidence/golden02/'+report['capture']+'.npz')), allow_pickle=False) as z:
            assert set(z.files) == set(report['arrays'])
            for key, expected in report['arrays'].items():
                a = z[key]
                ok = (str(a.dtype) == expected['dtype'] and list(a.shape) == expected['shape']
                      and digest(a.tobytes()) == expected['sha256'])
                arrays.append(dict(capture=report['capture'], key=key, match=ok,
                                   dtype=str(a.dtype), shape=list(a.shape)))
                if not ok:
                    errors.append('frozen array mismatch: '+report['capture']+'/'+key)

    # Pure arithmetic only: execute neither imported candidate code nor a transform.
    buffers = dict(pcm_double_frame=32768, hann=4096, doa_half_spectra=16416,
                   gate_half_spectra=16416, pair_phat=4104, pair_ifft=8192,
                   correlation=4096, audio_history=160, mono_double_hop=4096,
                   rx_slots_guards=16128, descriptors_allowance=1024)
    budget = dict(status='DEPENDENCY_ARITHMETIC_ONLY_REALTIME_BLOCKED',
                  forward_per_frame=8, inverse_max_per_frame=6,
                  radix2_butterflies_per_transform=1024//2*10,
                  radix2_butterflies_all_transforms=14*(1024//2*10),
                  historical_slot_sum_cycles=8*7366+6*7406,
                  hop_cycles_100mhz=100000000*512//48000,
                  historical_difference_not_margin=100000000*512//48000-(8*7366+6*7406),
                  buffers_bytes= buffers, listed_bytes=sum(buffers.values()),
                  total_wcet_cycles=None, actual_resources=None,
                  actual_memory_bytes=None, end_to_end_latency_cycles=None,
                  stall_upper_bound_cycles=None)
    assert budget['historical_slot_sum_cycles'] == 103364
    assert budget['listed_bytes'] == 107496
    after = git('status', '--porcelain', '--untracked-files=all').decode()
    if before != after or git('rev-parse', 'HEAD').decode().strip() != SHA:
        errors.append('source identity/status changed during audit')
    mismatches = [p for p,r in identities.items() if not r['working_matches_blob']]
    result = dict(status='PASS_READ_ONLY_IDENTITY_AND_ARITHMETIC' if not errors else 'FAIL',
                  source_root=str(ROOT), commit=SHA,
                  checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  python=sys.version, numpy=np.__version__,
                  dependency_count=len(dependencies), snapshot_entries=len(snapshot),
                  unique_identity_files=len(identities), frozen_arrays=len(arrays),
                  working_blob_mismatches=mismatches, errors=errors,
                  source_status_before=before, source_status_after=after,
                  algorithms_executed=False, old_tests_rerun=False,
                  note='Frozen array identity is not independent arithmetic regeneration or approval.')
    for name, value in [('source-identities.json',identities), ('code-anchors.json',anchors),
                        ('frozen-array-checks.json',arrays), ('budget.json',budget), ('result.json',result)]:
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return bool(errors)

if __name__ == '__main__':
    sys.exit(main())
