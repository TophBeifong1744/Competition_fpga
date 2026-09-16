"""Read-only firmware inspection and loader dry-run; never builds or uses XSDB.

Writes new evidence only below the previously copied user-build snapshot.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import check_entry as gate

HERE = Path(__file__).resolve().parent
SNAP = HERE / 'user-build-20260916-01'
OUT = SNAP / 'verification-01'
APP = Path('F:/College/verilog_digital_system/Vitis/four_mic_continuous')
PLATFORM = APP.parent / 'continuous_platform'
TOOLS = 'F:/AMD/2025.2/Vitis/gnu/aarch32/nt/gcc-arm-none-eabi/bin'
TCL = 'F:/AMD/2025.2/tps/win64/git-2.50.0/mingw64/bin/tclsh86.exe'
NINJA = 'F:/AMD/2025.2/Vitis/bin/ninja.exe'


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


def sections(path):
    elf = gate.Elf32(path, 2)
    return {name: (s, None if s[1] == 8 else elf.section_data(i))
            for i, (name, s) in enumerate(zip(elf.section_names, elf.sections))}


def main():
    OUT.mkdir(exist_ok=False)
    try:
        old_path = gate.REFERENCE / 'runtime/four_mic_continuous.elf'
        new_path = APP / 'build/four_mic_continuous.elf'
        old, new = sections(old_path), sections(new_path)
        delta = []
        for name in sorted(set(old) | set(new)):
            a, b = old.get(name), new.get(name)
            if a == b:
                continue
            row = {'section': name, 'old_size': a[0][5] if a else None,
                   'new_size': b[0][5] if b else None,
                   'contents_equal': bool(a and b and a[1] == b[1])}
            if a and b and a[1] is not None and b[1] is not None:
                row['old_sha256'] = hashlib.sha256(a[1]).hexdigest()
                row['new_sha256'] = hashlib.sha256(b[1]).hexdigest()
                if name == '.rodata' and len(a[1]) == len(b[1]):
                    changed = [i for i, (x, y) in enumerate(zip(a[1], b[1])) if x != y]
                    row['changed_offsets'] = changed
                    row['contexts'] = [dict(offset=i,
                        old=repr(a[1][max(0,i-16):i+24]),
                        new=repr(b[1][max(0,i-16):i+24])) for i in changed]
            delta.append(row)
        write('elf-difference.json', dict(old_sha256=gate.digest(old_path),
              new_sha256=gate.digest(new_path), sections=delta))
        # Fail if any copied application artifact changed during inspection.
        copied = {}
        for path in (SNAP / 'app').rglob('*'):
            if path.is_file():
                relative = path.relative_to(SNAP / 'app')
                actual = APP / relative
                gate.need(gate.digest(path) == gate.digest(actual), 'Snapshot changed: ' + str(relative))
                copied[relative.as_posix()] = gate.digest(path)
        write('snapshot-binding.json', copied)
        command = [NINJA, '-C', str(APP / 'build'), '-t', 'commands']
        p = subprocess.run(command, capture_output=True, text=True)
        write('ninja-commands.json', dict(argv=command, returncode=p.returncode, stdout=p.stdout, stderr=p.stderr,
                                         execution='read-only command enumeration; no compilation'))
        gate.need(p.returncode == 0, 'Ninja command enumeration failed')
        # Real Tcl/Python check of real files, with board commands forbidden.
        # Use copied genuine pre/post receipts and write new receipts in this snapshot.
        def quote(value):
            value = str(value).replace('\\', '/')
            gate.need('{' not in value and '}' not in value, 'Unsupported Tcl path')
            return '{' + value + '}'
        commands = '\n'.join('proc ' + name + ' {args} {error "FORBIDDEN hardware command"}'
                             for name in ('connect', 'targets', 'rst', 'fpga', 'dow', 'con'))
        commands += '\nif {[catch {\nsource ' + quote(HERE / 'load_timerfixed.tcl') + '\n'
        commands += 'c1_timerfixed_load ' + ' '.join(map(quote, (
            sys.executable, APP, PLATFORM, TOOLS, SNAP / 'records'))) + '\n} message]} {puts stderr $message; exit 1}\nexit 0\n'
        p = subprocess.run([TCL], input=commands, capture_output=True, text=True)
        write('loader-real-dry-run.json', dict(argv=[TCL], stdin=commands, returncode=p.returncode,
              stdout=p.stdout, stderr=p.stderr, board_test='NOT_RUN'))
        gate.need(p.returncode == 0 and 'DRY_RUN: no connect/reset/program/download' in p.stdout,
                  'Real artifact loader dry-run failed')
        write('result.json', dict(status='USER_BUILD_AND_LOAD_PREFLIGHT_VERIFIED_NOT_BOARD',
                                 new_elf_sha256=gate.digest(new_path), board_test='NOT_RUN'))
        print(p.stdout)
    except Exception as exc:
        write('failure.json', {'status': 'REJECTED', 'error': str(exc)})
        raise


if __name__ == '__main__':
    main()
