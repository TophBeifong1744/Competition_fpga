"""Validate the user-supplied hardware capture without modifying input data."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "reader"))
from h1_reader import ReaderSession

log = (ROOT / "uart_user_supplied.log").read_text(encoding="utf-8")
csv_raw = (ROOT / "samples.csv").read_bytes()
assert not csv_raw.startswith(b"\xef\xbb\xbf"), "CSV BOM"
assert not (ROOT / "metadata.json").read_bytes().startswith(b"\xef\xbb\xbf"), "JSON BOM"
assert csv_raw.decode("utf-8") == log.split("BEGIN_SAMPLES_CSV\n")[1].split("END_SAMPLES_CSV")[0]
record = ReaderSession().load(ROOT)
expected = [[0,257,-513,-32765],[1,-257,-32766,0],[-1,-32767,0,769],[-32768,0,513,-769]]
assert record.sample_ids.tolist() == [0,1,2,3]
assert record.samples.tolist() == expected
assert record.stream_error.tolist() == [0,0,0,0]
assert not record.missing_intervals
assert all(not f for f in record.error_flags)
assert record.direction_policy() == "forbidden_non_acoustic_input"
assert record.metadata["source_kind"] == "hardware-test-pattern"
assert record.metadata["evidence_level"] == "diagnostic"
assert record.metadata["coordinates_m"] is None
assert "sample_rate_hz" in record.metadata["provisional_fields"]
word_lines = re.findall(r"^packet=(\d+) word=(\d+) got=([0-9A-F]+) expected=([0-9A-F]+)$", log, re.M)
assert len(word_lines) == 12
words = []
for i, (p,w,got,exp) in enumerate(word_lines):
    assert (int(p),int(w)) == (i//6,i%6)
    assert got == exp
    words.append(int(got,16))
def signed16(v):
    v &= 65535
    return v-65536 if v >= 32768 else v
for i in range(4):
    sid, w1, w2 = words[3*i:3*i+3]
    assert sid == int(record.sample_ids[i])
    assert [signed16(w1),signed16(w1>>16),signed16(w2),signed16(w2>>16)] == record.samples[i].tolist()
assert re.findall(r"^RX batch=0 packet=(\d) actual_bytes=(\d+)$", log, re.M) == [("0","24"),("1","24")]
assert len(re.findall(r"^DONE batch=0 packet=[01] CR=0x00010003 SR=0x00001002 errors=0x00000000$", log, re.M)) == 2
assert "EXPORT PASS: packets=2 bytes=48 samples=4 errors=0" in log
report = {"status":"PASS_FORMAT_AND_PATTERN", "checks":{"csv_matches_user_log":True,"raw_words_match_csv":True,"independent_golden_match":True,"raw_words":12,"samples":4,"packets":2,"bytes":48}, "reader_sha256":hashlib.sha256((ROOT/"reader/h1_reader.py").read_bytes()).hexdigest(), "reader_summary":record.summary(), "limits":["User-pasted output, not direct UART byte capture.","No acoustic acceptance; nominal rate must not be used as measured timing.","Current file snapshots do not prove loaded hardware/software identity."]}
(ROOT/"validation.json").write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n",encoding="utf-8")
print(json.dumps(report,indent=2,ensure_ascii=False))
