"""A audit runner; append-only outputs, untouched delivery and shared checkout."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ap = argparse.ArgumentParser()
ap.add_argument('--repo', type=Path, required=True)
ap.add_argument('--out', type=Path, required=True)
ap.add_argument('--mode', choices=['fixed', 'register', 'fft29', 'archive'], required=True)
a = ap.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1',
           GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='safe.directory',
           GIT_CONFIG_VALUE_0=a.repo.as_posix())
commands = []

def run(label, argv):
    start = datetime.now(timezone.utc).isoformat()
    with (a.out/(label+'.stdout.txt')).open('wb') as stdout, (a.out/(label+'.stderr.txt')).open('wb') as stderr:
        p = subprocess.run(argv, cwd=a.repo, env=env, stdout=stdout, stderr=stderr)
    commands.append(dict(label=label, command=argv, cwd=str(a.repo), start=start,
                         end=datetime.now(timezone.utc).isoformat(), exit_code=p.returncode))
    (a.out/'commands.json').write_text(json.dumps(commands, indent=2)+'\n', encoding='utf-8')
    print(label, 'exit', p.returncode, flush=True)
    if p.returncode:
        print((a.out/(label+'.stderr.txt')).read_text(encoding='utf-8', errors='replace'))
        raise SystemExit(p.returncode)

run('head', ['git', 'rev-parse', 'HEAD'])
if a.mode == 'fixed':
    assert (a.out/'head.stdout.txt').read_text().strip() == '6cb76d11615b3f58e8350767a86479946fc34133'
    task = 'task-packages/PKG-B-ALG/tasks/phat-fixed-03/closeout-01'
    def snapshot():
        return {p.relative_to(a.repo/task).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted((a.repo/task).rglob('*')) if p.is_file()}
    before = snapshot()
    run('verify-delivery', [sys.executable, '-B', task+'/verify_delivery.py'])
    run('analyze', [sys.executable, '-B', task+'/analyze.py', '--out', str(a.out/'analysis')])
    assert before == snapshot(), 'Delivery mutated'
    (a.out/'delivery-before-after.json').write_text(json.dumps(before, indent=2)+'\n', encoding='utf-8')
elif a.mode == 'register':
    run('verify-register', [sys.executable, '-B', 'task-packages/PKG-B-ALG/tasks/four-channel-receipt-01/real-input-20260911/verify_register.py'])
elif a.mode == 'archive':
    task = 'task-packages/PKG-B-ALG/tasks/phat-fixed-03/closeout-01'
    run('verify-delivery', [sys.executable, '-B', task+'/verify_delivery.py'])
    run('compare-pinned-package', ['git', 'diff', '--exit-code', '6cb76d11615b3f58e8350767a86479946fc34133', 'HEAD', '--', task])
else:
    assert (a.out/'head.stdout.txt').read_text().strip() == 'c0b5f8fb44643e81d8c4e6f0be457dddeae9758e'
    task = a.repo/'task-packages/PKG-A-ACQ/tasks/fft29-bitexact-budget-01'
    run('manifest', [sys.executable, '-B', str(task/'source/package_manifest.py'), 'check'])
    run('resources', [sys.executable, '-B', str(task/'source/check_resources.py')])
    run('archived-rtl-comparison', [sys.executable, '-B', str(task/'source/check.py'),
        '--vectors', str(task/'evidence/run01/vectors'), '--simulation', str(task/'evidence/run01/simulation'),
        '--out', str(a.out/'archived-rtl-comparison.json')])
run('status', ['git', 'status', '--porcelain'])
assert not (a.out/'status.stdout.txt').read_text().strip(), 'Audit checkout not clean'
