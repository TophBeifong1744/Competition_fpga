"""Issue 26 read-only layout diagnostics; writes only its own evidence directory."""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
SHARED = Path('E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga')
BASE = '0a5f544893cff1094bcd1bad5346a1cf05790707'
PWSH = Path('C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
VIVADO = 'F:/AMD/2025.2/Vivado/bin'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def now():
    return datetime.now(timezone.utc).isoformat()

def preflight():
    old = read(SHARED / 'sim/modules.json')
    new = read(ROOT / 'simulation/modules.json')
    comparison = copy.deepcopy(new)
    changed = []
    identities = []
    assert len(old['files']) == len(new['files']) == 11
    assert len(old['cases']) == len(new['cases']) == 7
    for index, (before, after) in enumerate(zip(old['files'], new['files'])):
        comparison['files'][index]['target'] = before['target']
        if before['target'] != after['target']:
            changed.append(f'files[{index}].target')
        a, b = SHARED / before['target'], ROOT / after['target']
        identities.append({'kind': 'HDL_TB', 'old': before['target'], 'new': after['target'],
                           'shared_sha256': digest(a), 'candidate_sha256': digest(b),
                           'byte_identical': a.read_bytes() == b.read_bytes()})
    for index, (before, after) in enumerate(zip(old['cases'], new['cases'])):
        comparison['cases'][index]['sources'] = before['sources']
        if before['sources'] != after['sources']:
            changed.append(f'cases[{index}].sources')
    fixtures = sorted((ROOT / 'data/fixtures/h1').rglob('*'))
    for b in fixtures:
        if b.is_file():
            suffix = b.relative_to(ROOT / 'data/fixtures/h1')
            a = SHARED / 'examples/h1' / suffix
            identities.append({'kind': 'H1_FIXTURE', 'old': a.relative_to(SHARED).as_posix(),
                               'new': b.relative_to(ROOT).as_posix(), 'shared_sha256': digest(a),
                               'candidate_sha256': digest(b), 'byte_identical': a.read_bytes() == b.read_bytes()})
    assert sum(x['kind'] == 'H1_FIXTURE' for x in identities) == 5
    shared_head = subprocess.check_output(['git', '-c', f'safe.directory={SHARED.as_posix()}',
                                          '-C', str(SHARED), 'rev-parse', 'HEAD'], text=True).strip()
    facts = {'base_commit': BASE, 'shared_head': shared_head, 'manifest_only_allowed_fields_changed': comparison == old,
             'manifest_changed_fields': changed, 'identities': identities,
             'servo_status': [f.get('status') for f in new['files'] if '/servo/' in f['target']]}
    save('preflight.json', facts)
    assert shared_head == BASE, 'Shared HEAD no longer matches assigned baseline'
    assert comparison == old, 'Manifest changes exceed files.target / cases.sources'
    assert all(x['byte_identical'] for x in identities), 'Moved source bytes differ'
    inputs = {ROOT / x['new'] for x in identities}
    inputs.update(ROOT / x for x in ('simulation/modules.json', 'simulation/run_regression.ps1',
                                     'simulation/run_servo.ps1', 'scripts/check_h1_fixtures.py',
                                     'scripts/run_module_skill_examples.py'))
    inputs.update(p for p in (ROOT / 'skill/fpga-module-verification').rglob('*') if p.is_file())
    snapshot = {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(inputs)}
    save('inputs-before.json', snapshot)
    save('run-manifest.json', {'schema_version': '1.0.0', 'run_id': OUT.name,
         'snapshot_id': 'sha256:' + hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest(),
         'base_commit': BASE, 'issue': 26, 'scope': 'ANALYZE / DIAGNOSTIC_SMOKE',
         'claim_stage': 'SIM_SMOKE', 'verdict': 'DIAGNOSTIC_ONLY', 'cwd': str(ROOT),
         'python': sys.executable, 'python_version': sys.version, 'pwsh': str(PWSH),
         'vivado_bin': VIVADO, 'started_utc': now(), 'runs': [],
         'seed_policy': 'Existing deterministic TB seeds preserved; no runner seed override',
         'seeds': {'servo': 'DIRECTED_NO_RNG', 'stats': 'DIRECTED_NO_RNG',
                   'snapshot': '0xd1b54a32d192ed03', 'snapshot_joint': 'DIRECTED_NO_RNG',
                   'snapshot_independent': '0x7f2ac819008bed35', 'pcm4': '0x13579bdf XOR W',
                   'pcm4_independent': '0xdf931a27', 'skill_pcm4': '0x76543210', 'skill_elastic': '0x12345678'},
         'not_run': ['functional acceptance', 'negative HDL mutations', 'formal', 'CDC/RDC signoff',
                     'synthesis', 'implementation', 'STA', 'board', 'FFT', 'endurance',
                     'historical architecture input-boundary hash check'],
         'historical_boundary_note': 'Architecture hash baseline already mismatches; no PASS claimed'})
    print(json.dumps({'preflight': 'IDENTITY_MATCH', 'hdl_tb': 11, 'fixtures': 5,
                      'frozen_files': len(snapshot), 'manifest_allowed_changes': len(changed)}), flush=True)

def check_inputs(label):
    before = read(OUT / 'inputs-before.json')
    current = {name: digest(ROOT / name) if (ROOT / name).is_file() else None for name in before}
    changes = [name for name in before if current[name] != before[name]]
    save('inputs-latest.json', {'checkpoint': label, 'utc': now(), 'changed': changes, 'hashes': current})
    if changes:
        raise RuntimeError('INPUT_CHANGED: ' + repr(changes))

def tree_hash(path):
    return {str(p.relative_to(path)): digest(p) for p in path.rglob('*') if p.is_file()}

def execute(name, command, *, cwd=ROOT, negative=None, timeout=1200):
    check_inputs('before:' + name)
    logdir = OUT / 'commands' / name
    logdir.mkdir(parents=True, exist_ok=False)
    evidence = {'name': name, 'argv': [str(v) for v in command], 'cwd': str(cwd), 'started_utc': now(),
                'stdout': str((logdir / 'stdout.txt').relative_to(OUT)),
                'stderr': str((logdir / 'stderr.txt').relative_to(OUT)),
                'expectation': negative or 'exit code 0'}
    manifest = read(OUT / 'run-manifest.json')
    manifest['runs'].append(evidence)
    save('run-manifest.json', manifest)
    started = time.monotonic()
    with (logdir / 'stdout.txt').open('wb') as stdout, (logdir / 'stderr.txt').open('wb') as stderr:
        process = subprocess.Popen(evidence['argv'], cwd=cwd, stdout=stdout, stderr=stderr)
        while True:
            try:
                code = process.wait(timeout=20)
                break
            except subprocess.TimeoutExpired:
                print(json.dumps({'running': name, 'elapsed_seconds': round(time.monotonic() - started),
                                  'pid': process.pid}), flush=True)
                if time.monotonic() - started > timeout:
                    subprocess.run(['taskkill.exe', '/PID', str(process.pid), '/T', '/F'],
                                   stdout=stderr, stderr=stderr, check=False)
                    code = process.wait(timeout=15)
                    evidence['classification'] = 'TIMEOUT_HANG'
                    break
    evidence.update(exit_code=code, ended_utc=now(), elapsed_seconds=round(time.monotonic() - started, 3))
    text = (logdir / 'stdout.txt').read_text(encoding='utf-8', errors='replace') + (logdir / 'stderr.txt').read_text(encoding='utf-8', errors='replace')
    evidence['expectation_met'] = code != 0 and negative in text if negative else code == 0
    evidence['stdout_sha256'] = digest(logdir / 'stdout.txt')
    evidence['stderr_sha256'] = digest(logdir / 'stderr.txt')
    manifest['runs'][-1] = evidence
    save('run-manifest.json', manifest)
    check_inputs('after:' + name)
    print(json.dumps({'completed': name, 'exit_code': code, 'expectation_met': evidence['expectation_met']}), flush=True)
    return evidence['expectation_met']

def summarize():
    manifest = read(OUT / 'run-manifest.json')
    modules = read(ROOT / 'simulation/modules.json')
    rows = []
    def logtext(path):
        return path.read_text(encoding='utf-8-sig', errors='replace') if path.is_file() else ''
    def native_row(name, top, directory, sources, result, marker):
        logs = list(directory.glob('*.txt')) + list(directory.glob('*.log'))
        combined = '\n'.join(logtext(path) for path in logs)
        paths = re.findall(r'Analyzing (?:System)?Verilog file "([^"]+)"', combined)
        paths = sorted(set(p.replace('\\', '/') for p in paths))
        expected = [str(ROOT / source).replace('\\', '/') for source in sources]
        simlog = logtext(directory / 'simulation.log')
        row = {'name': name, 'top': top, 'output_directory': str(directory.relative_to(OUT)),
               'status': 'DIAGNOSTIC_ONLY' if marker in simlog else 'INCONCLUSIVE',
               'native_result': result, 'actual_loader_paths': paths,
               'all_requested_sources_observed': all(p in paths for p in expected),
               'marker': marker, 'marker_seen': marker in simlog,
               'compile_logs': [str(p.relative_to(OUT)) for p in logs if 'compile' in p.name],
               'elaborate_log': str((directory / 'elaborate.txt').relative_to(OUT)),
               'run_log': str((directory / 'simulation.log').relative_to(OUT)),
               'isolated_library': str((directory / 'xsim.dir').relative_to(OUT)),
               'warnings': sorted(set(re.findall(r'(?im)^.*\bwarning\b.*$', combined)))}
        rows.append(row)
    regression = read(OUT / 'regression/result.json')
    for case in modules['cases']:
        native_row('regression/' + case['name'], case['top'], OUT / 'regression' / case['name'],
                   case['sources'], next((x for x in regression['cases'] if x['name'] == case['name']), None), case['marker'])
    servo = read(OUT / 'servo-1mhz/result.json')
    native_row('servo-1mhz', 'tb_motor_drive', OUT / 'servo-1mhz',
               [f['target'] for f in modules['files'] if '/servo/' in f['target']], servo,
               'PASS motor_drive checks=39 CLK_FREQ_HZ=1000000 MAX_ANGLE_DEG=360')
    skill = read(OUT / 'skill-examples/summary.json')
    for case in skill['cases']:
        directory = OUT / 'skill-examples/runs' / case['name']
        result = read(directory / 'result.json')
        derived = read(OUT / 'skill-examples' / case['derived_case'])
        identities = []
        for source in result['sources']:
            source_path = Path(source['path'])
            snapshot = directory / source['snapshot']
            compiled = directory / 'work' / source_path.name
            identities.append({'resolved_source': str(source_path), 'snapshot': str(snapshot.relative_to(OUT)),
                               'compiled_copy': str(compiled.relative_to(OUT)), 'sha256': source['sha256'],
                               'all_three_bytes_identical': digest(source_path) == digest(snapshot) == digest(compiled) == source['sha256']})
        rows.append({'name': 'skill/' + case['name'], 'top': result['top'],
                     'status': 'DIAGNOSTIC_ONLY' if result['status'] == 'PASS_SIMULATION' else 'INCONCLUSIVE',
                     'native_status': result['status'], 'checks': result.get('checks'),
                     'result': str((directory / 'result.json').relative_to(OUT)),
                     'commands': result['commands'], 'load_chain': identities,
                     'derived_sources': derived['sources'], 'isolated_library': str((directory / 'work/xsim.dir').relative_to(OUT))})
    fixture = logtext(OUT / 'commands/h1-fixtures/stdout.txt')
    stability = read(OUT / 'inputs-after.json')
    checks = {'manifest_only_target_and_sources_changed': read(OUT / 'preflight.json')['manifest_only_allowed_fields_changed'],
              'all_16_moved_inputs_byte_identical': all(x['byte_identical'] for x in read(OUT / 'preflight.json')['identities']),
              'source_inputs_stable': not stability['changed'],
              'all_native_requested_sources_loaded': all(x.get('all_requested_sources_observed', True) for x in rows),
              'all_skill_snapshots_match_originals': all(v['all_three_bytes_identical'] for x in rows for v in x.get('load_chain', [])),
              'all_commands_match_expectations': manifest['all_command_expectations_met'],
              'h1_fixture_markers': 'PASS fixture code-pattern: 6 rows' in fixture and 'PASS fixture restart: 2 rows' in fixture}
    summary = {'schema_version': '1.0.0', 'run_id': OUT.name, 'snapshot_id': manifest['snapshot_id'],
               'claim_stage': 'SIM_SMOKE', 'verdict': 'DIAGNOSTIC_ONLY' if all(checks.values()) else 'INCONCLUSIVE',
               'checks': checks, 'matrix': rows, 'negative_cases': [x for x in manifest['runs'] if x['name'].startswith('negative-')],
               'tool_banner': logtext(OUT / 'commands/tool-version/stdout.txt').strip(),
               'source_stability_count': len(stability['hashes']), 'traceability': {
                   'R1_original_input_bytes': 'preflight.json: 11 HDL/TB + 5 fixtures compared to shared original paths',
                   'R2_provenance_approval_unchanged': 'preflight.json: deep manifest comparison permits only files.target/cases.sources',
                   'R3_new_entry_loads_relocated_sources': 'matrix: compiler loader lines and skill source/snapshot/work-copy hashes',
                   'R4_bounded_smoke_completion': 'run-manifest.json: four sequential entry points, logs, exit codes',
                   'R5_reject_unsafe_or_existing_output': 'negative_cases: rejected before EDA; existing evidence hashes unchanged',
                   'R6_frozen_runtime_inputs': 'inputs-before.json and inputs-after.json: 37 stable actual dependencies'},
               'changed_test_assets': [], 'changed_product_assets': [], 'defects': [],
               'limitations': ['Diagnostic scope only; native PASS strings retained as raw observations, not functional acceptance',
                               'Servo MAX_ANGLE_DEG candidate pending independent review remains unchanged',
                               'Regression script stores overall exit and markers, not individual numeric stage exits; guard code checks each stage',
                               'Historical architecture input-boundary hash mismatch was already known; check NOT RUN',
                               'No desktop BAT, vendor export/preparation, or external one project is in this task',
                               'Initial recorder preflight erroneously tried historical provenance paths omitted from sparse candidate; recorder corrected to actual execution dependencies before any EDA'],
               'required_reruns': ['Rerun affected cases only if an input fingerprint or loader/runner changes'],
               'not_run': manifest['not_run']}
    save('summary.json', summary)
    print(json.dumps({'summary': summary['verdict'], 'checks': checks, 'matrix_count': len(rows)}), flush=True)

def run():
    ps = [str(PWSH), '-NoProfile', '-File']
    py = [sys.executable, '-B']
    version = OUT / 'version'
    version.mkdir()
    if not execute('tool-version', [str(PWSH), '-NoProfile', '-Command',
               "& 'F:/AMD/2025.2/Vivado/bin/xvlog.bat' --version; exit $LASTEXITCODE"], cwd=version):
        return 1
    commands = [
        ('regression', ps + ['simulation/run_regression.ps1', '-VivadoBin', VIVADO,
                            '-OutputDirectory', str(OUT / 'regression')]),
        ('servo-1mhz', ps + ['simulation/run_servo.ps1', '-VivadoBin', VIVADO,
                            '-OutputDirectory', str(OUT / 'servo-1mhz'), '-ClockHz', '1000000']),
        ('h1-fixtures', py + ['scripts/check_h1_fixtures.py']),
        ('skill-examples', py + ['scripts/run_module_skill_examples.py', '--case', 'all',
                                '--vivado-bin', VIVADO, '--output', str(OUT / 'skill-examples')]),
    ]
    okay = True
    for name, command in commands:
        okay = execute(name, command) and okay
    forbidden = ROOT / 'layout-validation-invalid-output-01'
    assert not forbidden.exists()
    okay = execute('negative-regression-noncodex', ps + ['simulation/run_regression.ps1', '-VivadoBin', VIVADO,
                     '-OutputDirectory', str(forbidden)], negative='Use a new directory below repository codex_out') and okay
    assert not forbidden.exists(), 'Invalid output unexpectedly created'
    existing = OUT / 'regression'
    before = tree_hash(existing)
    okay = execute('negative-regression-existing', ps + ['simulation/run_regression.ps1', '-VivadoBin', VIVADO,
                     '-OutputDirectory', str(existing)], negative='Use a new output directory; previous evidence is immutable') and okay
    assert tree_hash(existing) == before, 'Existing evidence changed'
    existing = OUT / 'skill-examples'
    before = tree_hash(existing)
    okay = execute('negative-skill-existing', py + ['scripts/run_module_skill_examples.py', '--case', 'all',
                     '--vivado-bin', VIVADO, '--output', str(existing)],
                     negative='Use a new output directory; previous evidence is immutable') and okay
    assert tree_hash(existing) == before, 'Existing skill evidence changed'
    check_inputs('final')
    save('inputs-after.json', read(OUT / 'inputs-latest.json'))
    manifest = read(OUT / 'run-manifest.json')
    manifest['completed_utc'] = now()
    manifest['all_command_expectations_met'] = okay
    manifest['verdict'] = 'DIAGNOSTIC_ONLY' if okay else 'INCONCLUSIVE'
    save('run-manifest.json', manifest)
    print(json.dumps({'diagnostic': manifest['verdict'], 'all_command_expectations_met': okay}), flush=True)
    return 0 if okay else 1

if __name__ == '__main__':
    if sys.argv[1] == 'preflight':
        preflight()
    elif sys.argv[1] == 'run':
        sys.exit(run())
    elif sys.argv[1] == 'summarize':
        summarize()
