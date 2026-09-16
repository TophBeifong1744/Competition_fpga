"""Strict E1 UART summary/trace audit; not an offline replay of recycled PCM."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def require(condition, message):
    if not condition:
        raise ValueError(message)


def analyze(text):
    lines = iter(line for line in text.splitlines() if line.strip())
    position = 0

    def take(pattern):
        nonlocal position
        position += 1
        line = next(lines, None)
        require(line is not None, f"truncated at nonempty line {position}")
        m = re.fullmatch(pattern, line)
        require(m is not None, f"unexpected line {position}: {line}")
        return m.groups()

    def exact(line):
        return take(re.escape(line))

    exact("Opened with baud rate: 115200")
    exact("FOUR ENDURANCE E1 candidate build Sep 16 2026 20:52:11")
    exact("RX=[01000000,01100000) slot_stride=8064 packet=8000 guard=64 used=16128 end=00113890")
    exact("PROFILE=E1_300S_10X10S long_us=300000000 long_groups=14400000 short_us=10000000 short_groups=480000 short_count=10 gap_us=1000000 timeout_us=2000000")
    exact("One >=300s segment + ten >=10s segments; no PS/PL/DMA reset between; no full audio archive")
    sessions = []
    for n in range(11):
        target, minimum = (300000000, 14400000) if n == 0 else (10000000, 480000)
        exact(f"START session={n} target_us={target} min_groups={minimum} no_UART_until_stop")
        groups, packets, size = map(int, take(
            rf"SESSION {n} result=OK groups=(\d+) packets=(\d+) bytes_checked=(\d+) stop_sent=1"))
        first, last, duration, drain, check, arm = take(
            r"first=([0-9A-F]{16}) last=([0-9A-F]{16}) capture_command_us=(\d+) drain_us=(\d+) max_check_us=(\d+) max_arm_gap_us=(\d+)")
        first, last = int(first, 16), int(last, 16)
        duration, drain, check, arm = map(int, (duration, drain, check, arm))
        require(groups == packets * 250 and size == packets * 8000, f"counts session {n}")
        require(last - first + 1 == groups, f"ID span session {n}")
        require(target <= duration < target + 2000000 and groups >= minimum,
                f"threshold/deadline session {n}")
        require(0 < drain < 2000000, f"drain timeout session {n}")
        gap = None if not sessions else first - sessions[-1]["last_id"] - 1
        require(gap is None or gap >= 0, f"restart ID did not advance session {n}")
        # bad_* are the last examined location/value even on success, not counters.
        bad_group, bad_lane, bad_value = take(
            r"SOURCE=C100000A DMA_SR=00001002 length=8000 active=-1 owners=0,0 bad_group=(\d+) bad_lane=(\d+) bad_value=([0-9A-F]{8})")
        require(int(bad_group) < 250 and int(bad_lane) < 4, "invalid diagnostic cursor")
        exact(f"CHECK first_failure=OK verified_packets={packets} verified_groups={groups} guard_checked_per_verified_packet=1")
        trace = []
        for packet in range(packets - 16, packets):
            source, = take(rf"TRACE packet={packet} slot={packet % 2} SR=00001002 SOURCE=(C1000003|C100000A) length=8000")
            trace.append({"packet": packet, "slot": packet % 2, "source": source})
        channels = []
        for ch in range(4):
            lo, hi, zeros, clips = map(int, take(
                rf"mic{ch} min=(-?\d+) max=(-?\d+) zeros=(\d+) clip_flags=(\d+)"))
            require(-8388608 <= lo < hi <= 8388607, f"range/activity session {n} mic{ch}")
            require(0 <= zeros < groups and 0 <= clips <= groups, "channel counters")
            channels.append({"channel": ch, "min": lo, "max": hi, "zeros": zeros, "clip_flags": clips})
        sessions.append({"session": n, "groups": groups, "packets": packets,
                         "bytes_checked": size, "first_id": first, "last_id": last,
                         "gap_from_previous_last": gap, "capture_command_us": duration,
                         "drain_us": drain, "max_check_us": check, "max_arm_gap_us": arm,
                         "trace": trace, "channels": channels,
                         "first_failure": "OK", "both_slots_free": True,
                         "bad_cursor_not_error_count": [int(bad_group), int(bad_lane), bad_value]})
        if n < 10:
            exact("DRAINED; restart acquisition only in 1s; IDs may gap across this intentional stop")
    exact("ENDURANCE_11_SESSIONS_PASS_NOT_ACCEPTANCE; online checked/recycled, NOT a saved continuous BIN")
    exact("SUMMARY started=11 completed=11 failures=0 normal_between_session_resets=0")
    exact("RUN level LOW; retain logs; no board acceptance or hour-long claim")
    require(next(lines, None) is None, "extra execution/output after end")
    return {"status": "UART_EVIDENCE_CONSISTENT_NOT_ACCEPTANCE", "sessions": sessions,
            "totals": {key: sum(s[key] for s in sessions)
                       for key in ("groups", "packets", "bytes_checked")},
            "clip_flags_total": sum(c["clip_flags"] for s in sessions for c in s["channels"]),
            "limitations": ["UART summaries and last 16 traces per segment, not full PCM replay",
                            "Times are firmware timer readings, not independently calibrated wall time",
                            "Separate segments must not be concatenated into a continuous duration",
                            "Operator confirmation is separate from automated UART parsing"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--out", type=Path, help="new file only; default prints JSON")
    args = parser.parse_args()
    raw = args.log.read_bytes()
    try:
        result = analyze(raw.decode("utf-8-sig"))
    except (ValueError, UnicodeError) as exc:
        result = {"status": "REJECTED", "reason": str(exc)}
    result["log_sha256"] = hashlib.sha256(raw).hexdigest()
    payload = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        with args.out.open("x", encoding="utf-8") as stream:
            stream.write(payload)
        print(result["status"], args.out)
    else:
        print(payload, end="")
    return 1 if result["status"] == "REJECTED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
