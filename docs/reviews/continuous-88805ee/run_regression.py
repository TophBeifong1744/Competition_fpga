"""Record applicable B regressions, always into a new package-external output directory."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument('repository')
parser.add_argument('output')
parser.add_argument('--host-gcc', required=True)
args = parser.parse_args()
root, out = Path(args.repository).resolve(), Path(args.output).resolve()
task = root / 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01'
if out.is_relative_to(task):
    raise ValueError('Output must be outside frozen package')
out.mkdir(parents=True, exist_ok=False)
here = Path(__file__).resolve().parent
commands = [
    ('package', [sys.executable, '-B', str(task / 'publication/verify_package.py')]),
    ('git-package', [sys.executable, '-B', str(here / 'audit_package.py'), str(root)]),
    ('check-capstone', [sys.executable, '-B', str(here / 'check_with_capstone.py'), str(task / 'board-run-20260915-02')]),
    ('bindings', [sys.executable, '-B', str(here / 'audit_bindings.py'), str(root)]),
    ('entry-tests', [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(task / 'tests'), '-p', 'test_entry.py', '-v']),
    ('safety-tests', [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(task.parent / 'current_build'), '-p', 'test_build_current.py', '-v']),
    ('host', [sys.executable, '-B', str(task / 'run.py'), 'host', '--host-gcc', args.host_gcc, '--output', str(out / 'host-run01')]),
]
records = []
for name, command in commands:
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out / (name + '.txt')).write_bytes(result.stdout)
    records.append(dict(name=name, argv=command, cwd=str(root), started_utc=started, exit_code=result.returncode))
    (out / 'commands.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
    print(name, 'exit_code=' + str(result.returncode), flush=True)
    if result.returncode:
        print(result.stdout.decode('utf-8', errors='replace'), flush=True)
        raise SystemExit(result.returncode)
print('PASS_B_POSTMERGE_SOFTWARE_AND_ARCHIVED_EVIDENCE_ONLY')
