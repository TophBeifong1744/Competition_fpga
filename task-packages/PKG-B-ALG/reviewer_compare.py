"""Compare independent full rerun, separating byte identity and numeric agreement."""
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import numpy as np

root = Path(sys.argv[1]).resolve()
a = root / 'evidence/robustness-run-01'
b = root / 'evidence/reviewer-robustness-run'
old = json.loads((a/'run.json').read_text())
new = json.loads((b/'run.json').read_text())
assert old['source_sha256'] == new['source_sha256']
assert old['plan_sha256'] == new['plan_sha256']
m = json.loads((root/'evidence/package-files.json').read_text())
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest() == h for n,h in m['files'].items())
different = [n for n,h in old['artifact_sha256'].items() if new['artifact_sha256'].get(n) != h]
rir_max = 0.0
for name in old['artifact_sha256']:
    if name.endswith('.npy'):
        x,y = np.load(a/name),np.load(b/name)
        assert x.shape == y.shape
        rir_max = max(rir_max,float(np.max(np.abs(x-y))))
        np.testing.assert_allclose(x,y,atol=1e-12,rtol=1e-12)
maxima = {}
counts = {}
for name in ['frames.csv','comparisons.csv','per-seed.csv','pooled.csv','paired.csv','latencies.csv']:
    with (a/name).open(newline='',encoding='utf-8') as f, (b/name).open(newline='',encoding='utf-8') as g:
        x,y = csv.DictReader(f),csv.DictReader(g)
        assert x.fieldnames == y.fieldnames
        count = 0
        for r in x:
            s=next(y);count+=1
            for k,v in r.items():
                if v == s[k]:continue
                try: v1,v2=float(v),float(s[k])
                except ValueError:raise AssertionError((name,count,k,v,s[k]))
                assert math.isclose(v1,v2,abs_tol=1e-8,rel_tol=1e-10),(name,count,k,v1,v2)
                maxima[k] = max(maxima.get(k,0),abs(v1-v2))
        assert next(y,None) is None
        counts[name]=count
result = dict(status='PASS_NUMERIC_NOT_BYTE_IDENTICAL',reviewed_commit='b3989e101babfe1bb96a717aa396ee4d231dcd79',
              package_files_checked=len(m['files']),trials=new['trials'],method_rows=new['method_rows'],
              artifact_count=len(old['artifact_sha256']),byte_identical_count=len(old['artifact_sha256'])-len(different),
              byte_differences=different,rir_max_abs_difference=rir_max,csv_row_counts=counts,
              csv_max_abs_difference_by_column=maxima,
              csv_tolerance=dict(atol=1e-8,rtol=1e-10),rir_tolerance=dict(atol=1e-12,rtol=1e-12),
              python=new['python'],numpy=new['numpy'],
              source_hashes_match=True,plan_hash_matches=True,
              interpretation='Counts, accept/reject, states, flags, paired deltas and latencies identical. RIR and numeric estimates differ at floating roundoff scale; exact source is not established. Input content hashes consequently differ. No byte-identical claim.',
              rerun_artifact_sha256=new['artifact_sha256'])
out=root/'evidence/reviewer-reproduction.json'
if out.exists():raise RuntimeError('Refuse overwrite')
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k != 'rerun_artifact_sha256'},indent=2))
