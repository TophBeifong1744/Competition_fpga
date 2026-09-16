"""Independent offline review: no build, original edits, or hardware access.

Cases 1/2 use unmodified checker functions and real archived ARM objects/ELFs.
Case 3 exercises the full verify flow with explicit mocks ONLY for unavailable
BSP/hardware pinning and external gcc/objdump execution. The fixture remaps the
compiler path in memory; it does not change the checker or POLICY.json on disk.
"""
import argparse
import contextlib
import copy
import io
import json
from pathlib import Path
import shutil
import struct
import sys
from unittest.mock import patch


parser = argparse.ArgumentParser()
parser.add_argument('--package', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
package = args.package.resolve()
output = args.output.resolve()
output.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, str(package))
import check_entry as c

snapshot = package / 'user-build-20260916-01/app'
obj = snapshot / 'build/CMakeFiles/four_mic_continuous.elf.dir/main.c.obj'
exe = snapshot / 'build/four_mic_continuous.elf'
original = c.Elf32(exe, 2)
results = {'boundary': 'OFFLINE_ONLY_NO_FIRMWARE_BUILD_NO_BOARD',
           'checker_sha256': c.digest(package / 'check_entry.py'),
           'original_elf_sha256': c.digest(exe), 'original_entry': original.entry,
           'cases': []}

# -Wl,-e,0x01000000 changes the ELF entry without requiring a different section
# or load address. Here a byte mutation isolates exactly that linker property.
modified = output / 'entry-in-rx.elf'
data = bytearray(exe.read_bytes())
struct.pack_into('<I', data, 24, c.CONTRACT[1])
modified.write_bytes(data)
report = c.verify_elf(obj, modified)
results['cases'].append({'name': 'RX entry passes real binary contract checker',
    'expected': 'REJECTED', 'actual': 'ACCEPTED', 'new_entry': c.CONTRACT[1],
    'entry_in_any_load': any(r['start'] <= c.CONTRACT[1] < r['end'] for r in original.loads),
    'binary_byte_changes': sum(a != b for a, b in zip(exe.read_bytes(), data)),
    'compiled_report': report, 'mocks': []})

reference_command = c.POLICY['compile_command']
norm = lambda cmd: c.normalize_command(cmd, Path(c.POLICY['reference_app']), Path(c.POLICY['reference_bsp']))
for before, after in [('-DSDT', '-Dsdt'), ('-O2', '-o2')]:
    changed = reference_command.replace(before, after)
    assert before in reference_command and changed != reference_command
    results['cases'].append({'name': f'Compiler option case {before} -> {after}',
        'expected': 'DIFFERENT', 'actual': 'EQUAL' if norm(changed) == norm(reference_command) else 'DIFFERENT',
        'original_command': reference_command, 'changed_command': changed, 'mocks': []})

# Portable full-flow fixture. All actual source and ARM binary checks stay real.
workspace = output / 'fixture'
app = workspace / 'four_mic_continuous'
platform = workspace / 'continuous_platform'
shutil.copytree(snapshot, app)
platform.mkdir()
bsp = platform / 'export/continuous_platform/sw/standalone_ps7_cortexa9_0'
records = workspace / 'records'
tools = workspace / 'tools'
tools.mkdir()
for name in ('arm-none-eabi-gcc.exe', 'arm-none-eabi-objdump.exe'):
    (tools / name).write_text('NOT AN EXECUTABLE; external execution is mocked\n')
for name in c.POLICY['bsp_sha256']:
    path = bsp / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('UNAVAILABLE BSP TEST FIXTURE\n')
xsa = workspace / 'hardware/system_continuous_20260915.xsa'
xsa.parent.mkdir()
xsa.write_text('UNAVAILABLE HARDWARE TEST FIXTURE\n')
(platform / 'vitis-comp.json').write_text(json.dumps({'configuration': {'xsa': str(xsa)}}))
for rel in ('hw/system_continuous_20260915.xsa', 'export/continuous_platform/hw/system_continuous_20260915.xsa'):
    path = platform / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(xsa, path)
for rel in ('_ide/bitstream/system_continuous_20260915.bit', '_ide/psinit/ps7_init.tcl'):
    path = app / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('UNAVAILABLE HARDWARE TEST FIXTURE\n')
