"""Read-only E1 archive checks. Outputs go to a NEW directory outside the package.

Historical checker dependencies are extracted by exact Git commit into the output,
not installed into this checkout or the actual Vitis application. No board access.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
TASK = 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01'
C1 = TASK + '/continuous-prototype-01'
DEPENDENCY_SHA = 'bbe39c38dc36ccb4c0492f492b86f6c46d885fbe'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def put(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def verify_files(root, entries):
    for name, expected in entries.items():
        path = (root / name).resolve()
        require(root.resolve() in path.parents, 'Path escapes root: ' + name)
        require(digest(path) == expected, 'Hash mismatch: ' + name)
    return len(entries)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--gcc', type=Path, help='optional HOST compiler, never ARM/Vitis')
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.out.resolve()
    require(out != PACKAGE and PACKAGE not in out.parents, 'Output must be outside frozen E1')
    out.mkdir(parents=True, exist_ok=False)
    result = {'status': 'INCOMPLETE', 'dependency_commit': DEPENDENCY_SHA,
              'scope': 'A publication completeness / host rerun, NOT independent B approval',
              'commands': [], 'new_arm_build': False, 'new_board_run': False}
    try:
        sealed = read(PACKAGE / 'board-run-20260916-01/SHA256.json')['files']
        result['sealed_files'] = verify_files(PACKAGE, sealed)
        result['sealed_manifest_sha256'] = digest(PACKAGE / 'board-run-20260916-01/SHA256.json')
        build = PACKAGE / 'evidence/user-build-20260916-2052'
        result['build_manifest_files'] = verify_files(PACKAGE, read(build / 'BATCH-SHA256.json')['files'])
        result['snapshot_files'] = verify_files(build / 'app', read(build / 'snapshot-binding.json'))
        publication_manifest = HERE / 'PACKAGE-SHA256.json'
        if publication_manifest.exists():
            result['publication_files'] = verify_files(PACKAGE, read(publication_manifest)['files'])

        def command(name, argv, cwd=PACKAGE):
            argv = [str(item) for item in argv]
            run = subprocess.run(argv, cwd=cwd, capture_output=True)
            (out / (name + '.stdout')).write_bytes(run.stdout)
            (out / (name + '.stderr')).write_bytes(run.stderr)
            record = {'argv': argv, 'cwd': str(cwd), 'returncode': run.returncode}
            put(out / (name + '.command.json'), record)
            result['commands'].append(record)
            require(run.returncode == 0, name + ' failed, see preserved logs')
            return run.stdout

        def git(*argv):
            proc = subprocess.run(['git', '-c', 'core.longpaths=true', '-C', str(repo), *argv], capture_output=True)
            require(proc.returncode == 0, 'Git dependency access failed: ' + proc.stderr.decode(errors='replace'))
            return proc.stdout

        git('cat-file', '-e', DEPENDENCY_SHA + '^{commit}')
        names = [C1 + '/timerfixed-entry-01/' + name for name in ('check_entry.py', 'POLICY.json')]
        names += [TASK + '/current_build/' + name for name in ('build_current.py', 'ps_contract.py')]
        names += git('ls-tree', '-r', '--name-only', DEPENDENCY_SHA, C1 + '/board-run-20260915-02').decode().splitlines()
        names += [C1 + '/tests/test_core.c']
        dep = out / 'historical-dependencies'
        provenance = {}
        for name in names:
            raw = git('cat-file', 'blob', DEPENDENCY_SHA + ':' + name)
            target = dep / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            provenance[name] = hashlib.sha256(raw).hexdigest()
        put(out / 'dependency-files.json', {'commit': DEPENDENCY_SHA, 'files': provenance})
        dep_c1 = dep / C1
        result['pinned_checker_files'] = verify_files(dep_c1, read(PACKAGE / 'POLICY.json')['checker_dependencies'])
        base_policy = read(dep_c1 / 'timerfixed-entry-01/POLICY.json')
        result['pinned_helpers'] = verify_files(dep / TASK / 'current_build', base_policy['helper_sha256'])
        result['historical_hardware_files'] = verify_files(dep_c1 / 'board-run-20260915-02/runtime', base_policy['hardware_sha256'])
        # Compare reused approved dependencies with this main-based publication tree.
        for name, sha in provenance.items():
            if '/timerfixed-entry-01/' not in name:
                require(digest(repo / name) == sha, 'Published main dependency differs: ' + name)

        board = PACKAGE / 'board-run-20260916-01'
        command('hashes', [sys.executable, '-B', board / 'record_checks.py', 'verify'])
        command('log-tests', [sys.executable, '-B', board / 'test_verify_log.py'])
        command('uart', [sys.executable, '-B', board / 'verify_log.py',
                        board / 'endurance_300s_10x10s_20260916_01.log', '--out', out / 'uart.json'])
        result['totals'] = read(out / 'uart.json')['totals']
        bootstrap = ('import sys,runpy;sys.path.insert(0,sys.argv[1]);import check_entry;'
                     'target=sys.argv[2];sys.argv=[target];runpy.run_path(target,run_name="__main__")')
        for name in ('test_gate', 'test_timer_layout'):
            command(name, [sys.executable, '-B', '-c', bootstrap,
                           dep_c1 / 'timerfixed-entry-01', PACKAGE / 'tests' / (name + '.py')])
        compiled = ('import sys,json;sys.path.insert(0,sys.argv[1]);import check_entry;'
                    'sys.path.insert(0,sys.argv[2]);import check_endurance as gate;'
                    'print(json.dumps(gate.compiled(sys.argv[3],sys.argv[4]),indent=2))')
        raw = command('compiled-archive', [sys.executable, '-B', '-c', compiled,
                      dep_c1 / 'timerfixed-entry-01', PACKAGE,
                      build / 'app/build/CMakeFiles/four_mic_endurance.elf.dir/main.c.obj',
                      build / 'app/build/four_mic_endurance.elf'])
        result['compiled_archive'] = json.loads(raw)
        result['python_test_methods'] = 4 + 7 + 12
        result['host_model'] = 'NOT_RERUN'
        if args.gcc:
            exe = out / 'test_endurance.exe'
            command('host-compile', [args.gcc.resolve(), '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
                    '-Wno-misleading-indentation', '-I' + str(PACKAGE / 'proposed-src/continuous'),
                    '-I' + str(dep_c1 / 'tests'), PACKAGE / 'proposed-src/continuous/continuous_core.c',
                    PACKAGE / 'tests/test_endurance.c', '-o', exe])
            raw = command('host-model', [exe])
            require(b'ENDURANCE_MODEL_PASS' in raw, 'Missing host model PASS')
            result['host_model'] = 'old16 + schedule11 + invalid/retry/null/deadline; NOT board'
        result['status'] = 'PASS_PUBLICATION_CHECKS_NOT_B_ACCEPTANCE'
    except Exception as exc:
        result['status'] = 'FAIL'
        result['error'] = str(exc)
    put(out / 'result.json', result)
    print(result['status'], out)
    return 0 if result['status'].startswith('PASS') else 1


if __name__ == '__main__':
    raise SystemExit(main())
