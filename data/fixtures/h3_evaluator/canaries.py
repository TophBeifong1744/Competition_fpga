"""Mutate saved DUT reports and require the real checker subprocess to reject."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys

ASSET = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundles", required=True, type=Path)
    ap.add_argument("--dut-results", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ns = ap.parse_args()
    ns.out.mkdir(parents=True, exist_ok=False)
    recipes = [
        ("count_n", "c04_v749", lambda r: r["runs"][0]["metrics"].__setitem__("N", 935), "TARGET_CONSERVATION"),
        ("missing_failed_run", "c08_sixth_fail", lambda r: r["runs"].pop(), "RUN_SET_COUNT"),
        ("equal_angle_wrong_k", "c14_equal_angle", lambda r: r["runs"][0]["windows"][0]["outcome"].__setitem__(
            "key_sha256", r["runs"][0]["windows"][1]["outcome"]["key_sha256"]), "K_IDENTITY"),
        ("missing_event", "c14_equal_angle", lambda r: r["runs"][0]["windows"][0]["outcome"]["event_ids"].pop(), "EVENT_SET_INCOMPLETE_OR_EXTRA"),
        ("u_forged_done", "c03_all_u", lambda r: (r["runs"][0]["metrics"].__setitem__("U_N", 0),
                                               r["runs"][0]["metrics"].__setitem__("D_N", 936)), "EXPECTED"),
        ("bad_certificate", "r01a", lambda r: r["runs"][0]["gates"]["P50"]["certificate"].__setitem__("g", 1), "EXPECTED"),
        ("delete_target_axis", "mixed_wrong_same_angle", lambda r: r["runs"][0].pop("target_identity_qualification"), "MISSING_EXPECTED_PATH"),
        ("delete_audio_axis", "c25_audio_missing", lambda r: r["runs"][0].pop("audio_qualification"), "AUDIO_UNQUALIFIED_UPGRADE"),
        ("erase_time_uncertainty", "c21_take_u", lambda r: r["runs"][0]["windows"][0]["outcome"].__setitem__("reason", "NO_RESULT"), "EXPECTED"),
        ("synthetic_to_pass", "c04_v749", lambda r: r.__setitem__("status", "PASS"), "SYNTHETIC_SCOPE_ESCALATED"),
    ]
    records = []
    for name, case, mutate, expected_error in recipes:
        original = json.loads((ns.dut_results / case / "report.json").read_text())
        altered = copy.deepcopy(original)
        mutate(altered)
        path = ns.out / (name + ".json")
        path.write_text(json.dumps(altered, indent=2) + "\n", encoding="utf-8")
        cmd = [sys.executable, "-B", str(ASSET / "checker.py"), "--case", case,
               "--inventory", str(ns.bundles / "inventory.json"),
               "--expected", str(ASSET / "expected.json"), "--bundles", str(ns.bundles),
               "--report", str(path)]
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        (ns.out / (name + ".stdout.log")).write_text(p.stdout, encoding="utf-8")
        (ns.out / (name + ".stderr.log")).write_text(p.stderr, encoding="utf-8")
        (ns.out / (name + ".command.json")).write_text(json.dumps(
            {"argv": cmd, "cwd": str(Path.cwd()), "exit_code": p.returncode}, indent=2)+"\n")
        passed = p.returncode != 0 and expected_error in p.stderr
        records.append({"name": name, "case": case, "expected_error": expected_error,
                        "exit_code": p.returncode, "matched_target_assertion": passed})
    (ns.out / "summary.json").write_text(json.dumps(records, indent=2)+"\n")
    print(json.dumps({"canaries": len(records), "target_rejections": sum(x["matched_target_assertion"] for x in records)}))
    return 0 if all(x["matched_target_assertion"] for x in records) else 1


if __name__ == "__main__":
    sys.exit(main())