(app / 'src/CMakeLists.txt').write_text((c.REFERENCE / 'ps/CMakeLists.txt').read_text().strip() + '\n\n' + c.hook_text() + '\n')
policy = copy.deepcopy(c.POLICY)
old_compiler = policy['compile_command'].split(' ')[0]
policy['compile_command'] = policy['compile_command'].replace(old_compiler, str(tools / 'arm-none-eabi-gcc.exe'))
command = policy['compile_command'].replace(policy['reference_app'], app.as_posix()).replace(policy['reference_bsp'], bsp.as_posix())
command = command.replace(str(Path(policy['reference_app'])), str(app))
compile_db = [{'directory': str(app / 'build'), 'command': command, 'file': str(app / 'src/main.c')}]
(app / 'build/compile_commands.json').write_text(json.dumps(compile_db))
map_path = app / 'build/memory.map'
map_path.write_text(map_path.read_text().replace(policy['reference_bsp'], bsp.as_posix()))
real_pinned = c.pinned
mocked_checks = []


def fixture_pinned(path, expected):
    path = Path(path).resolve()
    if path.is_relative_to(platform) or path.is_relative_to(xsa.parent) or path.is_relative_to(app / '_ide'):
        c.safe.need_file(path)
        mocked_checks.append(str(path))
        return path
    return real_pinned(path, expected)


def run_stage(stage):
    argv = ['check_entry.py', '--stage', stage, '--app', str(app), '--platform', str(platform),
            '--tools-bin', str(tools), '--record-root', str(records)]
    stdout, stderr = io.StringIO(), io.StringIO()
    with patch.object(sys, 'argv', argv), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        rc = c.main()
    run = {'stage': stage, 'exit_code': rc, 'stdout': stdout.getvalue(), 'stderr': stderr.getvalue()}
    results.setdefault('full_flow', []).append(run)
    assert rc == 0, run
    result_path = Path(stdout.getvalue().strip().split(' ', 1)[1]) / 'result.json'
    return json.loads(result_path.read_text()), result_path


with patch.object(c, 'POLICY', policy), patch.object(c, 'pinned', fixture_pinned), \
        patch.object(c.safe, 'run_command', return_value='MOCKED gcc/objdump, no external tool executed'):
    pre, pre_path = run_stage('pre')
    baseline, baseline_path = run_stage('post')
    run_stage('load')
    # A link-only configuration change is outside build_inputs, and post uses
    # the earlier pre again. There is no new pre invocation or firmware build.
    ninja = app / 'build/build.ninja'
    ninja.write_text(ninja.read_text().replace('  LINK_LIBRARIES = ', '  LINK_FLAGS = -Wl,-e,0x01000000\n  LINK_LIBRARIES = ', 1))
    cache = app / 'build/CMakeCache.txt'
    cache.write_text(cache.read_text() + '\nCMAKE_EXE_LINKER_FLAGS:STRING=-Wl,-e,0x01000000\n')
    map_path.write_text(map_path.read_text() + '\nLOAD CMakeFiles/unapproved_extra.c.obj\n')
    shutil.copyfile(modified, app / 'build/four_mic_continuous.elf')
    wrong_post, wrong_post_path = run_stage('post')
    wrong_load, wrong_load_path = run_stage('load')
    results['cases'].append({'name': 'Link-only entry change plus extra map LOAD passes post/load with reused pre',
        'expected': 'REJECTED', 'actual': [wrong_post['status'], wrong_load['status']],
        'pre_record_reused': wrong_post['precheck_record'] == str(pre_path),
        'new_pre_invocation': False, 'new_compile_or_link': False,
        'entry': c.Elf32(app / 'build/four_mic_continuous.elf', 2).entry,
        'records': [str(wrong_post_path), str(wrong_load_path)]})
    compile_db[0]['command'] = compile_db[0]['command'].replace('-DSDT', '-Dsdt').replace('-O2', '-o2')
    (app / 'build/compile_commands.json').write_text(json.dumps(compile_db))
    bad_options_load, bad_options_path = run_stage('load')
    results['cases'].append({'name': 'Wrong-case compile command passes full load flow',
        'expected': 'REJECTED', 'actual': bad_options_load['status'], 'record': str(bad_options_path)})

results['full_flow_mocks'] = {'pinning_paths': sorted(set(mocked_checks)),
    'external_tools': 'gcc --version and objdump execution mocked; no compiler/linker run',
    'policy': 'Only the compiler executable path in POLICY dictionary remapped; disk original untouched',
    'real_checks': 'source hashes, CMake hook, binary parser/contracts/timer, map, launch paths, pre/post/load records'}
(output / 'result.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
print(json.dumps({'result': str(output / 'result.json'), 'cases': [
    {'name': item['name'], 'expected': item['expected'], 'actual': item['actual']} for item in results['cases']]}, indent=2))
