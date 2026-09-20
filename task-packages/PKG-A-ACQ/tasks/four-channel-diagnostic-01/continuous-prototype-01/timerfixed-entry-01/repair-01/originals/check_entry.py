"""Fail-closed C1 timer-fixed entry. Never compiles, connects or downloads.
Only supports the pinned 2025.2/O2/single-TU contract; unsupported input is denied.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import time
import uuid
import zipfile

HERE = Path(__file__).resolve().parent
TASK = HERE.parent
REFERENCE = TASK / 'board-run-20260915-02'
POLICY = json.loads((HERE / 'POLICY.json').read_text(encoding='utf-8'))


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# Reuse, but first bind the helpers themselves to the inspected approved version.
HELPERS = TASK.parent / 'current_build'
for _name, _sha in POLICY['helper_sha256'].items():
    need(digest(HELPERS / _name) == _sha, 'ELF/safety helper changed: ' + _name)
sys.path.insert(0, str(HELPERS))
import build_current as safe
from ps_contract import Elf32

CONTRACT = (0x434f4e31, 0x01000000, 0x01100000, 250, 8, 8000, 64, 8064,
            2, 16128, 0x00100000, 0x3fffffff, 0x40400000, 0x41200000, 10000000, 480000)


def pinned(path, expected):
    path = safe.need_file(path)
    need(digest(path) == expected, 'Unapproved/mismatched file: ' + str(path))
    return path


def symbol(elf, name):
    matches = []
    for section in elf.sections:
        if section[1] != 2:
            continue
        strings = elf.section_data(section[6])
        for offset in range(section[4], section[4] + section[5], 16):
            item = elf.unpack('<IIIBBH', offset)
            if item[5] and elf.string(strings, item[0]) == name:
                matches.append(item)
    need(len(matches) == 1, 'Missing/ambiguous symbol: ' + name)
    item = matches[0]
    section = elf.sections[item[5]]
    offset = (item[1] & ~1) - section[3]
    need(offset >= 0 and offset + item[2] <= section[5], 'Symbol range: ' + name)
    return item[1], elf.section_data(item[5])[offset:offset + item[2]]


def timer_code(elf):
    address, data = symbol(elf, 'now_us')
    need(address & 1 == 0 and len(data) % 4 == 0, 'Unsupported timer instruction mode')
    words = list(struct.unpack('<' + 'I' * (len(data)//4), data))
    calls = []
    for i, word in enumerate(words):
        if word >> 24 not in (0xeb, 0xfa, 0xfb):
            continue
        offset = (word & 0xffffff) << 2
        if offset & (1 << 25):
            offset -= 1 << 26
        target = address + 4*i + 8 + offset
        if word >> 24 in (0xfa, 0xfb):
            target += (word >> 23) & 2
        calls.append(target & ~1)
        words[i] &= 0xff000000
    need(calls == [elf.symbol_value('XTime_GetTime') & ~1,
                   elf.symbol_value('__aeabi_uldivmod') & ~1], 'Timer calls not bound to real callees')
    literal = [i for i, word in enumerate(words[:-1])
               if word == 0xe28f3010 and words[i+1] == 0xe1c320d0]
    need(len(literal) == 1, 'Unsupported timer literal addressing')
    divisor = struct.unpack_from('<Q', data, literal[0]*4 + 8 + 16)[0]
    need(divisor == 333333343, 'Wrong actual timer divisor')
    return words, divisor


def verify_elf(obj_path, elf_path):
    obj, exe = Elf32(obj_path, 1), Elf32(elf_path, 2)
    expected = struct.pack('<16I', *CONTRACT)
    need(symbol(obj, 'continuous_contract')[1] == symbol(exe, 'continuous_contract')[1] == expected,
         'Object/ELF buffer, packet, DDR, duration contract mismatch')
    ref_obj = Elf32(pinned(REFERENCE / 'build/main.c.obj',
                          '8a376d38a7188af5884ce0e6c7eff868a0878d222634ec360cb35961c7cd11ff'), 1)
    ref_exe = Elf32(pinned(REFERENCE / 'runtime/four_mic_continuous.elf', POLICY['archive_elf_sha256']), 2)
    need(symbol(obj, 'now_us')[1] == symbol(ref_obj, 'now_us')[1], 'Object timer code differs from fixed computation')
    actual, divisor = timer_code(exe)
    need(actual == timer_code(ref_exe)[0], 'ELF timer arithmetic differs beyond relocated calls')
    end = exe.symbol_value('end')
    ranges = exe.loads + exe.allocated
    need(end <= CONTRACT[1] and all(CONTRACT[10] <= r['start'] < r['end'] <= CONTRACT[1] for r in ranges),
         'Program/stack/heap outside program DDR or overlapping RX')
    return dict(divisor=divisor, contract=list(CONTRACT), program_end=end, ranges=ranges,
                elf_sha256=digest(elf_path), object_sha256=digest(obj_path))


def launch_paths(app, workspace):
    config = json.loads((app / '_ide/launch.json').read_text(encoding='utf-8'))
    matches = [c for c in config['configurations'] if c['name'] == app.name + '_app_hw_1']
    need(len(matches) == 1, 'Missing/ambiguous selected Vitis Run configuration')
    c = matches[0]
    need(c['type'] == 'tcf-debug' and c['request'] == 'launch'
         and c['target']['targetConnectionId'] == 'Local' and c['target']['context'] == 'zynq',
         'Wrong connection/launch mode')
    t = c['targetSetup']
    init = t['zynqInitialization']
    downloads = t['downloadElf']
    need(c['debugType'] == 'baremetal-zynq' and t['resetSystem'] and t['programDevice']
         and not t.get('partialBitstream') and not init['isFsbl']
         and init['usingPs7Init']['runPs7Init'] and init['usingPs7Init']['runPs7PostInit'], 'Wrong initialization configuration')
    need(len(downloads) == 1 and downloads[0]['core'] == 'ps7_cortexa9_0'
         and downloads[0]['resetProcessor'] and not downloads[0]['stopAtEntry']
         and not downloads[0]['isSelfRelocatingApp'], 'Wrong CPU/download configuration')
    def resolve(value):
        value = value.replace('${workspaceFolder}', str(workspace)).replace('\\', '/')
        need('${' not in value and Path(value).is_absolute(), 'Unresolved/relative load path')
        return safe.need_file(value)
    actual = dict(elf=resolve(downloads[0]['elfFile']), bit=resolve(t['bitstreamFile']),
                  init=resolve(init['usingPs7Init']['ps7InitTclFile']))
    wanted = dict(elf=app/'build'/f'{app.name}.elf', bit=app/'_ide/bitstream/system_continuous_20260915.bit',
                  init=app/'_ide/psinit/ps7_init.tcl')
    need(all(actual[k] == v.resolve() for k,v in wanted.items()), 'Run points to wrong/old artifact path')
    return {k:str(v) for k,v in actual.items()}


def normalize_command(command, app, bsp):
    value = command.replace('\\', '/').casefold()
    for before, after in ((str(app).replace('\\','/').casefold(), '$app'),
                          (str(bsp).replace('\\','/').casefold(), '$bsp')):
        value = value.replace(before, after)
    return ' '.join(value.split())


def verify(args, out):
    app, platform = safe.no_links(args.app), safe.no_links(args.platform)
    need(app.is_dir() and platform.is_dir(), 'Application/platform missing')
    need(app.name == 'four_mic_continuous' and platform.name == 'continuous_platform', 'Unsupported application/platform identity')
    bsp = platform/'export'/platform.name/'sw/standalone_ps7_cortexa9_0'
    for name, sha in POLICY['source_sha256'].items():
        pinned(REFERENCE/'ps'/name, sha)
        pinned(app/'src'/name, sha)
    actual_c = {p.relative_to(app/'src').as_posix() for p in (app/'src').rglob('*')
                if p.suffix.lower() in ('.c','.cpp','.cc','.cxx','.s','.asm','.h','.hpp','.inc')}
    need(actual_c == {'main.c','continuous/main_continuous.c','continuous/continuous_core.c',
                      'continuous/continuous_core.h'}, 'Unexpected source/header/shadowing file')
    # Only the documented append is permitted; no silent changes to generated CMake logic.
    base = (REFERENCE/'ps/CMakeLists.txt').read_text(encoding='utf-8').strip()
    cmake = (app/'src/CMakeLists.txt').read_text(encoding='utf-8').strip()
    if args.stage == 'audit':
        need(cmake == base or cmake == base + '\n\n' + hook_text(), 'CMake differs from base+gate')
    else:
        need(cmake == base + '\n\n' + hook_text(), 'Required CMake guard is missing/changed; do not bypass')
    component = json.loads((app/'vitis-comp.json').read_text(encoding='utf-8'))
    need(component['platform'] == platform.name and component['domain'] == 'standalone_ps7_cortexa9_0'
         and component['cpuInstance'] == 'ps7_cortexa9_0' and component['os'] == 'standalone', 'Application domain mismatch')
    for name, sha in POLICY['bsp_sha256'].items():
        pinned(bsp/name, sha)
    xsa_sha = POLICY['hardware_sha256']['system_continuous_20260915.xsa']
    cfg = json.loads((platform/'vitis-comp.json').read_text(encoding='utf-8'))['configuration']
    pinned(cfg['xsa'], xsa_sha)
    for path in (platform/'hw/system_continuous_20260915.xsa',
                 platform/'export'/platform.name/'hw/system_continuous_20260915.xsa'):
        pinned(path, xsa_sha)
    bit = pinned(app/'_ide/bitstream/system_continuous_20260915.bit', POLICY['hardware_sha256']['system_continuous_20260915.bit'])
    pinned(app/'_ide/psinit/ps7_init.tcl', POLICY['hardware_sha256']['ps7_init.tcl'])
    tools = Path(args.tools_bin).resolve(strict=True)
    for name in ('arm-none-eabi-gcc.exe','arm-none-eabi-objdump.exe'):
        safe.need_tool(tools/name)
    object_path = app/'build/CMakeFiles'/f'{app.name}.elf.dir/main.c.obj'
    report = dict(stage=args.stage, app=str(app), platform=str(platform), bsp=str(bsp),
                  policy_sha256=digest(HERE/'POLICY.json'), source_sha256=POLICY['source_sha256'],
                  bit_sha256=digest(bit), bsp_dependency_files=len(POLICY['bsp_sha256']),
                  fresh_compilation_observed=False, board_test='NOT_RUN')
    if args.stage == 'pre':
        report['prechecked_at_ns'] = time.time_ns()
        report['object_mtime_before_ns'] = object_path.stat().st_mtime_ns if object_path.exists() else None
        return report
    build = app/'build'
    entries = json.loads((build/'compile_commands.json').read_text(encoding='utf-8'))
    need(len(entries) == 1 and Path(entries[0]['file']).resolve() == app/'src/main.c', 'Wrong compiled translation unit')
    need(normalize_command(entries[0]['command'],app,bsp) == normalize_command(POLICY['compile_command'],Path(POLICY['reference_app']),Path(POLICY['reference_bsp'])), 'Compiler/options/includes/specs changed')
    compiler = Path(entries[0]['command'].split(' ')[0]).resolve(strict=True)
    need(compiler == (tools/'arm-none-eabi-gcc.exe').resolve(), 'Tool path mismatch')
    report['compiler_version_output'] = safe.run_command([compiler,'--version'],out,'gcc-version',app)
    report['compiled'] = verify_elf(build/'CMakeFiles'/f'{app.name}.elf.dir/main.c.obj',build/f'{app.name}.elf')
    map_text = (build/'memory.map').read_text(encoding='utf-8')
    found = re.findall(r'0x([0-9a-fA-F]+)\s+end\s*=\s*\.', map_text)
    need(len(found) == 1 and int(found[0],16) == report['compiled']['program_end'], 'Map/end mismatch')
    need(re.search(r'ps7_ddr_0_memory_0\s+0x00100000\s+0x00f00000',map_text), 'Linker program region mismatch')
    loads = [line[5:].strip() for line in map_text.splitlines() if line.startswith('LOAD ')]
    for lib in ('libxil.a','libxilstandalone.a','libxiltimer.a'):
        selected = [Path(s.replace('\\','/')).resolve() for s in loads if s.replace('\\','/').endswith('/'+lib)]
        need(selected == [(bsp/'lib'/lib).resolve()], 'Map links different BSP library: '+lib)
    report['load_paths'] = launch_paths(app, app.parent)
    report['now_us_disassembly'] = safe.run_command([tools/'arm-none-eabi-objdump.exe','-d','--disassemble=now_us',
                                                   build/f'{app.name}.elf'],out,'timer-disassembly',app)
    report['build_inputs'] = {str(p):digest(p) for p in (app/'src').rglob('*') if p.is_file()}
    if args.stage in ('post','load'):
        previous = []
        for path in Path(args.record_root).glob('*/result.json'):
            value = json.loads(path.read_text(encoding='utf-8'))
            if value.get('app') == str(app) and value.get('policy_sha256') == report['policy_sha256']:
                previous.append((path.stat().st_mtime_ns,value,path))
        if args.stage == 'post':
            prior = sorted((x for x in previous if x[1].get('status') == 'PRECHECK_ONLY'),key=lambda x:x[0])
            need(prior, 'Missing successful pre-build record')
            before = prior[-1][1]
            report['precheck_record'] = str(prior[-1][2])
            report['fresh_compilation_observed'] = object_path.stat().st_mtime_ns >= before['prechecked_at_ns']
        else:
            prior = sorted((x for x in previous if x[1].get('stage') == 'post'
                            and x[1].get('status') == 'ARTIFACT_CHECK_PASS_NOT_BOARD'),key=lambda x:x[0])
            need(prior, 'Missing successful guarded post-build record; historical audit is not a build receipt')
            checked = prior[-1][1]
            need(checked['compiled']['elf_sha256'] == report['compiled']['elf_sha256']
                 and checked['compiled']['object_sha256'] == report['compiled']['object_sha256']
                 and checked['build_inputs'] == report['build_inputs'], 'Artifacts/source changed since guarded build')
            report['postcheck_record'] = str(prior[-1][2])
    return report


def hook_text():
    return '# BEGIN C1 TIMERFIX ENTRY\ninclude("' + HERE.as_posix() + '/vitis_gate.cmake")\n# END C1 TIMERFIX ENTRY'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage', required=True, choices=('audit','pre','post','load'))
    for name in ('app','platform','tools-bin','record-root'):
        p.add_argument('--'+name, required=True)
    args = p.parse_args()
    # A fresh child on EVERY invocation retains all rejected inputs/results.
    need(Path(args.record_root).is_absolute(), 'Record root must be absolute')
    root = safe.no_links(args.record_root)
    protected = [Path(args.app)/s for s in ('src','build','_ide')]+[Path(args.platform), REFERENCE, TASK/'delivery-01', HELPERS]
    protected += [p for p in TASK.iterdir() if p.is_dir() and p.resolve() != HERE]
    platform_config = Path(args.platform)/'vitis-comp.json'
    if platform_config.is_file():
        configured_xsa = json.loads(platform_config.read_text(encoding='utf-8'))['configuration']['xsa']
        protected.append(Path(configured_xsa).resolve().parent)  # protect actual one, not just its XSA
    for item in protected:
        item = item.resolve()
        need(not safe.under(root,item) and not safe.under(item,root), 'Evidence overlaps protected input')
    root.mkdir(parents=True,exist_ok=True)
    out = root/(time.strftime('%Y%m%d_%H%M%S')+'_'+args.stage+'_'+uuid.uuid4().hex[:10])
    out.mkdir(exist_ok=False)
    safe.write_json(out/'request.json',vars(args))
    try:
        report = verify(args,out)
        report['status'] = 'PRECHECK_ONLY' if args.stage=='pre' else ('HISTORICAL_ARTIFACT_AUDIT_ONLY' if args.stage=='audit' else 'ARTIFACT_CHECK_PASS_NOT_BOARD')
        safe.write_json(out/'result.json',report)
        print(report['status']+' '+str(out))
    except Exception as exc:
        safe.write_json(out/'failure.json',{'status':'REJECTED','error':str(exc)})
        print('REJECTED '+str(exc)+' EVIDENCE='+str(out),file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
