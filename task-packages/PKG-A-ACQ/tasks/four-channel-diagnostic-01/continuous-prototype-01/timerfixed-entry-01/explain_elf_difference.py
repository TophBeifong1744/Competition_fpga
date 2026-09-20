"""Explain this build's byte differences using the saved ELF, map and fixed reference."""
import json
import re
import struct
from pathlib import Path
import check_entry as gate

here = Path(__file__).resolve().parent
snapshot = here / 'user-build-20260916-01'
old = gate.Elf32(gate.REFERENCE / 'runtime/four_mic_continuous.elf', 2)
new = gate.Elf32(snapshot / 'app/build/four_mic_continuous.elf', 2)
mapping = (snapshot / 'app/build/memory.map').read_text(encoding='utf-8')
found = re.findall(r' \.note\.gnu\.build-id\s+0x([0-9a-f]+)\s+0x([0-9a-f]+) linker stubs', mapping)
gate.need(len(found) == 1, 'Ambiguous build-id map location')
address, size = (int(v, 16) for v in found[0])
i = new.section_names.index('.text')
section = new.sections[i]
offset = section[4] + address - section[3]
gate.need(new.data[offset:offset+16] == struct.pack('<III', 4, 20, 3) + b'GNU\0', 'Not a GNU build-id note')
gate.need(size == 36 and old.data[offset:offset+16] == new.data[offset:offset+16], 'Note mismatch')
changed = [i for i, (a,b) in enumerate(zip(old.data,new.data)) if a != b]
build_id_positions = set(range(offset+16, offset+36))
r = new.sections[new.section_names.index('.rodata')]
timestamp_positions = {r[4]+v for v in (936,937,939,940,942,943,953)}
gate.need(len(old.data) == len(new.data) and set(changed) == build_id_positions | timestamp_positions,
          'Additional unexplained ELF differences')
gate.need(b'18:23:50\0' in new.data and b'Sep 16 2026\0' in new.data, 'Unexpected new build strings')
result = dict(status='ALL_27_BYTE_DIFFERENCES_EXPLAINED', changed_bytes=len(changed),
              build_id_note_address=hex(address), build_id_changed_bytes=20,
              old_build_id=old.data[offset+16:offset+36].hex(),
              new_build_id=new.data[offset+16:offset+36].hex(),
              timestamp_changed_bytes=7, old_timestamp='Sep 15 2026 20:57:08',
              new_timestamp='Sep 16 2026 18:23:50', instruction_bytes_changed=False)
with (snapshot/'verification-01/elf-difference-explained.json').open('x',encoding='utf-8') as stream:
    json.dump(result,stream,indent=2)
print(json.dumps(result))
