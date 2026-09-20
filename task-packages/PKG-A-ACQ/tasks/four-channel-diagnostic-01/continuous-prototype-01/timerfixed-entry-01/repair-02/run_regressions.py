"""Capture baseline or repaired TF-B-02-R1 checks; no ARM build/link or hardware."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ENTRY = HERE.parent


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('baseline', 'fixed'), required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--gcc', type=Path, required=True, help='host GCC, only -### argument printing')
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {'phase': args.phase, 'status': 'INCOMPLETE', 'started_utc': datetime.now(timezone.utc).isoformat(),
              'command_contract_sha256': hashlib.sha256((ENTRY / 'command_contract.py').read_bytes()).hexdigest(),
              'scope': 'Command comparison and offline regressions; no ARM build/link/board', 'commands': []}

    def run(name, argv, expected_zero=True):
        argv = [str(item) for item in argv]
        result = subprocess.run(argv, cwd=ENTRY, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'),
                                capture_output=True, text=True, errors='replace')
        row = {'argv': argv, 'cwd': str(ENTRY), 'returncode': result.returncode,
               'stdout': result.stdout, 'stderr': result.stderr}
        save(out / (name + '.json'), row)
        report['commands'].append({'name': name, 'returncode': result.returncode})
        if expected_zero and result.returncode:
            raise ValueError(name + ' failed; logs retained')
        return result

    try:
        raw_path = HERE / 'review-inputs/spec/check_arguments.py'
        source = raw_path.read_text(encoding='utf-8')
        old = 'norm = lambda s: cc.normalize_command(s, app, bsp)'
        new = ('def norm(s):\n'
               '    try: return cc.normalize_command(s, app, bsp)\n'
               '    except ValueError as exc: return ("REJECTED_BY_PARSER", str(exc))')
        if source.count(old) != 1:
            raise ValueError('Unexpected B source; do not guess adaptation')
        adapted = out / 'check_arguments_adapted.py'
        with adapted.open('x', encoding='utf-8') as stream:
            stream.write(source.replace(old, new))
        save(out / 'adaptation.json', {'original_sha256': hashlib.sha256(raw_path.read_bytes()).hexdigest(),
              'changed_only': 'norm diagnostic wrapper catches ValueError to report strict rejection; gate and inputs unchanged',
              'before': old, 'after': new})
        run('b-arguments', [sys.executable, '-B', adapted, '--package', ENTRY, '--output', out / 'b-arguments', '--gcc', args.gcc])
        run('b-extra', [sys.executable, '-B', HERE / 'review-inputs/spec/extra_link_flags.py',
                       '--package', ENTRY, '--output', out / 'b-extra'])
        base = json.loads((out / 'b-arguments/result.json').read_text())
        extra = json.loads((out / 'b-extra/result.json').read_text())
        composite = next(c for c in base['cases'] if 'verify_link_output' in c)
        statuses = [composite['verify_link_output']] + [row['status'] for row in extra]
        report['b_four_actual_statuses'] = statuses
        wanted = 'ACCEPTED' if args.phase == 'baseline' else 'REJECTED'
        if not all(s.startswith(wanted) for s in statuses):
            raise ValueError('Four B counterexamples differ from expected ' + wanted)
        for row in base['cases']:
            if 'expected_equal' in row and row['accepted_as_equal'] != row['expected_equal']:
                raise ValueError('Old macro/quote/case behavior regressed')
            if 'actual' in row and row['actual'] != row['expected']:
                raise ValueError('Ordinary extra flag was accepted')
        native = base['native_gcc_argument_evidence']
        if native['returncode'] or native['output_created']:
            raise ValueError('Host GCC -### probe failed or generated a program')
        tests = run('new12', [sys.executable, '-B', HERE / 'test_linker_args.py'], expected_zero=args.phase == 'fixed')
        if args.phase == 'baseline':
            if tests.returncode == 0:
                raise ValueError('Expected baseline regression failure missing')
            report['status'] = 'BASELINE_DEFECT_REPRODUCED_NOT_REPAIR_PASS'
        else:
            run('old-b-negatives', [sys.executable, '-B', ENTRY / 'repair-01/reproduce_b_negatives.py', out / 'old-b-negatives'])
            run('original82', [sys.executable, '-B', ENTRY / 'repair-01/run_checks.py', out / 'original82'])
            report['status'] = 'PASS_R1_AUTHOR_REGRESSION_NOT_B_APPROVAL'
    except Exception as exc:
        report['status'] = 'FAIL'
        report['error'] = str(exc)
    save(out / 'result.json', report)
    print(report['status'], out)
    return 1 if report['status'] == 'FAIL' else 0


if __name__ == '__main__':
    raise SystemExit(main())
