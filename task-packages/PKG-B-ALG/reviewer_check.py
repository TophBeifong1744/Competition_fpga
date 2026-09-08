"""A-side focused review: recompute key claims directly from frame records."""
import csv
import json
from collections import defaultdict, Counter
from pathlib import Path
import hashlib
import sys
import numpy as np

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
import audit_robustness

audit = audit_robustness.audit()
run = root / 'evidence/robustness-run-01'
groups = defaultdict(list)
totals = defaultdict(Counter)
events = defaultdict(dict)
with (run / 'frames.csv').open(newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        method = r['method']
        fresh = r['fresh_valid'] == 'True'
        stale = r['stale'] == 'True'
        assert not (fresh and stale)
        if r['scope'] == 'target_absent':
            totals[method]['absent'] += 1
            totals[method]['false'] += fresh
            totals[method]['hold'] += stale
        if r['scope'] == 'target_active':
            good = fresh and float(r['error_deg']) <= 10
            groups[r['condition'], method].append(good)
            if r['target_allowed'] == 'False':
                totals[method]['outside_fresh'] += fresh
            if good:
                key = (r['condition'], r['seed'], r['episode'])
                events[key].setdefault(method, float(r['timestamp_ms']))
deltas = {}
for condition, method in groups:
    if method != 'original_quorum' or '__outside__' in condition:
        continue
    a = groups[condition, method]
    b = groups[condition, 'gcc_beta075_quorum']
    assert len(a) == len(b)
    deltas[condition] = (sum(b) - sum(a)) / len(a)
tonal = {k: v for k, v in deltas.items() if k.startswith('tonal__')}
assert len(tonal) == 9 and all(v < 0 for v in tonal.values())
assert sum(v < -0.02 for v in tonal.values()) == 4
assert totals['original_raw']['false'] == 8
assert totals['gcc_beta075_raw']['false'] == 16
for method in ('original_quorum', 'gcc_beta075_quorum'):
    assert totals[method]['false'] == totals[method]['outside_fresh'] == 0
    assert totals[method]['absent'] == 20244
assert totals['original_quorum']['hold'] == 2110
assert totals['gcc_beta075_quorum']['hold'] == 2168
paired = [(key, x['gcc_beta075_quorum'] - x['original_quorum'])
          for key, x in events.items()
          if 'original_quorum' in x and 'gcc_beta075_quorum' in x
          and '__outside__' not in key[0]]
worst = max(paired, key=lambda x: x[1])
assert abs(worst[1] - 736) < 1e-8
assert worst[0][0] == 'band__el_edge__early_late'
report = dict(status='PASS', reviewed_commit='b3989e101babfe1bb96a717aa396ee4d231dcd79',
              author_audit_rerun=audit, tonal_correct_rate_deltas=tonal,
              totals={k: dict(v) for k, v in totals.items()},
              largest_paired_slowdown=dict(event=worst[0], milliseconds=worst[1]),
              scope='Independent frame-level claim checks, not real-room/hardware/H3 acceptance')
out = root / 'evidence/reviewer-focused-check.json'
if out.exists():
    raise RuntimeError('Refuse overwrite')
out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
