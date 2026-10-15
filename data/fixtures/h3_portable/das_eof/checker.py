"""Standalone evidence checker with stable, canary-targetable failure categories."""
import argparse
import json
from pathlib import Path

import numpy as np

from reference import expected_units, lanes, FRESH_EMITS

HERE = Path(__file__).resolve().parent


class Failure(Exception):
    pass


def require(value, category, detail):
    if not value:
        raise Failure(category + ": " + detail)


def equal(actual, expected, category, detail):
    require(actual == expected, category, f"{detail}; expected={expected!r}, observed={actual!r}")


def check_angles(path):
    observed = json.loads(path.read_text(encoding="utf-8"))["angle_samples"]
    expected = json.loads((HERE / "accepted-exact-samples.json").read_text(encoding="utf-8"))["angle_rom_samples"]
    equal(len(expected), 6, "ANGLE_COUNT", "accepted literal must have six")
    equal(len(observed), 6, "ANGLE_COUNT", "observed table must have six")
    equal([r["angle_deg"] for r in observed], [-180, -90, -45, 0, 45, 90], "ANGLE_IDENTITY", "angle ordering")
    for i in range(6):
        for field in ("delays_q12", "beam", "source_n", "emit"):
            equal(observed[i][field], expected[i][field], "ANGLE_VALUE", f"row{i}.{field}")


