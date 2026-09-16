"""Record applicable A checks in a fresh external directory, without editing B."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np


def main():
    ap = argparse.ArgumentParser(__doc__)
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    root, out = args.repo.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    parent = 'task-packages/PKG-B-ALG/tasks/four-channel-track-01'
    audio = parent+'/audio-01'
    base = [sys.executable, '-B']
    commands = [
        ('integrity', base+[audio+'/verify_package.py']),
        ('audio', base+[audio+'/reproduce.py', '--out', str(out/'audio-run01')]),
        ('parent', base+[parent+'/reproduce.py', '--out', str(out/'parent-run01')]),
        ('parent-comparison', base+[parent+'/verify.py', '--compare', str(out/'parent-run01/replay')]),
        ('saved-comparison', base+[audio+'/verify_package.py', '--compare-saved']),
        ('independent', base+[str(Path(__file__).with_name('independent_check.py')),
                            '--repo', str(root), '--runs', str(out), '--out', str(out/'independent01')]),
        ('integrity-after', base+[audio+'/verify_package.py'])]
    results = []
    for label, command in commands:
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with (out/(label+'.log')).open('xb') as log:
            p = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT)
        results.append(dict(label=label, command=command, cwd=str(root), started_utc=started, exit_code=p.returncode))
        (out/'commands.json').write_text(json.dumps(results, indent=2)+'\n', encoding='utf-8')
        print(label, p.returncode, flush=True)
        if p.returncode:
            raise SystemExit(p.returncode)
    head = subprocess.check_output(['git', '-c', 'safe.directory='+root.as_posix(), 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    inventory = {p.relative_to(out).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                 for p in sorted(out.rglob('*')) if p.is_file()}
    report = dict(checkout_head=head, python=sys.version, numpy=np.__version__, platform=platform.platform(), artifacts=inventory)
    (out/'run-inventory.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
