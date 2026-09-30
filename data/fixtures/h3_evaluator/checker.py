"""Independent report checker. Exit nonzero on any discrepancy."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fail(message):
    raise AssertionError(message)


def get_path(value, path):
    for token in path.split("."):
        value = value[int(token)] if token.isdigit() else value[token]
    return value


def key_hash(key):
    return hashlib.sha256(json.dumps(key, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()


def inspect(case, inventory, expected, bundle, report):
    if case not in inventory or case not in expected:
        fail("CASE_NOT_REGISTERED")
    if report.get("schema_version") != "H3_EVALUATION_REPORT_V1":
        fail("REPORT_SCHEMA")
    checks = expected[case]
    scope = checks.get("top_scope", "SYNTHETIC_TEST")
    status = checks.get("top_status", "SYNTHETIC_TEST_ONLY")
    if report.get("status") != status or report.get("claim_scope") != scope:
        fail("SYNTHETIC_SCOPE_ESCALATED_OR_FORMAL_UNQUALIFIED")
    input_runs = bundle["runs"]
    output_runs = report.get("runs")
    if not isinstance(output_runs, list) or len(output_runs) != len(input_runs):
        fail("RUN_SET_COUNT")
    ids = [r["run_id"] for r in input_runs]
    if [r.get("run_id") for r in output_runs] != ids or len(ids) != len(set(ids)):
        fail("RUN_SET_IDENTITY_OR_ORDER")
    cell_ids = [rid for cell in report.get("cells", []) for rid in cell.get("run_ids", [])]
    if sorted(cell_ids) != sorted(ids):
        fail("CELL_RUN_SET")
    for source, result in zip(input_runs, output_runs):
        first, stop = source["capture"]["first_original_id"], source["capture"]["stop_original_id"]
        origin = source["window_grid"]["origin_original_id"]
        starts = [x for x in range(origin, stop - 1024 + 1, 512) if x >= first]
        M = len(starts)
        metrics = result.get("metrics", {})
        if metrics.get("M") != M or len(result.get("windows", [])) != M:
            fail("GRID_M_OR_WINDOW_COUNT:" + source["run_id"])
        if sum(metrics.get("M_classes", {}).values()) != M:
            fail("FIVE_CLASS_CONSERVATION:" + source["run_id"])
        truth = {w["start_original_id"]: w for w in source["truth"]["windows"]}
        input_event_ids = {e["event_id"] for e in source["algorithm"]["events"]}
        event_ids_by_key, takes_by_key = {}, {}
        for e in source["algorithm"]["events"]:
            if not isinstance(e.get("key"), dict) or e.get("kind") == "NOTICE":
                continue
            kh = key_hash(e["key"])
            event_ids_by_key.setdefault(kh, set()).add(e["event_id"])
            if e.get("kind") == "TAKE" and e.get("result") == "SUCCESS":
                takes_by_key.setdefault(kh, set()).add(e["event_id"])
        for i, (start, window) in enumerate(zip(starts, result["windows"])):
            if window.get("frame_index") != i or window.get("start_original_id") != start or window.get("stop_original_id") != start + 1024:
                fail(f"WINDOW_ORIGINAL_ID:{source['run_id']}:{i}")
            if window.get("truth_label") != truth[start]["label"]:
                fail(f"TRUTH_LABEL_CHANGED:{source['run_id']}:{i}")
            capture = source["capture"]
            key = {"run_id": source["run_id"], "frame_index": i,
                   "start_original_id": start, "last_original_id": start + 1023,
                   **{name: capture[name] for name in ("boot_id", "session_id", "interval_id",
                       "epoch", "generation", "algorithm_id", "config_id", "calibration_id")}}
            outcome = window.get("outcome", {})
            if outcome.get("key_sha256") != key_hash(key):
                fail(f"K_IDENTITY:{source['run_id']}:{i}")
            if any(eid not in input_event_ids for eid in outcome.get("event_ids", [])):
                fail(f"FABRICATED_EVENT_ID:{source['run_id']}:{i}")
            kh = key_hash(key)
            expected_ids = event_ids_by_key.get(kh, set())
            if set(outcome.get("event_ids", [])) != expected_ids:
                fail(f"EVENT_SET_INCOMPLETE_OR_EXTRA:{source['run_id']}:{i}")
            successful_takes = takes_by_key.get(kh, set())
            if set(outcome.get("take_history", [])) != successful_takes:
                fail(f"TAKE_HISTORY_INCOMPLETE_OR_EXTRA:{source['run_id']}:{i}")
        if metrics.get("N") is not None and metrics["N"] != metrics["V"] + metrics["D_N"] + metrics["U_N"]:
            fail("TARGET_CONSERVATION:" + source["run_id"])
        for name, parts in (("pre", ("F_pre", "D_pre", "U_pre")),
                            ("post", ("F_post", "D_post", "U_post"))):
            b = metrics.get("B_" + name)
            if b is not None and b != sum(metrics[p] for p in parts):
                fail("BACKGROUND_CONSERVATION:" + name + ":" + source["run_id"])
        if metrics.get("U_N", 0) > 0:
            for gate in ("P50", "P95"):
                if result["gates"][gate].get("final_nominal_deg") is not None:
                    fail("PREMATURE_FINAL_QUANTILE:" + source["run_id"])
        if result.get("audio_qualification", {}).get("status") != "NOT_MEASURABLE":
            fail("AUDIO_UNQUALIFIED_UPGRADE:" + source["run_id"])
        if source["scenario"] != "single-source" and result.get("target_identity_qualification", {}).get("status") == "ESTABLISHED":
            fail("TARGET_IDENTITY_UNPROVEN_UPGRADE:" + source["run_id"])
    if "run_count" in checks and len(output_runs) != checks["run_count"]:
        fail("EXPECTED_RUN_COUNT")
    if "all_run_V" in checks and [r["metrics"]["V"] for r in output_runs] != checks["all_run_V"]:
        fail("UNFAVORABLE_PREREGISTERED_RUN_ERASED_OR_REWRITTEN")
    target = output_runs[checks.get("run_index", 0)]
    for path, wanted in checks.items():
        if path in ("run_count", "all_run_V", "run_index", "top_scope", "top_status"):
            continue
        if path == "protocol_kind":
            if wanted not in [x.get("kind") for x in target.get("protocol_numeric_failures", [])]:
                fail("EXPECTED_PROTOCOL_KIND:" + str(wanted))
            continue
        try:
            actual = get_path(target, path)
        except (KeyError, IndexError, TypeError) as exc:
            fail(f"MISSING_EXPECTED_PATH:{path}:{exc}")
        if actual != wanted:
            fail(f"EXPECTED:{case}:{path}:wanted={wanted!r}:actual={actual!r}")
    return {"case": case, "runs": ids, "assertions": len(checks), "status": "CHECKED"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--inventory", required=True, type=Path)
    ap.add_argument("--expected", required=True, type=Path)
    ap.add_argument("--bundles", required=True, type=Path)
    ap.add_argument("--report", required=True, type=Path)
    ns = ap.parse_args()
    try:
        inventory = json.loads(ns.inventory.read_text())
        expected = json.loads(ns.expected.read_text())["cases"]
        row = inventory[ns.case]
        input_path = ns.bundles / row["file"]
        if sha(input_path) != row["sha256"]:
            fail("INPUT_IDENTITY_DRIFT")
        result = inspect(ns.case, inventory, expected,
                         json.loads(input_path.read_text()), json.loads(ns.report.read_text()))
        print(json.dumps(result, sort_keys=True))
        return 0
    except (AssertionError, KeyError, ValueError, OSError) as exc:
        print(f"CHECKER_FAIL:{type(exc).__name__}:{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
