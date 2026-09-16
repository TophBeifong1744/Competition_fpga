"""Independent source/table/callsite inspection, read-only archived ARM binaries."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

p = argparse.ArgumentParser()
p.add_argument('--repo', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
task = a.repo / 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01'
package = task / 'continuous-prototype-01/endurance-test-01'
sys.path.insert(0, str(task / 'current_build'))
from ps_contract import Elf32

sha = lambda data: hashlib.sha256(data).hexdigest()
src = package / 'evidence/user-build-20260916-2052/app/src'
build = src.parent / 'build'
policy = json.loads((package / 'POLICY.json').read_text())
report = {'scope': 'Independent archive reads only; no checker gate, ARM build or board execution',
          'source_bindings': {}, 'proposed_vs_actual': {}, 'binaries': {}}
for rel, expected in policy['source_text_sha256'].items():
    raw = (src / rel).read_bytes()
    text_sha = sha((src / rel).read_text(encoding='utf-8').replace('\r\n', '\n').encode())
    assert text_sha == expected, rel
    report['source_bindings'][rel] = {'raw_sha256': sha(raw), 'policy_text_sha256': text_sha}
    proposed = package / 'proposed-src' / rel
    if proposed.exists():
        same = proposed.read_bytes() == raw
        assert same, rel
        report['proposed_vs_actual'][rel] = {'raw_equal': same, 'sha256': sha(raw)}


def symbol(e, name):
    found = []
    for sec in e.sections:
        if sec[1] != 2:
            continue
        strings = e.section_data(sec[6])
        for off in range(sec[4], sec[4] + sec[5], 16):
            sym = e.unpack('<IIIBBH', off)
            if sym[5] and e.string(strings, sym[0]) == name:
                found.append(sym)
    assert len(found) == 1, (name, len(found))
    sym = found[0]
    sec = e.sections[sym[5]]
    offset = sec[4] + (sym[1] & ~1) - sec[3]
    return sym, e.data[offset:offset + sym[2]]


expected_profile = [0x454e4431, 1, 300000000, 14400000, 10000000, 480000, 10, 11, 1000000, 2000000]
expected_schedule = [300000000, 14400000] + [10000000, 480000] * 10
paths = [('object', build / 'CMakeFiles/four_mic_endurance.elf.dir/main.c.obj', 1),
         ('elf', build / 'four_mic_endurance.elf', 2)]
for label, path, kind in paths:
    e = Elf32(path, kind)
    profile = list(struct.unpack('<10I', symbol(e, 'endurance_contract')[1]))
    schedule = list(struct.unpack('<22I', symbol(e, 'endurance_schedule')[1]))
    assert profile == expected_profile and schedule == expected_schedule
    main, main_data = symbol(e, 'main')
    timer, timer_data = symbol(e, 'now_us')
    schedule_symbol, unused = symbol(e, 'endurance_schedule')
    row = {'path': str(path), 'sha256': sha(e.data), 'profile': profile, 'schedule': schedule,
           'main_address': main[1], 'main_size': main[2],
           'schedule_address': schedule_symbol[1],
           'timer_address': timer[1], 'timer_size': timer[2],
           'timer_words': [hex(x) for x in struct.unpack('<' + 'I' * (len(timer_data) // 4), timer_data)]}
    if kind == 1:
        relocations = []
        start = main[1] - e.sections[main[5]][3]
        for rel in e.sections:
            if rel[1] != 9 or rel[7] != main[5]:
                continue
            table = e.sections[rel[6]]
            strings = e.section_data(table[6])
            for off in range(rel[4], rel[4] + rel[5], 8):
                location, info = e.unpack('<II', off)
                if start <= location < start + main[2]:
                    target = e.unpack('<IIIBBH', table[4] + (info >> 8) * 16)
                    name = e.string(strings, target[0])
                    if name in ('endurance_schedule', 'session_run_config', 'session_init', 'usleep', '.rodata'):
                        relocations.append({'offset_in_main': location - start, 'type': info & 255, 'symbol': name})
        row['main_schedule_and_call_relocations'] = relocations
        assert any(x['symbol'] == 'session_run_config' for x in relocations)
    else:
        words = struct.unpack('<' + 'I' * (len(main_data) // 4), main_data)
        target_sym, unused = symbol(e, 'session_run_config')
        calls = []
        for i, word in enumerate(words):
            if word >> 24 != 0xeb:
                continue
            delta = (word & 0xffffff) << 2
            if delta & (1 << 25):
                delta -= 1 << 26
            target = main[1] + 4 * i + 8 + delta
            if target == target_sym[1]:
                calls.append({'offset_in_main': 4 * i, 'target': target})
        row['actual_main_calls_to_session_run_config'] = calls
        row['main_literals_equal_schedule_address'] = [i * 4 for i, word in enumerate(words) if word == schedule_symbol[1]]
        low, assembled = {}, []
        for i, word in enumerate(words):
            opcode = word & 0x0ff00000
            register = (word >> 12) & 15
            immediate = ((word >> 4) & 0xf000) | (word & 0xfff)
            if opcode == 0x03000000:
                low[register] = (i, immediate, word)
            elif opcode == 0x03400000 and register in low:
                earlier, lower, earlier_word = low[register]
                value = (immediate << 16) | lower
                assembled.append({'register': register, 'movw_offset': earlier * 4,
                    'movt_offset': i * 4, 'movw_word': hex(earlier_word),
                    'movt_word': hex(word), 'assembled_address': value})
        row['main_movw_movt_addresses'] = assembled
        row['schedule_callsite_words'] = [{'offset': i * 4, 'word': hex(words[i])} for i in range(275, 364)]
        # GCC merged the immutable io initializer immediately before schedule.
        # LDR lr,[pc,#0x120]; two LDMIA lr! of 16 bytes; MOV r9,lr;
        # LDR r3,[r9],#4 leaves r9 at the schedule, passed as r2 at the call.
        assert words[1140 // 4] == 0xe59fe120
        assert words[1172 // 4] == words[1200 // 4] == 0xe8be000f
        assert words[1204 // 4] == 0xe1a0900e and words[1212 // 4] == 0xe4993004
        assert words[1252 // 4] == 0xe1a02009
        pointer = words[(1140 + 8 + 0x120) // 4]
        assert pointer + 36 == schedule_symbol[1]
        row['main_schedule_argument_proof'] = {'literal_offset': 1436, 'io_initializer_address': pointer,
            'postincrement_bytes': 36, 'resulting_r9_and_r2': pointer + 36,
            'endurance_schedule_symbol_address': schedule_symbol[1],
            'session_run_config_call_offset': 1264}
        assert calls
    report['binaries'][label] = row
(a.out / 'result.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({'status': 'PASS_READONLY_SOURCE_AND_SYMBOL_BINDINGS',
                  'source_fields': len(report['source_bindings']),
                  'proposed_files_equal': len(report['proposed_vs_actual']),
                  'binaries': {k: {q: v for q, v in value.items() if q in ('sha256', 'main_schedule_and_call_relocations', 'actual_main_calls_to_session_run_config', 'main_literals_equal_schedule_address')} for k, value in report['binaries'].items()}}, indent=2))
