"""Read-only checks of this archived run; not independent raw audio validation."""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent.parent / "current_build"))
from ps_contract import Elf32


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contract(elf):
    symbol = elf.symbols["continuous_contract"]
    section = elf.sections[symbol[5]]
    offset = symbol[1] - section[3]
    need(symbol[2] == 64 and offset >= 0, "contract size/range")
    return struct.unpack("<16I", elf.section_data(symbol[5])[offset:offset + 64])


def check():
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        path = ROOT / item["file"]
        need(path.stat().st_size == item["bytes"] and sha(path) == item["sha256"], item["file"])
    exe = Elf32(ROOT / "runtime/four_mic_continuous.elf", 2)
    obj = Elf32(ROOT / "build/main.c.obj", 1)
    expected = (0x434f4e31, 0x01000000, 0x01100000, 250, 8, 8000, 64,
                8064, 2, 16128, 0x00100000, 0x3fffffff, 0x40400000,
                0x41200000, 10000000, 480000)
    need(contract(exe) == contract(obj) == expected, "object/ELF fixed contract")
    need(exe.symbol_value("end") == 0x00112640, "program end")
    need(all(r["end"] <= expected[1] or r["start"] >= expected[2]
             for r in exe.loads + exe.allocated), "program/RX overlap")
    bit_sha = sha(ROOT / "runtime/system_continuous_20260915.bit")
    need(bit_sha == "b15991bc0f8595970361be553b542e334dbb7dca268c01864ecd80fcffbbffaf", "changed bitstream")
    with zipfile.ZipFile(ROOT / "runtime/system_continuous_20260915.xsa") as z:
        bits = [n for n in z.namelist() if n.endswith(".bit")]
        need(len(bits) == 1 and hashlib.sha256(z.read(bits[0])).hexdigest() == bit_sha,
             "XSA/bit mismatch")
    old = (ROOT.parent / "board-run-20260915-01/main_continuous_prefix.c").read_text(encoding="utf-8")
    new = (ROOT / "ps/continuous/main_continuous.c").read_text(encoding="utf-8")
    compact = lambda s: re.sub(r"\s+", "", s)
    need(compact(old.replace("/COUNTS_PER_SECOND;", "/(COUNTS_PER_SECOND);")) == compact(new),
         "unexpected application change")
    for name in ("continuous_core.c", "continuous_core.h"):
        need(sha(ROOT / "ps/continuous" / name) == sha(ROOT.parent / "ps" / name), "changed core: " + name)

    log = (ROOT / "continuous_c1_timerfix_20260915_02.log").read_text(encoding="utf-8")
    need("CONTINUOUS_TWO_SESSIONS_PASS_NOT_ACCEPTANCE" in log and "CONTINUOUS_FAIL" not in log,
         "missing finish or failure present")
    need("build Sep 15 2026 20:57:08" in log and b"20:57:08" in exe.data, "build time mismatch")
    blocks = re.findall(r"^SESSION (\d+) result=(\w+) groups=(\d+) packets=(\d+) bytes_checked=(\d+) stop_sent=(\d+)\n(.*?)(?=^DRAINED|^CONTINUOUS_TWO|\Z)", log, re.M | re.S)
    need(len(blocks) == 2, "session count")
    summaries = []
    previous_last = None
    for index, block in enumerate(blocks):
        sid, result, groups, packets, count, stopped, body = block
        groups, packets, count = int(groups), int(packets), int(count)
        need(int(sid) == index and result == "OK" and stopped == "1", "session result/stop")
        m = re.search(r"first=([0-9A-F]+) last=([0-9A-F]+) capture_command_us=(\d+) drain_us=(\d+) max_check_us=(\d+) max_arm_gap_us=(\d+)", body)
        need(m is not None, "timing fields")
        first, last = (int(m[i], 16) for i in (1, 2))
        capture, drain, check_us, gap_us = (int(m[i]) for i in range(3, 7))
        need(last-first+1 == groups == packets*250 and count == groups*32, "count/ID mismatch")
        need(groups >= 480000 and 10000000 <= capture < 10100000, "duration target")
        # Allow up to two packet periods when comparing local-clock timing and sample count.
        need(abs(groups / 48000 - capture / 1000000) < 500 / 48000, "sample/time mismatch")
        need("SOURCE=C100000A DMA_SR=00001002 length=8000 active=-1 owners=0,0" in body, "final status")
        traces = re.findall(r"^TRACE packet=(\d+) slot=(\d+) SR=([0-9A-F]+) SOURCE=([0-9A-F]+) length=(\d+)$", body, re.M)
        need(len(traces) == 16, "trace tail count")
        for n, (p, slot, sr, source, size) in enumerate(traces, packets-16):
            source = int(source, 16)
            need(int(p) == n and int(slot) == n % 2 and int(sr, 16) == 0x1002 and int(size) == 8000,
                 "trace completion/order/slot")
            need(source & 0xff000000 == 0xc1000000 and source & 0x00ffff24 == 0, "trace source error")
        channels = re.findall(r"^mic(\d) min=(-?\d+) max=(-?\d+) zeros=(\d+) clip_flags=(\d+)$", body, re.M)
        need(len(channels) == 4, "four channel stats")
        for c, (lane, lo, hi, zeros, clips) in enumerate(channels):
            need(int(lane) == c and -8388608 <= int(lo) < 0 < int(hi) <= 8388607
                 and 0 <= int(zeros) <= groups and int(clips) == 0, "channel range/stats")
        gap = None if previous_last is None else first-previous_last-1
        need(gap is None or gap >= 0, "restart ID overlap")
        summaries.append(dict(session=index, groups=groups, packets=packets, bytes_checked=count,
                              first_id=first, last_id=last, gap_from_previous=gap,
                              configured_rate_seconds=groups/48000, capture_command_us=capture,
                              drain_us=drain, max_check_us=check_us, max_arm_gap_us=gap_us))
        previous_last = last

    # Read the actual executable, not a log banner, to confirm the timer divisor.
    objdump = Path("F:/AMD/2025.2/Vitis/gnu/aarch32/nt/gcc-arm-none-eabi/bin/arm-none-eabi-objdump.exe")
    disassembly = subprocess.run([str(objdump), "-d", "--disassemble=now_us",
                                  str(ROOT / "runtime/four_mic_continuous.elf")],
                                 text=True, capture_output=True, check=True).stdout
    need("<now_us>:" in disassembly and "0x13de435f" in disassembly
         and "<__aeabi_uldivmod>" in disassembly, "ELF timer divisor evidence")
    vectors = []
    for seconds in (1, 10, 40):
        ticks = 333333343 * seconds
        old_us = ticks*1000000 // 666666687 // 2
        fixed_us = ticks*1000000 // (666666687 // 2)
        need(fixed_us == seconds*1000000 and old_us != fixed_us, "timer arithmetic regression")
        vectors.append(dict(seconds=seconds, old_us=old_us, fixed_us=fixed_us))
    return dict(result="PASS_ARCHIVED_EVIDENCE_CHECK_NOT_ACCEPTANCE", sessions=summaries,
                files_sha256_verified=len(manifest["files"]), object_elf_contract_match=True,
                program_end="0x00112640", rx_used_bytes=16128,
                timer_divisor_in_elf=333333343, timer_arithmetic_vectors=vectors,
                limitations=["No full raw continuous audio retained; per-group correctness relies on PS online checks.",
                             "Two sessions with one acquisition restart, not one continuous 20-second recording.",
                             "No independent wall-clock calibration, board fault injection or new RTL simulation.",
                             "No independent reviewer acceptance, one-hour or acoustic performance claim."],
                timer_disassembly=disassembly)


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))
