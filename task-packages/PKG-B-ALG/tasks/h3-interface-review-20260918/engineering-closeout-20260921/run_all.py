"""No overwrite; subprocess logs, commands, exact sources and output hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    repo, out, here = a.repo.resolve(), a.out.resolve(), Path(__file__).resolve().parent
    out.mkdir(parents=True, exist_ok=False)
    commands = [
        [sys.executable, '-B', str(here/'verify_increment.py'), '--repo', str(repo), '--out', str(out/'checks')],
        [sys.executable, '-B', str(here/'budget_ledger.py'), '--config', str(here/'budget_config.json'), '--out', str(out/'budget.json')],
        [sys.executable, '-B', str(here/'trace_scoreboard.py'), str(out/'checks/valid-trace.json'), '--max-stall-ticks', '2', '--expected-units', 'fft', 'ifft']]
    results = []
    for i, command in enumerate(commands):
        proc = subprocess.run(command, cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (out/f'stage-{i}.log').write_bytes(proc.stdout)
        results.append(dict(command=command, cwd=str(repo), exit_code=proc.returncode))
        if proc.returncode:
            break
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in here.iterdir() if p.is_file() and p.suffix in ('.py', '.json')}
    (out/'runner.json').write_text(json.dumps(dict(commands=results, source_sha256=hashes), indent=2)+'\n', encoding='utf-8')
    output_hashes = {p.relative_to(out).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}
    (out/'OUTPUT-SHA256.json').write_text(json.dumps(output_hashes, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(stages=len(results), exit_codes=[r['exit_code'] for r in results])))
    return int(any(r['exit_code'] for r in results))


if __name__ == '__main__':
    sys.exit(main())