def check_case(result_path, arrays_path, schedule_path, pcm_path, long):
    result = json.loads(result_path.read_text(encoding="utf-8"))
    schedule = json.loads(schedule_path.read_text(encoding="utf-8"))
    pcm = np.load(pcm_path, allow_pickle=False)
    origin = schedule["first_sample_id"]
    width = pcm.shape[1]
    stop = schedule.get("stop_emit")
    fatal = schedule.get("fatal_emit")
    end = origin + width + 8
    edge = min(x for x in (stop, fatal) if x is not None) if stop is not None or fatal is not None else None
    edge_reason = "FATAL" if fatal is not None and fatal == edge else "STOP"
    equal(result["claim"], "PORTABLE_RESEARCH_CONFIG_ONLY", "EOF_AUDIT", "limited claim")
    equal(result["time_basis"], "SYNTHETIC_TIME", "EOF_AUDIT", "time basis")
    equal(result["first_sample_id"], origin, "EOF_AUDIT", "absolute origin")
    equal(result["status"], "ABORTED" if fatal is not None else "COMPLETED", "EOF_AUDIT", "status")
    frames = result["frames"]
    count = 7 if long else 1
    equal(result["planned_frames"], count, "HISTORY", "planned frame count")
    equal(len(frames), count, "HISTORY", "all frames retained")
    terms = result["terminations"]
    equal(len(terms), count, "HISTORY", "one termination per frame")
    units = expected_units()
    equal(len(units), 53, "HISTORY", "required instance count")
    for i in range(count):
        timing = schedule["frames"][i]
        take = timing["take_now"]
        commit = timing["commit_now"]
        available = timing["available"]
        cancelled = edge is not None and edge <= take
        identity = {"boot": schedule["boot_id"], "session": schedule["session_id"],
                    "interval": schedule["interval_id"], "frame": i,
                    "generation": schedule["generation"], "last_id": origin + 1023 + i * 512}
        frame, term = frames[i], terms[i]
        for field, expected in {"frame": i, "last_id": identity["last_id"], "available": available,
                                "commit": commit, "take": take,
                                "expiry": identity["last_id"] + schedule["result_ttl_samples"]}.items():
            equal(frame[field], expected, "HISTORY", f"frame{i}.{field}")
        equal(term["identity"], identity, "HISTORY", f"termination{i} identity")
        equal(term["time_basis"], "SYNTHETIC_TIME", "HISTORY", f"termination{i} time basis")
        equal(term["expected_units"], units, "HISTORY", f"termination{i} required IDs")
        prior = set(term["final_before"])
        cancelled_ids = term["cancelled_units"]
        require(len(cancelled_ids) == len(set(cancelled_ids)) and not prior.intersection(cancelled_ids)
                and prior.union(cancelled_ids) == set(units), "HISTORY", f"termination{i} exact partition")
        equal(term["ever_committed"], edge is None or commit < edge, "HISTORY", f"termination{i} committed history")
        equal(term["ever_taken"], not cancelled, "HISTORY", f"termination{i} take history")
        equal(term["successful_commit_at"], commit if edge is None or commit < edge else None, "HISTORY", f"termination{i} commit coordinate")
        if edge is None or commit < edge:
            equal(term["final_before"]["result_binding"], "BOUND_FRESH" if long and i >= 3 else "BOUND_NO_FRESH",
                  "HISTORY", f"termination{i} final committed binding status")
        equal(term["successful_take_at"], None if cancelled else take, "HISTORY", f"termination{i} take coordinate")
        equal(term["prior_binding_retracted"], False, "HISTORY", f"termination{i} immutable binding")
        equal(term["later_interval_end_at"], edge if edge is not None and edge > take else None, "HISTORY", f"termination{i} later edge")
        equal(term["later_interval_end_reason"], edge_reason if edge is not None and edge > take else None, "HISTORY", f"termination{i} later reason")
        equal(term["at"], edge if cancelled else take, "HISTORY", f"termination{i} coordinate")
        if cancelled:
            reason = edge_reason + ("_BEFORE_AVAILABLE" if edge <= available else "_BEFORE_COMMIT" if edge <= commit else "_BEFORE_TAKE")
            equal(term["reason"], reason, "HISTORY", f"termination{i} reason")
            equal(frame["fresh"], False, "HISTORY", f"frame{i} cancelled fresh")
            equal(frame["state"], "CANCELLED" if edge_reason == "FATAL" else "STOPPED", "HISTORY", f"frame{i} cancellation")
            equal(frame["suppressed"], ["FRAME_TAKE_CANCELLED_BY_" + edge_reason], "HISTORY", f"frame{i} suppressed")
            if commit < edge:
                equal(term["final_before"]["result_binding"], "BOUND_FRESH" if long and i >= 3 else "BOUND_NO_FRESH",
                      "HISTORY", f"termination{i} earlier binding status retained")
            if long and i >= 3 and available < edge:
                equal(frame["prior_tracker"]["angle_q8_deg"], 0, "HISTORY", f"frame{i} retained prior angle")
                equal(frame["prior_tracker"]["fresh_valid"], True, "HISTORY", f"frame{i} earlier tracker retained")
        else:
            equal(term["reason"], "TAKE_COMPLETE", "HISTORY", f"termination{i} completed reason")
            equal(frame["fresh"], bool(long and i >= 3), "HISTORY", f"frame{i} fresh identity")
            state = "SEARCH" if not long or i < 2 else "ACQUIRE" if i == 2 else "LOCKED"
            equal(frame["state"], state, "HISTORY", f"frame{i} state")
            equal(frame["invalid"], False, "HISTORY", f"frame{i} invalid")
            equal(frame["suppressed"], [], "HISTORY", f"frame{i} suppression")
            equal(cancelled_ids, [], "HISTORY", f"termination{i} no cancellation")
            if long and i >= 3:
                equal(frame["tracker"]["angle_q8_deg"], 0, "HISTORY", f"frame{i} accepted fixture angle")
                equal(frame["control"], {"emit": FRESH_EMITS[i - 3], "state": "LOCKED", "delays": [0, 22928, 22928, 0],
                                         "valid_through": timing["audio_valid_through_emit"] - origin}, "HISTORY", f"frame{i} fresh control")
    # Successful numeric/binding/take history is judged separately from EOF.
    takes = [e for e in result["events"] if e["unit"] == "take"]
    expected_takes = [{"frame": i, "unit": "take", "visible_at": row["take_now"],
                       "result": "TAKEN_FRESH" if long and i >= 3 else "TAKEN_NO_FRESH"}
                      for i, row in enumerate(schedule["frames"]) if edge is None or row["take_now"] < edge]
    equal(takes, expected_takes, "HISTORY", "complete successful take events")
    for event in result["events"]:
        require(edge is None or event["visible_at"] < edge, "HISTORY", "no same/later edge publication")
    # Check the complete public sequence, including earlier external completion,
    # tracker and binding events. This detects dropped/duplicated/relabelled
    # history in addition to checking the eventual termination records.
    queue = []
    for i, row in enumerate(schedule["frames"]):
        for unit, at in row["external_visible_at"].items():
            queue.append((at, 0, i, unit, "OK"))
        queue += [(row["available"], 2, i, "tracker", "OK_FRESH" if long and i >= 3 else "OK_NO_FRESH"),
                  (row["commit_now"], 3, i, "result_binding", "BOUND_FRESH" if long and i >= 3 else "BOUND_NO_FRESH"),
                  (row["take_now"], 4, i, "take", "TAKEN_FRESH" if long and i >= 3 else "TAKEN_NO_FRESH")]
    expected_events = [{"frame": i, "unit": unit, "visible_at": at, "result": outcome}
                       for at, _priority, i, unit, outcome in sorted(queue) if edge is None or at < edge]
    equal(result["events"], expected_events, "HISTORY", "complete ordered public event history")
    if stop == end:
        audit = {"identity": {"boot": schedule["boot_id"], "session": schedule["session_id"],
                              "interval": schedule["interval_id"], "generation": schedule["generation"]},
                 "time_basis": "SYNTHETIC_TIME", "at": end, "reason": "STOP_AT_EOF",
                 "effective": fatal is None or stop < fatal,
                 "superseded_by": None if fatal is None or stop < fatal else {"reason": "FATAL", "at": fatal},
                 "renderer_control_emitted": False, "termination_frames": list(range(count))}
        equal(result.get("eof_stop_audit"), audit, "EOF_AUDIT", "exact public EOF audit")
    else:
        require("eof_stop_audit" not in result, "EOF_AUDIT", "no fabricated EOF audit")
    actual = np.load(arrays_path, allow_pickle=False)
    expected = lanes(pcm, long=long, stop=None if stop is None else stop - origin,
                     fatal=None if fatal is None else fatal - origin)
    for name, values in expected.items():
        key = "audio_" + name
        require(key in actual.files, "PCM", "missing " + key)
        observed = actual[key]
        require(observed.ndim == 1 and len(observed) == len(values), "PCM", name + " length")
        expected_array = np.asarray(values, dtype=np.int64)
        mismatch = np.flatnonzero(observed != expected_array)
        require(not len(mismatch), "PCM", f"{name} first mismatch {int(mismatch[0]) if len(mismatch) else None}")
    equal(result["audio"]["source_count"], len(expected["single"]), "PCM", "source length")
    # The renderer has no emission at E. At that absolute cancellation edge
    # the interval is ABORTED, but its already-finished local renderer has no
    # stopped emission to report. This field is an observation of local render
    # termination, not the public interval-end coordinate.
    local_abort = fatal - origin if fatal is not None and fatal < end else None
    equal(result["audio"]["aborted_at_emit"], local_abort, "PCM", "local fatal coordinate")
    require(not any(e["kind"] == "STOP" and e["emit"] == width + 8 for e in result["audio"]["events"]),
            "EOF_AUDIT", "no EOF renderer control")
    return {"case": result_path.parent.name, "frames": count, "fresh": sum(f["fresh"] for f in frames),
            "raw_samples": len(expected["automatic_raw"]), "all_lane_codes_checked": sum(map(len, expected.values()))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--angles", type=Path)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--arrays", type=Path)
    parser.add_argument("--schedule", type=Path)
    parser.add_argument("--pcm", type=Path)
    parser.add_argument("--long", action="store_true")
    args = parser.parse_args()
    try:
        if args.angles:
            check_angles(args.angles)
            summary = {"six_angles_checked": 6}
        else:
            summary = check_case(args.result, args.arrays, args.schedule, args.pcm, args.long)
        print(json.dumps({"status": "CHECKED_PENDING_NONAUTHOR_REVIEW", **summary}))
        return 0
    except Failure as exc:
        print(json.dumps({"status": "REJECTED", "category": str(exc).split(":", 1)[0], "detail": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
