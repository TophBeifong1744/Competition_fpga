"""Single-command author replay and targeted regression; preserve every run."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    tb = HERE.parents[1]/'payload/tb/python'
    commands = [
        ('adapter-tests', [sys.executable, '-B', str(HERE/'test_tracking.py'), '-v']),
        ('tracker-regression', [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(tb), '-p', 'test_sector_tracker.py', '-v']),
        ('framing-regression', [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(tb), '-p', 'test_audio_frames.py', '-v']),
        ('real-replay', [sys.executable, '-B', str(HERE/'run.py'), '--out', str(out/'replay')]),
    ]
    records = []
    for label, command in commands:
        with (out/(label+'.log')).open('xb') as log:
            result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        records.append(dict(label=label, command=command, cwd=str(ROOT), returncode=result.returncode))
        (out/'commands.json').write_text(json.dumps(records, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(label, 'PASS' if result.returncode == 0 else 'FAIL', flush=True)
        if result.returncode:
            raise SystemExit(result.returncode)
    files = sorted(p for p in out.rglob('*') if p.is_file())
    manifest = {p.relative_to(out).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (out/'SHA256.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
