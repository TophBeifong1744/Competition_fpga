"""Independent integer/causal checker with in-memory negative canaries.

Does not import the DUT or its leaves. It compares the independent arithmetic
reference, predeclared event schedule and audio coordinates to CLI artifacts.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

import numpy as np


class CheckFailure(Exception):
    pass


def require(condition, label):
    if not condition:
        raise CheckFailure(label)


def first_array_difference(observed, expected, name):
    require(observed.shape == expected.shape, name + ":SHAPE")
    require(observed.dtype == expected.dtype, name + ":DTYPE")
    mismatches = np.argwhere(observed != expected)
    if len(mismatches):
        index = tuple(map(int, mismatches[0]))
        raise CheckFailure("NUMERIC_FIRST_DIFFERENCE:" + name + ":" + str(index)
                           + ":expected=" + str(expected[index])
                           + ":observed=" + str(observed[index]))


def manual_reference(pcm, rom, angle_q8):
    delays = (0,) + tuple(map(int, rom[angle_q8 + 46080]))
    count = pcm.shape[1]
    output = np.zeros(count, dtype=np.int64)
    q = 4096
    for n in range(count):
        weighted = 0
        for ch, delay in enumerate(delays):
            position, fraction = divmod(n * q - delay, q)
            left = int(pcm[ch, position]) if 0 <= position < count else 0
            right = int(pcm[ch, position + 1]) if fraction and 0 <= position + 1 < count else 0
            weighted += (q - fraction) * left + fraction * right
        # nearest even with explicit sign handling
        magnitude, remainder = divmod(abs(weighted), 4 * q)
        if 2 * remainder > 4 * q or (2 * remainder == 4 * q and magnitude % 2):
            magnitude += 1
        output[n] = -magnitude if weighted < 0 else magnitude
    return output


def compare(result, arrays, expected, fixture, repo, manual_angle_q8):
    checked = []
    for name in expected.files:
        require(name in arrays, "MISSING_ARRAY:" + name)
        first_array_difference(arrays[name], expected[name], name)
        checked.append(name)
    require(result["claim"] == "PORTABLE_RESEARCH_CONFIG_ONLY", "CLAIM")
    require(result["time_basis"] == "SYNTHETIC_TIME", "TIME_BASIS")
    require(result["status"] == "COMPLETED", "NORMAL_RUN_STATUS")
    require(result["planned_frames"] == 7 and len(result["frames"]) == 7,
            "FRAME_COUNT")
    require(len(result["stage_details"]) == 7, "STAGE_COUNT")
    expected_units = None
    fresh = 0
    ifft_success = 0
    for i, row in enumerate(result["frames"]):
        detail = result["stage_details"][i]
        units = detail["units"]
        if expected_units is None:
            expected_units = set(detail["expected"])
            require(len(expected_units) == len(detail["expected"]), "DUPLICATE_EXPECTED")
        require(set(detail["expected"]) == expected_units and set(units) == expected_units,
                "UNIT_CLOSURE:" + str(i))
        require(all(value != "PENDING" for value in units.values()), "PENDING_UNIT:" + str(i))
        require(row["frame"] == i and row["last_id"] == 1023 + i * 512,
                "FRAME_IDENTITY:" + str(i))
        schedule = fixture["frames"][i]
        require((row["available"], row["commit"], row["take"], row["expiry"]) ==
                (schedule["available"], schedule["commit_now"], schedule["take_now"],
                 row["last_id"] + fixture["result_ttl_samples"]), "EVENT_TIMING:" + str(i))
        require(row["last_id"] < row["available"] <= row["commit"] <= row["take"] <= row["expiry"],
                "CAUSAL_ORDER:" + str(i))
        require(row["external_visible"] == schedule["external_visible_at"],
                "EXTERNAL_STATUS_IDENTITY:" + str(i))
        require(row["external_errors"] == [], "UNEXPECTED_EXTERNAL_ERROR:" + str(i))
        for domain in ("gate", "doa"):
            for ch in range(4):
                require(units[f"{domain}_fft_{ch}"] == "OK" and
                        units[f"{domain}_fixed4_{ch}"] == "OK",
                        "FORWARD_UNIT:" + str(i))
        active = i >= 2
        require(bool(detail["detail"]["gate_state"]["active"]) == active,
                "GATE_ATTACK:" + str(i))
        require(not row["invalid"] and not detail["detail"]["numeric_invalid"],
                "NUMERIC_INVALID:" + str(i))
        for pair in ("01", "02", "03", "12", "13", "23"):
            if not active:
                require(all(units[f"{kind}_{pair}"] == "SKIPPED_GATE_CLOSED"
                            for kind in ("phat", "ifft", "lag")), "GATE_CLOSED_SKIP:" + str(i))
            else:
                require(units[f"phat_{pair}"] == "OK" and units[f"ifft_{pair}"] == "OK",
                        "ACTIVE_PAIR:" + str(i) + ":" + pair)
                ifft_success += 1
        doa = detail["detail"]["doa"]
        if active:
            require(doa["valid"] and doa["reason"] == "VALID", "DOA_QUALIFICATION:" + str(i))
            require(abs(doa["azimuth_q8_deg"]) <= 8 * 256,
                    "SYNTHETIC_X_AXIS_ANGLE:" + str(i))
            require(detail["detail"]["cordic"] == "OK_NORMALIZED_S23", "CORDIC:" + str(i))
        else:
            require(not doa["valid"] and row["state"] == "SEARCH" and not row["fresh"],
                    "CLOSED_GATE_FRESH:" + str(i))
        if i == 2:
            require(row["state"] == "ACQUIRE" and not row["fresh"] and
                    row["control"]["state"] == "SEARCH", "ACQUIRE_MUST_NOT_FRESH")
        if i >= 3:
            require(row["state"] == "LOCKED" and row["fresh"] and
                    row["control"]["state"] == "LOCKED", "LOCKED_FRESH:" + str(i))
            fresh += 1
        require(row["control"]["emit"] == row["take"], "CONTROL_EMIT_TIME:" + str(i))
    require(ifft_success == 30 and fresh == 4, "POSITIVE_COVERAGE")
    events = result["events"]
    for i, schedule in enumerate(fixture["frames"]):
        event_rows = [event for event in events if event["frame"] == i]
        take = [event for event in event_rows if event["unit"] == "take"]
        require(len(take) == 1 and take[0]["visible_at"] == schedule["take_now"] and
                take[0]["result"] == ("TAKEN_FRESH" if i >= 3 else "TAKEN_NO_FRESH"),
                "TAKE_EVENT:" + str(i))
        require(len([event for event in event_rows if event["unit"] in schedule["external_visible_at"]])
                == len(schedule["external_visible_at"]), "MISSING_OR_DUPLICATE_STATUS:" + str(i))
    pcm = np.load(repo["pcm_path"], allow_pickle=False)
    count = pcm.shape[1]
    audio = result["audio"]
    require(audio["source_count"] == count and audio["aborted_at_emit"] is None,
            "AUDIO_SOURCE_COUNT")
    for lane in ("single", "manual", "automatic"):
        require(arrays["audio_" + lane].shape == (count,), "AUDIO_LENGTH:" + lane)
    require(arrays["audio_automatic_raw"].shape == (count + 8,), "RAW_EMIT_LENGTH")
    first_fresh_emit = result["frames"][3]["take"]
    first_affected_source = first_fresh_emit - 8
    first_array_difference(arrays["audio_single"], pcm[0], "audio_single_source_coordinate")
    first_array_difference(arrays["audio_automatic_raw"][8:8 + count],
                           arrays["audio_automatic"], "audio_emit_plus_8")
    first_array_difference(arrays["audio_automatic"][:first_affected_source],
                           pcm[0, :first_affected_source], "audio_before_first_fresh")
    rom_path = repo["root"] / repo["delay_path"]
    require(hashlib.sha256(rom_path.read_bytes()).hexdigest() == repo["delay_sha"],
            "DELAY_ROM_IDENTITY")
    rom = np.load(rom_path, allow_pickle=False)
    first_array_difference(arrays["audio_manual"], manual_reference(pcm, rom, manual_angle_q8),
                           "manual_fixed_angle_q12")
    require(audio["stats"]["max_beams"] <= 2 and audio["stats"]["max_history"] <= 17,
            "DYNAMIC_RESOURCE_BOUND")
    return {"compared_arrays": len(checked), "frames": 7, "fresh": fresh,
            "conditional_ifft": ifft_success, "first_fresh_emit": first_fresh_emit,
            "audio_sources": count}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--fixture", type=Path, required=True)
    ap.add_argument("--reference", type=Path, required=True)
    ap.add_argument("--result", type=Path, required=True)
    ap.add_argument("--manual-angle-q8", type=int, required=True)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    require(not a.out.exists(), "OUTPUT_EXISTS")
    schedule = json.loads((a.fixture / "schedule.json").read_text())
    manifest = json.loads((a.repo / "models/python/soundsight_h3_portable/tables/source-manifest.json").read_text())
    drom = manifest["entries"]["delay_rom"]
    context = {"root": a.repo, "pcm_path": a.fixture / "pcm.npy",
               "delay_path": drom["path"], "delay_sha": drom["sha256"]}
    result = json.loads((a.result / "result.json").read_text())
    with np.load(a.result / "stages-and-audio.npz", allow_pickle=False) as source:
        arrays = {name: source[name].copy() for name in source.files}
    with np.load(a.reference / "expected-stages.npz", allow_pickle=False) as source:
        expected = {name: source[name].copy() for name in source.files}
    class ArrayView:
        files = list(expected)
        def __getitem__(self, key):
            return expected[key]
    summary = compare(result, arrays, ArrayView(), schedule, context, a.manual_angle_q8)
    negatives = {}
    if a.self_test:
        experiments = ("NUMERIC", "FRESH", "EVENT", "AUDIO")
        for kind in experiments:
            result_copy = copy.deepcopy(result)
            array_copy = dict(arrays)
            if kind == "NUMERIC":
                array_copy["frame0000_doa_fft29"] = arrays["frame0000_doa_fft29"].copy()
                array_copy["frame0000_doa_fft29"][0, 7, 0] += 1
            elif kind == "FRESH":
                result_copy["frames"][2]["fresh"] = True
            elif kind == "EVENT":
                result_copy["events"] = [row for row in result_copy["events"]
                                         if not (row["frame"] == 3 and row["unit"] == "take")]
            else:
                array_copy["audio_automatic"] = arrays["audio_automatic"].copy()
                array_copy["audio_automatic"][0] += 1
            try:
                compare(result_copy, array_copy, ArrayView(), schedule, context,
                        a.manual_angle_q8)
            except CheckFailure as error:
                negatives[kind] = str(error)
            else:
                raise CheckFailure("NEGATIVE_CANARY_NOT_DETECTED:" + kind)
    a.out.mkdir()
    output = {"status": "CHECKER_PASS_SCOPE_ONLY", "positive": summary,
              "negative_canaries": negatives,
              "reference_is_independent_of_dut_import": True,
              "not_claimed": ["SNR", "real activity truth", "RTL timing", "production profile"]}
    (a.out / "checker-result.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output))


if __name__ == "__main__":
    try:
        main()
    except (CheckFailure, AssertionError, ValueError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
