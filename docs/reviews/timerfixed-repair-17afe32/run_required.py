"""B review: archive actual commands/results outside the frozen package."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path('F:/NUEC/review-worktrees/timerfixed-repair-17afe32')
PACKAGE = ROOT / 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/timerfixed-entry-01'
out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=False)
env = dict(os.environ, TF_TCL='F:/STUDY/IT/Anaconda3/Library/bin/tclsh.exe', PYTHONDONTWRITEBYTECODE='1')
jobs = [
    ('manifest', [sys.executable, '-B', 'repair-01/verify_repair.py']),
    ('b-negatives', [sys.executable, '-B', 'repair-01/reproduce_b_negatives.py', str(out/'b-negatives')]),
    ('checks', [sys.executable, '-B', 'repair-01/run_checks.py', str(out/'checks')]),
]
results = []
for name, argv in jobs:
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    p = subprocess.run(argv, cwd=PACKAGE, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=300)
    result = dict(name=name, argv=argv, cwd=str(PACKAGE), started_utc=start,
                  finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  returncode=p.returncode, stdout=p.stdout, stderr=p.stderr, TF_TCL=env['TF_TCL'])
    (out/(name+'.json')).write_text(json.dumps(result, indent=2), encoding='utf-8')
    results.append(result)
    print(name, p.returncode, p.stdout, p.stderr, flush=True)
(out/'summary.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
sys.exit(any(r['returncode'] for r in results))
