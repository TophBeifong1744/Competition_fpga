"""Independent TF-B-02 command-only checks. Never compile/link/load firmware."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

p = argparse.ArgumentParser()
p.add_argument('--package', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--gcc', type=Path, required=True)
a = p.parse_args()
package = a.package.resolve()
out = a.output.resolve()
out.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, str(package))
import command_contract as cc
import check_entry as gate

app = Path(gate.POLICY['reference_app'])
bsp = Path(gate.POLICY['reference_bsp'])
norm = lambda s: cc.normalize_command(s, app, bsp)
archived = json.loads((package / 'user-build-20260916-01/verification-01/ninja-commands.json').read_text())['stdout']
original_link = cc.link_command(archived)
needle = '-Wl,"' + app.as_posix() + '/src/lscript.ld"'
assert needle in original_link
replacement = needle[:-1] + ',-L,/../lscript.ld"'
changed = archived.replace(needle, replacement)
assert changed != archived
changed_link = cc.link_command(changed)
report = {
    'scope': 'command parsing/comparison only; no compilation, linking, hardware, or source edits',
    'command_contract_sha256': hashlib.sha256((package / 'command_contract.py').read_bytes()).hexdigest(),
    'cases': [],
}
for before, after in [('-DSDT', '-Dsdt'), ('-U__clang__', '-u__clang__'), ('-O2', '-o2')]:
    original = gate.POLICY['compile_command']
    report['cases'].append({'name': before + ' vs ' + after, 'accepted_as_equal': norm(original) == norm(original.replace(before, after)), 'expected_equal': False})
for left, right in [('gcc -DNAME=Value', 'gcc -DNAME=value'),
                    ('gcc "-DMSG=Hello World"', 'gcc -DMSG=Hello World'),
                    ('gcc -DSTR=F:/AbC', 'gcc -DSTR=f:/abc')]:
    report['cases'].append({'name': left + ' vs ' + right, 'accepted_as_equal': norm(left) == norm(right), 'expected_equal': False})
try:
    accepted = gate.verify_link_output(changed, app, bsp)
    status, error = 'ACCEPTED', None
except Exception as e:
    status, error = 'REJECTED', repr(e)
bad_wl = next(x for x in cc.command_argv(changed_link) if x.startswith('-Wl,') and ',-L,/../' in x)
report['cases'].append({'name': 'Additional -Wl linker arguments hidden by path normalization',
    'original_token': needle, 'changed_token': replacement,
    'normalized_original': list(norm(original_link)), 'normalized_changed': list(norm(changed_link)),
    'normalized_equal': norm(original_link) == norm(changed_link),
    'GCC_linker_argv_from_comma_split': bad_wl[4:].split(','),
    'verify_link_output': status, 'expected': 'REJECTED', 'error': error})

# GCC -### prints subprocess argv without invoking compiler or linker. This
# independent host GCC only demonstrates standard -Wl comma splitting; it is
# not represented as the author's pinned ARM compiler.
dummy_object = out / 'probe.obj'
dummy_object.write_bytes(b'argument fixture only; not an object file\n')
native = [str(a.gcc), '-###', '-Wl,-T', bad_wl, str(dummy_object), '-o', str(out / 'must-not-be-created.exe')]
completed = subprocess.run(native, capture_output=True, text=True)
report['native_gcc_argument_evidence'] = {'argv': native, 'returncode': completed.returncode,
    'stdout': completed.stdout, 'stderr': completed.stderr,
    'output_created': (out / 'must-not-be-created.exe').exists(),
    'limitation': 'Host MinGW GCC -### only; no ARM toolchain, compile, linker, or firmware execution'}

for addition in (' -Wl,-e,0', ' -Wl,--entry=0x01000000', ' -u__clang__', ' -Wl,--defsym,X=1'):
    bad = archived.replace(' -Wl,-Map=memory.map,--cref', ' -Wl,-Map=memory.map,--cref' + addition)
    try:
        gate.verify_link_output(bad, app, bsp)
        status = 'ACCEPTED'
    except ValueError:
        status = 'REJECTED'
    report['cases'].append({'name': 'Ordinary extra link argument ' + addition, 'actual': status, 'expected': 'REJECTED'})

(out / 'result.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
