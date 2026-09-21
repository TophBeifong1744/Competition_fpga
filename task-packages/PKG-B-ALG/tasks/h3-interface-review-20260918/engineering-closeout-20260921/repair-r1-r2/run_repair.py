"""Run only the changed checker scope; persist exact commands/logs/hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from check_repair import verify


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    repo, out, here = a.repo.resolve(), a.out.resolve(), Path(__file__).resolve().parent
    out.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, '-B', str(here/'verify_repair.py'), '--repo', str(repo), '--out', str(out/'checks')]
    process = subprocess.run(command, cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out/'run.log').write_bytes(process.stdout)
    sources = [here/'verify_repair.py', here/'run_repair.py', here/'check_repair.py', here.parent/'trace_scoreboard.py']
    hashes = {p.relative_to(repo).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    metadata = dict(command=command, cwd=str(repo), exit_code=process.returncode,
                    python=sys.version, source_sha256=hashes)
    (out/'runner.json').write_text(json.dumps(metadata, indent=2)+'\n', encoding='utf-8')
    outputs = {p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}
    (out/'OUTPUT-SHA256.json').write_text(json.dumps(outputs, indent=2)+'\n', encoding='utf-8')
    if process.returncode:
        print(json.dumps(dict(status='REPAIR_FAILED', exit_code=process.returncode)))
        return process.returncode
    result = verify(repo, out)
    # Check result is intentionally outside the already verified output manifest.
    (out/'delivery.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    sys.exit(main())
