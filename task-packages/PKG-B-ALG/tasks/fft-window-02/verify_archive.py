"""Verify sealed task files and recheck archived model/XSim exact codes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
out=args.out.resolve()
if out==HERE or HERE in out.parents:
    parser.error('write verification outside sealed task package')
for name,expected in json.loads((HERE/'hashes.json').read_text()).items():
    assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==expected,name
evidence=HERE/'evidence/run01'
subprocess.run([sys.executable,'-B',str(HERE/'check_simulation.py'),'--vectors',str(evidence),
    '--sim',str(evidence),'--log',str(evidence/'simulation.txt'),'--out',str(out)],check=True)
print('PASS_ARCHIVE_HASHES_AND_EXACT_CODES; archived evidence only, not a new RTL run')
