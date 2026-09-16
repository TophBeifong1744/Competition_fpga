"""Independent, read-only envelope and archived binary checks; no A output overwritten."""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

root = Path(sys.argv[1]).resolve()
scope = 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01'
parent = root / scope
package = parent / 'timerfixed-entry-01'
snap = package / 'user-build-20260916-01'
sha = 'bbe39c38dc36ccb4c0492f492b86f6c46d885fbe'
base = '8371f014711e04553749e6c2ffc29f34b9d5ccc9'
git_path = 'C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
def git(*args):
    return subprocess.check_output([git_path, '-c', 'safe.directory=' + root.as_posix(), '-C', str(root), *args])
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
assert git('rev-parse', 'HEAD').decode().strip() == sha
changes = git('diff', '--name-status', base, sha).decode().splitlines()
assert len(changes) == 88 and all(s.startswith('A\t' + scope + '/timerfixed-entry-01/') for s in changes)
count = 0
for row in git('ls-tree', '-r', '-z', sha, '--', scope + '/timerfixed-entry-01').split(b'\0'):
    if not row: continue
    meta, name = row.split(b'\t', 1)
    data = (root / name.decode()).read_bytes()
    assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == meta.split()[2].decode()
    count += 1
assert count == 88
manifest = json.loads((package / 'DELIVERY-SHA256.json').read_bytes())['files']
assert len(manifest) == 87
assert set(manifest) | {'DELIVERY-SHA256.json'} == {p.relative_to(package).as_posix() for p in package.rglob('*') if p.is_file()}
for name, expected in manifest.items(): assert digest(package / name) == expected, name
historical = json.loads((parent / 'publication/SHA256.json').read_bytes())
for name, expected in historical.items(): assert digest(parent / name) == expected, name
assert len(historical) == 221
assert git('show', base + ':' + scope + '/publication/SHA256.json') == (parent / 'publication/SHA256.json').read_bytes()
binding = json.loads((snap / 'verification-01/snapshot-binding.json').read_bytes())
assert set(binding) == {p.relative_to(snap / 'app').as_posix() for p in (snap / 'app').rglob('*') if p.is_file()}
for name, expected in binding.items(): assert digest(snap / 'app' / name) == expected, name
policy = json.loads((package / 'POLICY.json').read_bytes())
for name, expected in policy['source_sha256'].items():
    assert digest(snap / 'app/src' / name) == digest(parent / 'board-run-20260915-02/ps' / name) == expected
for name, expected in policy['helper_sha256'].items(): assert digest(parent.parent / 'current_build' / name) == expected

sys.path.insert(0, str(parent.parent / 'current_build'))
from ps_contract import Elf32
old = Elf32(parent / 'board-run-20260915-02/runtime/four_mic_continuous.elf', 2)
new = Elf32(snap / 'app/build/four_mic_continuous.elf', 2)
obj = Elf32(snap / 'app/build/CMakeFiles/four_mic_continuous.elf.dir/main.c.obj', 1)
assert hashlib.sha256(new.data).hexdigest() == '726a91fe19fd9b9e67cca6f3c8668bf484df92d1bbb2ec2e5f2619cc0237324c'
assert hashlib.sha256(obj.data).hexdigest() == '0fc486cf671402f1d62041e94e8ec947ebc24961f852114f03ba4baed04f6469'
assert len(old.data) == len(new.data) == 296612
assert old.sections == new.sections and old.section_names == new.section_names
changed = {i for i, (a, b) in enumerate(zip(old.data, new.data)) if a != b}
timestamp_changes = set()
for a, b in [(b'Sep 15 2026\0', b'Sep 16 2026\0'), (b'20:57:08\0', b'18:23:50\0')]:
    assert old.data.count(a) == 1 and new.data.count(b) == 1
    offset = old.data.index(a)
    assert new.data[offset:offset + len(b)] == b
    rodata = new.sections[new.section_names.index('.rodata')]
    assert rodata[4] <= offset < offset + len(a) <= rodata[4] + rodata[5]
    timestamp_changes |= {offset + i for i, (x, y) in enumerate(zip(a, b)) if x != y}
map_text = (snap / 'app/build/memory.map').read_text()
notes = re.findall(r' \.note\.gnu\.build-id\s+0x([0-9a-f]+)\s+0x([0-9a-f]+) linker stubs', map_text)
assert len(notes) == 1
address, size = (int(x, 16) for x in notes[0])
text_sec = new.sections[new.section_names.index('.text')]
offset = text_sec[4] + address - text_sec[3]
assert size == 36 and old.data[offset:offset+16] == new.data[offset:offset+16] == struct.pack('<III', 4, 20, 3) + b'GNU\0'
assert len(timestamp_changes) == 7
assert changed == timestamp_changes | set(range(offset+16, offset+36)) and len(changed) == 27

