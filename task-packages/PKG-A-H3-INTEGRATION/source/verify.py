"""Portable offline verification; never opens Vivado or touches a board."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from calculate_budget import calculate

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
a.out.mkdir(parents=True,exist_ok=False)
index=json.loads((ROOT/'evidence/source-index.json').read_text(encoding='utf-8'))
for item in index['entries']:
    path=ROOT/item['file']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
        raise ValueError('Source SHA mismatch: '+item['file'])
expected=json.loads((ROOT/'evidence/calculations.json').read_text(encoding='utf-8'))
actual=calculate()
if actual!=expected: raise ValueError('Budget numeric/semantic mismatch')
encoded=(json.dumps(actual,indent=2)+'\n').encode()
(a.out/'calculations.json').write_bytes(encoded)
tests=subprocess.run([sys.executable,'-B',str(ROOT/'source/test_budget.py')],capture_output=True,text=True)
(a.out/'tests.txt').write_text(tests.stdout+tests.stderr,encoding='utf-8')
if tests.returncode: raise RuntimeError('Tests failed')
fft=subprocess.run([sys.executable,'-B',str(ROOT/'references/fft/verify.py'),'--out',str((a.out/'fft').resolve())],capture_output=True,text=True)
(a.out/'fft.txt').write_text(fft.stdout+fft.stderr,encoding='utf-8')
if fft.returncode: raise RuntimeError('Archived FFT recheck failed')
result=dict(status='PASS_CONSTRAINT_PACKAGE_NOT_H3',source_hashes=len(index['entries']),tests=11,
            base_main=index['base_main'],fft_candidate_commit=index['fft_candidate_commit'],
            budget_numeric_equal=True,budget_bytes_equal=encoded==(ROOT/'evidence/calculations.json').read_bytes(),
            fft_archive_recheck=True,new_xsim=False,new_synthesis=False,board_test=False)
(a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
