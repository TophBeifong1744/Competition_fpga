"""Read-only S1 load preflight composed with the approved 21c141b checks.

Never builds, runs the inherited gate, connects, or downloads. Historical
pre/post records retain their original identities and approval limitations.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
import uuid

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SCENE = HERE.parent
TASK = SCENE.parents[1]
REPO = TASK.parents[3]
S1 = 'batches/background-target-stop-20260917/'
C1 = 'continuous-prototype-01/timerfixed-entry-01/'
REF = 'continuous-prototype-01/board-run-20260915-02/'
MODULES = {
    'command_contract': C1 + 'command_contract.py',
    'ps_contract': 'current_build/ps_contract.py',
    'build_current': 'current_build/build_current.py',
    'check_entry': C1 + 'check_entry.py',
    'timer_layout': 'continuous-prototype-01/endurance-test-01/timer_layout.py',
    'check_scene': S1 + 'check_scene.py',
}
DATA = {S1 + name for name in ('POLICY.json', 'vitis_gate.cmake',
        'delivery-01/versions/build-result.json', 'delivery-01/FINAL-SHA256.json',
        'delivery-01/versions/build/four_mic_endurance.elf')}
DATA |= {C1 + 'POLICY.json'}
DATA |= {REF + name for name in ('ps/CMakeLists.txt', 'ps/lscript.ld',
                                'build/main.c.obj', 'runtime/four_mic_continuous.elf')}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def no_links(value):
    path = Path(os.path.abspath(value))
    for node in (path, *path.parents):
        try:
            info = node.lstat()
        except FileNotFoundError:
            continue
        need(not stat.S_ISLNK(info.st_mode) and
             not getattr(info, 'st_file_attributes', 0) & 0x400,
             'Linked/reparse path is unsupported: ' + str(node))
    return path.resolve()


def digest(path):
    return hashlib.sha256(no_links(path).read_bytes()).hexdigest()


def write_json(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


class Inputs:
    """Record every consumed file; reject input changes during the check."""
    def __init__(self):
        self.hashes = {}

    def file(self, path, sha=None):
        path = no_links(path)
        actual = digest(path)
        need(sha is None or actual == sha, 'Dependency/input mismatch: ' + str(path))
        need(str(path) not in self.hashes or self.hashes[str(path)] == actual,
             'Input changed during preflight: ' + str(path))
        self.hashes[str(path)] = actual
        return path

    def unchanged(self):
        for path, sha in self.hashes.items():
            need(digest(path) == sha, 'Input changed during preflight: ' + path)


def dependencies(inputs, policy):
    pins = policy['dependency_sha256']
    need(set(pins) == set(MODULES.values()) | DATA, 'Incomplete/unexpected dependency closure')
    # Pin the WHOLE closure before any repository Python is imported. The
    # installed gate root differs from this review worktree and stays explicit.
    installed = no_links(policy['installed_task_root'])
    for root in (TASK, installed):
        for name, sha in pins.items():
            inputs.file(root / name, sha)
    for name, relative in MODULES.items():
        path = TASK / relative
        if name in sys.modules:
            need(Path(sys.modules[name].__file__).resolve() == path.resolve(),
                 'Unexpected already-loaded module: ' + name)
            continue
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules['check_scene'], sys.modules['check_entry'], sys.modules['command_contract']


def sources(scene, base, src, installed, inputs):
    for path in base.safe.tree_files(src):
        inputs.file(path)
    hashes = {}
    for name, sha in scene.POLICY['source_text_sha256'].items():
        path = inputs.file(src / name)
        need(scene.text_hash(path) == sha, 'Unsupported S1 source/config: ' + name)
        hashes[name] = digest(path)
    found = {p.relative_to(src).as_posix() for p in src.rglob('*') if p.is_file()
             and p.suffix.lower() in ('.c', '.h', '.s', '.asm', '.cpp', '.cxx', '.cc', '.hpp', '.inc')}
    need(found == scene.EXPECTED_SOURCES, 'Unexpected compiled source/header')
    cmake = (base.REFERENCE / 'ps/CMakeLists.txt').read_text(encoding='utf-8').strip()
    cmake = cmake.replace('set(APP_NAME four_mic_continuous)', 'set(APP_NAME four_mic_endurance)')
    hook = '# BEGIN S1 SCENE ENTRY\ninclude("' + (installed / S1 / 'vitis_gate.cmake').as_posix() + '")\n# END S1 SCENE ENTRY'
    path = inputs.file(src / 'CMakeLists.txt')
    need(path.read_text(encoding='utf-8').strip() == cmake + '\n\n' + hook,
         'Changed S1 CMake body or installed gate path')
    hashes['CMakeLists.txt'] = digest(path)
    return hashes


def commands(scene, contract, compile_command, ninja_output, app, bsp):
    # Keep all four frozen commands, including the complete pre/post gate
    # envelope and allowed independent prerequisite transposition.
    scene.check_commands(compile_command, ninja_output)
    expected = contract.normalize_command(scene.POLICY['compile_command'], app, bsp)
    actual = contract.normalize_command(compile_command, app, bsp)
    need(actual == expected, 'S1 compiler argument contract mismatch')
    expected_link = contract.normalize_command(contract.link_command(scene.POLICY['ninja_commands']), app, bsp)
    actual_link = contract.normalize_command(contract.link_command(ninja_output), app, bsp)
    need(actual_link == expected_link, 'S1 linker argument contract mismatch')
    return dict(compile_argv=list(actual), link_argv=list(actual_link), complete_command_count=4)


def compiled(scene, base, obj, elf):
    result = scene.compiled(obj, elf)
    # Startup instructions/literals contain application link addresses. Use the
    # independently archived S1 image from 8f708e42, pinned before import, not
    # the other application's timerfixed ELF and not a copy of today's input.
    reference = base.Elf32(TASK / S1 / 'delivery-01/versions/build/four_mic_endurance.elf', 2)
    result['startup'] = base.verify_startup(base.Elf32(elf, 2), reference)
    return result


def run(argv, cwd, out, label):
    write_json(out / (label + '.command.json'), dict(argv=list(map(str, argv)), cwd=str(cwd)))
    process = subprocess.run(list(map(str, argv)), cwd=cwd, capture_output=True,
                             text=True, errors='replace', timeout=60, shell=False)
    (out / (label + '.stdout.log')).write_text(process.stdout, encoding='utf-8')
    (out / (label + '.stderr.log')).write_text(process.stderr, encoding='utf-8')
    write_json(out / (label + '.exit.json'), dict(exit_code=process.returncode))
    need(process.returncode == 0, label + ' failed; inspect retained command/logs')
    return process.stdout


def history(scene, policy, inputs, app, platform, report):
    archived = TASK / S1 / 'delivery-01/versions/build-result.json'
    delivery = json.loads((TASK / S1 / 'delivery-01/FINAL-SHA256.json').read_text(encoding='utf-8'))
    need(digest(archived) == delivery['files']['versions/build-result.json'], 'Archived post receipt identity mismatch')
    need(digest(TASK / S1 / 'delivery-01/versions/build/four_mic_endurance.elf') ==
         delivery['files']['versions/build/four_mic_endurance.elf'], 'Archived S1 startup reference identity mismatch')
    post_path = inputs.file(app / policy['historical_post'], digest(archived))
    pre_path = inputs.file(app / policy['historical_pre'], policy['historical_pre_sha256'])
    pre, post = (json.loads(path.read_text(encoding='utf-8')) for path in (pre_path, post_path))
    old_verifier = {name: digest(SCENE / name) for name in ('check_scene.py', 'vitis_gate.cmake')}
    for item, stage, status in ((pre, 'pre', 'S1_PRECHECK_ONLY'),
                                (post, 'post', 'S1_ARTIFACT_PASS_NOT_LOAD_NOT_BOARD')):
        need(item['stage'] == stage and item['status'] == status and
             item['app'] == str(app) and item['platform'] == str(platform), 'Historical receipt identity mismatch')
        need(item['policy_sha256'] == digest(SCENE / 'POLICY.json') and
             item['verifier_sha256'] == old_verifier, 'Historical verifier identity mismatch')
        need(item['source_sha256'] == report['source_sha256'], 'Sources changed since historical build')
    need(Path(post['prior_record']) == pre_path and post['fresh_compilation_observed'] is True,
         'Broken historical pre/post chain')
    for key in ('elf_sha256', 'object_sha256'):
        need(post['compiled'][key] == report['compiled'][key], 'Artifact changed since historical build: ' + key)
    need(post['map_sha256'] == report['map_sha256'], 'Map changed since historical build')
    return dict(pre=str(pre_path), post=str(post_path), archived_post=str(archived),
                pre_sha256=digest(pre_path), post_sha256=digest(post_path),
                original_policy_sha256=post['policy_sha256'], original_verifier_sha256=old_verifier,
                new_build_observed=False, historical_gate_approval='NOT_GRANTED')


def verify(args, out):
    inputs = Inputs()
    inputs.file(HERE / 'check_load.py')
    policy = json.loads(inputs.file(HERE / 'DEPENDENCIES.json').read_text(encoding='utf-8'))
    scene, base, contract = dependencies(inputs, policy)
    app, platform = no_links(args.app), no_links(args.platform)
    need(app == no_links(policy['app']) and platform == no_links(policy['platform']), 'Wrong app/platform path')
    bsp = platform / 'export/continuous_platform/sw/standalone_ps7_cortexa9_0'
    report = dict(stage='load', app=str(app), platform=str(platform), board_test='NOT_RUN',
                  build='NOT_RUN', historical_gate_approval='NOT_GRANTED',
                  approved_dependency_commit=policy['approved_dependency_commit'])
    report['source_sha256'] = sources(scene, base, app / 'src', Path(policy['installed_task_root']), inputs)
    component = json.loads(inputs.file(app / 'vitis-comp.json').read_text(encoding='utf-8'))
    need(component['name'] == scene.APP_NAME and component['platform'] == platform.name and
         component['domain'] == 'standalone_ps7_cortexa9_0' and component['cpuInstance'] == 'ps7_cortexa9_0'
         and component['os'] == 'standalone', 'Wrong app domain')
    for name, sha in base.POLICY['bsp_sha256'].items():
        inputs.file(bsp / name, sha)
    config = json.loads(inputs.file(platform / 'vitis-comp.json').read_text(encoding='utf-8'))
    xsa_sha = base.POLICY['hardware_sha256']['system_continuous_20260915.xsa']
    for path in (config['configuration']['xsa'], platform / 'hw/system_continuous_20260915.xsa',
                 platform / 'export/continuous_platform/hw/system_continuous_20260915.xsa'):
        inputs.file(path, xsa_sha)
    tools = Path(args.tools_bin).resolve(strict=True)
    for path, sha in scene.POLICY['tool_sha256'].items():
        resolved = Path(path).resolve(strict=True)
        need(str(resolved) == scene.POLICY['tool_resolved_paths'][path], 'Tool installation target changed')
        inputs.file(resolved, sha)
    compiler = tools / 'arm-none-eabi-gcc.exe'
    gcc_path = next(p for p in scene.POLICY['tool_sha256'] if p.endswith('/arm-none-eabi-gcc.exe'))
    need(compiler == Path(scene.POLICY['tool_resolved_paths'][gcc_path]),
         'Wrong tools-bin')
    build = app / 'build'
    entries = json.loads(inputs.file(build / 'compile_commands.json').read_text(encoding='utf-8'))
    need(len(entries) == 1 and no_links(entries[0]['file']) == app / 'src/main.c' and
         no_links(entries[0]['directory']) == build, 'Wrong compiled unit/directory')
    inputs.file(build / 'build.ninja')
    # Included Ninja files affect `-t commands`; bind every file under build
    # with the Ninja suffix before invoking that read-only inspection command.
    for path in build.rglob('*.ninja'):
        inputs.file(path)
    ninja_output = run([scene.POLICY['ninja'], '-t', 'commands'], build, out, 'ninja-commands')
    report['commands'] = commands(scene, contract, entries[0]['command'], ninja_output, app, bsp)
    need(Path(contract.command_argv(entries[0]['command'])[0]).resolve(strict=True) == compiler,
         'Compiler path mismatch')
    report['build_graph'] = scene.check_build_graph((build / 'build.ninja').read_text(encoding='utf-8'))
    report['compiler'] = run([compiler, '--version'], app, out, 'compiler-version')
    obj = inputs.file(build / 'CMakeFiles/four_mic_endurance.elf.dir/main.c.obj')
    elf = inputs.file(build / 'four_mic_endurance.elf')
    report['compiled'] = compiled(scene, base, obj, elf)
    map_path = inputs.file(build / 'memory.map')
    mapping = map_path.read_text(encoding='utf-8')
    report['map_sha256'] = digest(map_path)
    ends = re.findall(r'0x([0-9a-fA-F]+)\s+end\s*=\s*\.', mapping)
    need(len(ends) == 1 and int(ends[0], 16) == report['compiled']['program_end'], 'Map/end mismatch')
    need(re.search(r'ps7_ddr_0_memory_0\s+0x00100000\s+0x00f00000', mapping), 'Program region mismatch')
    for lib in ('libxil.a', 'libxilstandalone.a', 'libxiltimer.a'):
        paths = [no_links(s[5:].strip()) for s in mapping.splitlines()
                 if s.startswith('LOAD ') and s.replace('\\', '/').endswith('/' + lib)]
        need(paths == [no_links(bsp / 'lib' / lib)], 'BSP link mismatch: ' + lib)
    report['history'] = history(scene, policy, inputs, app, platform, report)
    inputs.file(app / '_ide/launch.json')
    report['load_paths'] = base.launch_paths(app, app.parent)
    for key, name in (('bit', 'system_continuous_20260915.bit'), ('init', 'ps7_init.tcl')):
        inputs.file(report['load_paths'][key], base.POLICY['hardware_sha256'][name])
    report['disassembly'] = run([tools / 'arm-none-eabi-objdump.exe', '-d', '--disassemble=now_us', elf], app, out, 'timer')
    inputs.unchanged()
    report['input_sha256'] = inputs.hashes
    report['status'] = 'ARTIFACT_CHECK_PASS_NOT_BOARD'
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', required=True, choices=('load',))
    for name in ('app', 'platform', 'tools-bin', 'record-root'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    out = None
    try:
        root = no_links(args.record_root)
        need(Path(args.record_root).is_absolute() and (REPO / 'codex_out') in root.parents,
             'Evidence root must be a child of this checkout/codex_out')
        for protected in (no_links(args.app), no_links(args.platform), HERE):
            need(root != protected and protected not in root.parents and root not in protected.parents,
                 'Evidence overlaps protected input')
        root.mkdir(parents=True, exist_ok=True)
        out = root / (time.strftime('%Y%m%d_%H%M%S') + '_load_' + uuid.uuid4().hex[:10])
        out.mkdir()
        write_json(out / 'request.json', dict(argv=sys.argv, args=vars(args), cwd=os.getcwd(), python=sys.version))
        report = verify(args, out)
        write_json(out / 'result.json', report)
        print(report['status'] + ' ' + str(out))
        return 0
    except Exception as exc:
        if out is not None:
            write_json(out / 'failure.json', dict(status='REJECTED', error=str(exc), board_test='NOT_RUN', build='NOT_RUN'))
        print('REJECTED ' + str(exc) + ' EVIDENCE=' + str(out), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
