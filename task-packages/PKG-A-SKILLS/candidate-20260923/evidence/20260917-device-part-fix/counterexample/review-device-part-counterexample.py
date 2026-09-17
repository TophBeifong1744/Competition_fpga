"""Isolated counterexample: HWH PART is wrong; unrelated attribute is a decoy."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parent
fixture = root / 'pynq-overlay-dma-validation/references/example-receive'
out = root / 'review-evidence/device-part-counterexample-02'
if out.exists():
    raise SystemExit('output exists')
shutil.copytree(fixture, out)
schema = fixture.parent / 'soundsight-record-v1.json'
schema_copy = out.parent / schema.name
if not schema_copy.exists():
    shutil.copyfile(schema, schema_copy)
hwh = out / 'design.hwh'
before = hwh.read_text(encoding='utf-8')
after = before.replace('PART="xc7z020clg400-2"', 'PART="xc7z010clg400-2"', 1)
after = after.replace('MODTYPE="axi_dma"', 'COMMENT="xc7z020clg400-2" MODTYPE="axi_dma"', 1)
assert after != before
hwh.write_text(after, encoding='utf-8')
manifest = out / 'build-manifest.json'
record = json.loads(manifest.read_text(encoding='utf-8'))
record['hwh']['sha256'] = hashlib.sha256(hwh.read_bytes()).hexdigest()
manifest.write_text(json.dumps(record, indent=2), encoding='utf-8')
cmd = [sys.executable, '-B', str(root / 'pynq-overlay-dma-validation/scripts/validate_receive_profile.py'),
       '--profile', str(out / 'receive-profile.json'), '--output', str(out / 'result.json')]
run = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
(out / 'stdout.log').write_text(run.stdout, encoding='utf-8')
(out / 'stderr.log').write_text(run.stderr, encoding='utf-8')
report = json.loads((out / 'result.json').read_text(encoding='utf-8'))
print(json.dumps({'exit_code': run.returncode, 'status': report['status'],
                  'declared_part': 'xc7z020clg400-2', 'actual_hwh_part': 'xc7z010clg400-2',
                  'issue_codes': [x['code'] for x in report['issues']]}, indent=2))
