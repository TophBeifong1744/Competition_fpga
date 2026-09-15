"""Final offline audit and new batch hash list; never overwrite existing reports."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
out = ROOT/'evidence/final-check-01'
out.mkdir(exist_ok=False)
cmd = [sys.executable,'-B',str(ROOT/'finish_capture.py'),'--verify',str(ROOT/'delivery-01')]
with (out/'verify.log').open('x',encoding='utf-8') as f:
    proc = subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,shell=False)
with (out/'command.json').open('x',encoding='utf-8') as f:
    json.dump({'argv':cmd,'returncode':proc.returncode},f,indent=2)
if proc.returncode:
    raise SystemExit(proc.returncode)
inspection = json.loads((ROOT/'evidence/preflight-02/report.json').read_text(encoding='utf-8'))
for category in ('sources','loading'):
    for name,row in inspection[category].items():
        if hashlib.sha256(Path(row['path']).read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Input changed during delivery: '+name)
delivery = ROOT/'delivery-01'
repo = ROOT.parents[5]
for name,digest in json.loads((delivery/'dependencies.json').read_text(encoding='utf-8')).items():
    if hashlib.sha256((repo/name).read_bytes()).hexdigest() != digest:
        raise ValueError('Export dependency changed: '+name)
manifest = ROOT/'PACKAGE-SHA256.json'
hashes = {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
          for p in sorted(ROOT.rglob('*')) if p.is_file() and p != manifest}
with manifest.open('x',encoding='utf-8') as f:
    json.dump(hashes,f,indent=2)
    f.write('\n')
print('PACKAGE_AUDIT_PASS_NOT_B_ACCEPTANCE',len(hashes),'files')
