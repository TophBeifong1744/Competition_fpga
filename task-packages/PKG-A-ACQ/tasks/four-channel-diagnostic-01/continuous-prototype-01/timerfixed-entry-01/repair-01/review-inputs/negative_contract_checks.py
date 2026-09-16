"""Offline input-validation regression. Reads ELF files; never executes firmware."""
import json
from pathlib import Path
import struct
import sys

package = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
output.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, str(package))
import check_entry as c

build = package / 'user-build-20260916-01/app/build'
object_path = build / 'CMakeFiles/four_mic_continuous.elf.dir/main.c.obj'
elf_path = build / 'four_mic_continuous.elf'
baseline = c.verify_elf(object_path, elf_path)
original = c.Elf32(elf_path, 2)
rows = []
for name, entry in [('entry_in_reserved_rx', 0x01000000), ('entry_outside_all_loads', 0)]:
    data = bytearray(elf_path.read_bytes())
    struct.pack_into('<I', data, 24, entry)  # ELF32 e_entry field only
    path = output / (name + '.elf')
    path.write_bytes(data)
    assert c.Elf32(path, 2).entry == entry
    try:
        checked = c.verify_elf(object_path, path)
        actual = 'ACCEPTED'
    except Exception as exc:
        actual = 'REJECTED: ' + str(exc)
        checked = None
    rows.append({'case': name, 'expected': 'REJECTED', 'actual': actual,
                 'original_entry': hex(original.entry), 'changed_entry': hex(entry),
                 'entry_in_any_load': any(x['start'] <= entry < x['end'] for x in original.loads),
                 'byte_changes': [i for i, (a,b) in enumerate(zip(original.data, data)) if a != b],
                 'changed_elf_sha256': c.digest(path), 'returned_contract_report': checked})
command = c.POLICY['compile_command']
norm = lambda value: c.normalize_command(value, Path(c.POLICY['reference_app']), Path(c.POLICY['reference_bsp']))
for before, after in [('-DSDT', '-Dsdt'), ('-U__clang__', '-u__clang__')]:
    assert before in command
    altered = command.replace(before, after)
    rows.append({'case': 'case_sensitive_gcc_option', 'before': before, 'after': after,
                 'expected': 'DIFFERENT', 'actual': 'EQUAL' if norm(command) == norm(altered) else 'DIFFERENT'})
result = {'scope': 'REAL_ARCHIVED_OBJECT_AND_ELF_PARSER_ONLY; no compilation, no hardware, no mocks',
          'checker_sha256': c.digest(package / 'check_entry.py'),
          'original_elf_sha256': c.digest(elf_path), 'baseline': baseline, 'cases': rows}
(output / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'baseline': 'PASS', 'cases': [{k:v for k,v in row.items() if k != 'returned_contract_report'} for row in rows]}, indent=2))
assert all(row['actual'] in ('ACCEPTED', 'EQUAL') for row in rows), 'Review result changed; inspect evidence'