def symbol(elf, name):
    matches = []
    for section in elf.sections:
        if section[1] != 2: continue
        names = elf.section_data(section[6])
        for offset in range(section[4], section[4] + section[5], 16):
            row = elf.unpack('<IIIBBH', offset)
            if row[5] and elf.string(names, row[0]) == name: matches.append(row)
    assert len(matches) == 1
    row = matches[0]; sec = elf.sections[row[5]]; pos = (row[1] & ~1) - sec[3]
    assert 0 <= pos and pos + row[2] <= sec[5]
    return row[1], elf.section_data(row[5])[pos:pos + row[2]]

expected = (0x434f4e31, 0x01000000, 0x01100000, 250, 8, 8000, 64, 8064, 2, 16128,
            0x00100000, 0x3fffffff, 0x40400000, 0x41200000, 10000000, 480000)
for elf in (obj, new): assert struct.unpack('<16I', symbol(elf, 'continuous_contract')[1]) == expected
assert new.symbol_value('end') == 0x00112640
assert all(0x00100000 <= x['start'] < x['end'] <= 0x00112640 for x in new.loads + new.allocated)
old_obj = Elf32(parent / 'board-run-20260915-02/build/main.c.obj', 1)
assert symbol(obj, 'now_us')[1] == symbol(old_obj, 'now_us')[1]
assert symbol(old, 'now_us') == symbol(new, 'now_us')

sys.path.insert(0, 'F:/NUEC/review-tools/continuous-capstone-5')
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
pc, data = symbol(new, 'now_us')
instructions = list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(data, pc))
loads = [i for i, x in enumerate(instructions) if x.mnemonic == 'ldrd' and x.op_str == 'r2, r3, [r3]']
assert len(loads) == 1
index = loads[0]; addr = instructions[index-1]; call = instructions[index+1]
assert addr.mnemonic == 'add' and addr.op_str.startswith('r3, pc, #')
literal = addr.address + 8 + int(addr.op_str.split('#')[1], 0)
divisor = struct.unpack_from('<Q', data, literal-pc)[0]
assert divisor == 333333343
assert call.mnemonic == 'blx' and int(call.op_str.lstrip('#'), 0) == new.symbol_value('__aeabi_uldivmod') & ~1
assert any(x.mnemonic == 'bl' and int(x.op_str.lstrip('#'), 0) == new.symbol_value('XTime_GetTime') & ~1 for x in instructions)
records = {}
for path in (snap / 'records').glob('*/result.json'):
    value = json.loads(path.read_bytes())
    assert value['policy_sha256'] == digest(package / 'POLICY.json')
    records[value['stage']] = value
assert set(records) == {'pre', 'post', 'load'}
assert records['pre']['object_mtime_before_ns'] is None
assert records['post']['fresh_compilation_observed'] is True
for stage in ('post', 'load'):
    assert records[stage]['compiled']['elf_sha256'] == hashlib.sha256(new.data).hexdigest()
    assert records[stage]['compiled']['object_sha256'] == hashlib.sha256(obj.data).hexdigest()
    assert records[stage]['compiled']['program_end'] == 0x00112640
assert records['post']['build_inputs'] == records['load']['build_inputs']
print(json.dumps({'status': 'PASS_ARCHIVE_ONLY_NOT_ENTRY_APPROVAL', 'review_sha': sha,
    'added_files': count, 'increment_hash_entries': len(manifest), 'historical_hash_entries_unchanged': len(historical),
    'snapshot_files': len(binding), 'fixed_source_files': len(policy['source_sha256']),
    'changed_elf_bytes': len(changed), 'timestamp_bytes': 7, 'gnu_build_id_bytes': 20,
    'gnu_note_address': hex(address), 'other_elf_bytes_identical': True,
    'new_elf_sha256': hashlib.sha256(new.data).hexdigest(), 'new_object_sha256': hashlib.sha256(obj.data).hexdigest(),
    'contract': expected, 'end': hex(new.symbol_value('end')), 'all_allocated_and_load_ranges': new.loads + new.allocated,
    'timer_divisor': divisor, 'literal_address': hex(literal),
    'timer_disassembly': [f'{x.address:08x}: {x.mnemonic} {x.op_str}' for x in instructions if x.address < literal],
    'archived_pre_post_load_records_consistent': True,
    'not_independently_observed': ['A actual BSP and tools', 'actual compilation', 'full original Vitis console', 'actual download or board']}, indent=2))
