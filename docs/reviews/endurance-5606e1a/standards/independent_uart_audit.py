"""Independent audit of immutable E1 UART, no hardware or author-file writes."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
ENTRY = Path('F:/NUEC/review-worktrees/endurance-5606e1a/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/endurance-test-01')
BOARD = ENTRY / 'board-run-20260916-01'
raw = (BOARD/'endurance_300s_10x10s_20260916_01.log').read_bytes()
text = raw.decode('utf-8-sig')
assert hashlib.sha256(raw).hexdigest() == '6920a852e43f2f6e4f47c2f1a4aefb8c3058ff5d108fc8ec5b4ea80e9cd41fd5'
assert text.count('FOUR ENDURANCE E1 candidate build ') == 1
assert text.count('DRAINED; restart acquisition only in 1s;') == 10
assert 'CONTINUOUS_FAIL' not in text and 'RESET_TIMEOUT' not in text

chunks = re.split(r'(?m)^START session=', text)[1:]
assert len(chunks) == 11
rows = []
for n, chunk in enumerate(chunks):
    lines = chunk.splitlines()
    start = re.fullmatch(r'(\d+) target_us=(\d+) min_groups=(\d+) no_UART_until_stop', lines[0])
    assert start and int(start[1]) == n
    target = 300_000_000 if n == 0 else 10_000_000
    minimum = 14_400_000 if n == 0 else 480_000
    assert (int(start[2]), int(start[3])) == (target, minimum)
    summary = re.search(r'SESSION (\d+) result=(\w+) groups=(\d+) packets=(\d+) bytes_checked=(\d+) stop_sent=(\d+)', chunk)
    assert summary and (int(summary[1]), summary[2], int(summary[6])) == (n, 'OK', 1)
    groups, packets, size = map(int, summary.group(3, 4, 5))
    ids = re.search(r'first=([0-9A-F]{16}) last=([0-9A-F]{16}) capture_command_us=(\d+) drain_us=(\d+) max_check_us=(\d+) max_arm_gap_us=(\d+)', chunk)
    first, last = int(ids[1], 16), int(ids[2], 16)
    duration, drain, check, arm = map(int, ids.group(3, 4, 5, 6))
    assert groups == packets*250 == last-first+1 and size == packets*8000
    assert groups >= minimum and target <= duration < target+2_000_000
    assert 0 < check < drain < 2_000_000 and 0 < arm < 2_000_000
    gap = None if not rows else first-rows[-1]['last_id']-1
    assert gap is None or gap > 0
    state = re.search(r'SOURCE=([0-9A-F]{8}) DMA_SR=([0-9A-F]{8}) length=(\d+) active=(-?\d+) owners=(\d+),(\d+) bad_group=(\d+) bad_lane=(\d+) bad_value=([0-9A-F]{8})', chunk)
    assert state and state.group(1,2,3,4,5,6) == ('C100000A','00001002','8000','-1','0','0')
    # A successful full packet ends at group 249, lane 3; this value is one of
    # mic3's checked samples and must fit its own reported range.
    assert state.group(7,8) == ('249','3')
    last_sample = int(state[9],16)
    if last_sample & 0x80000000:
        last_sample -= 0x100000000
    assert -8388608 <= last_sample <= 8388607
    assert f'CHECK first_failure=OK verified_packets={packets} verified_groups={groups} guard_checked_per_verified_packet=1' in chunk
    traces = re.findall(r'(?m)^TRACE packet=(\d+) slot=(\d+) SR=([0-9A-F]{8}) SOURCE=([0-9A-F]{8}) length=(\d+)', chunk)
    assert len(traces) == 16
    for expected, trace in zip(range(packets-16,packets),traces):
        p, slot, sr, source, length = trace
        assert int(p) == expected and int(slot) == expected%2
        assert sr == '00001002' and source in ('C1000003','C100000A') and length == '8000'
    channels = re.findall(r'(?m)^mic(\d+) min=(-?\d+) max=(-?\d+) zeros=(\d+) clip_flags=(\d+)', chunk)
    assert len(channels) == 4
    statistics = []
    for expected, channel in enumerate(channels):
        c, lo, hi, zeros, clips = map(int,channel)
        assert c == expected and -8388608 <= lo < hi <= 8388607
        assert 0 <= zeros < groups and clips == 0
        if zeros:
            assert lo <= 0 <= hi
        if lo == 0 or hi == 0:
            assert zeros > 0
        if c == 3:
            assert lo <= last_sample <= hi
        statistics.append(dict(channel=c,min=lo,max=hi,zeros=zeros,clip_flags=clips))
    rows.append(dict(session=n,groups=groups,packets=packets,bytes_checked=size,
                     first_id=first,last_id=last,gap_from_previous=gap,
                     capture_command_us=duration,drain_us=drain,max_check_us=check,
                     max_arm_gap_us=arm,final_checked_value_mic3=last_sample,
                     traces=16,channels=statistics))
totals = {key:sum(row[key] for row in rows) for key in ('groups','packets','bytes_checked')}
assert totals == dict(groups=19202750,packets=76811,bytes_checked=614488000)

# Supplemental robustness probes, not modifications of frozen evidence.
spec = importlib.util.spec_from_file_location('e1_author_log_checker', BOARD/'verify_log.py')
parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parser)
mutations = {
    'success_cursor_not_final_group': text.replace('bad_group=249 bad_lane=3', 'bad_group=0 bad_lane=3', 1),
    'success_last_value_outside_signed24': re.sub(r'bad_value=[0-9A-F]{8}', 'bad_value=7FFFFFFF', text, count=1),
    'zeros_in_strictly_positive_range': re.sub(r'mic0 min=-?\d+ max=-?\d+ zeros=\d+', 'mic0 min=1 max=2 zeros=1', text, count=1),
    'ownership_not_drained': text.replace('owners=0,0','owners=1,0',1),
    'drain_timeout': re.sub(r'drain_us=\d+', 'drain_us=2000000', text, count=1),
}
probe_results = {}
for name, changed in mutations.items():
    assert changed != text
    try:
        result = parser.analyze(changed)
        probe_results[name] = {'author_checker':'ACCEPTED','status':result['status']}
    except ValueError as exc:
        probe_results[name] = {'author_checker':'REJECTED','reason':str(exc)}
report = dict(status='INDEPENDENT_FIXED_UART_AUDIT_PASS',log_sha256=hashlib.sha256(raw).hexdigest(),
              totals=totals,segment_count=len(rows),channels_checked=44,sessions=rows,
              supplemental_mutations=probe_results,
              scope='read-only archived UART arithmetic/semantic audit; no PCM replay or hardware operation',
              limits='No external power/reset measurement. A separate operator confirmation and source control flow support the between-segment reset claim. Supplemental parser gaps do not change verified fixed log bytes.')
(ROOT/'independent-uart-result.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(dict(status=report['status'],totals=totals,segment_count=len(rows),channels=44,mutations=probe_results),indent=2,ensure_ascii=False))
