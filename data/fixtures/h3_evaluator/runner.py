"""Run exact CLI then independent checker; keep first failure and raw logs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ASSET = Path(__file__).resolve().parent
PACKAGE_CWD = ASSET.parents[2] / "models" / "python"
PRODUCT = PACKAGE_CWD / "soundsight_h3_evaluator"
PRODUCT_FILES = ("__init__.py", "__main__.py", "bundle.py", "events.py", "grid.py",
                 "metrics.py", "report.py", "README.md")


def hashes():
    return {name: hashlib.sha256((PRODUCT / name).read_bytes()).hexdigest()
            for name in PRODUCT_FILES}


def execute(argv, cwd, prefix):
    p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=180)
    (prefix.with_suffix(".stdout.log")).write_text(p.stdout, encoding="utf-8")
    (prefix.with_suffix(".stderr.log")).write_text(p.stderr, encoding="utf-8")
    (prefix.with_suffix(".command.json")).write_text(json.dumps(
        {"argv": argv, "cwd": str(cwd), "exit_code": p.returncode}, indent=2) + "\n",
        encoding="utf-8")
    return p.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundles", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--case")
    ap.add_argument("--inject-checker-failure", action="store_true")
    ns = ap.parse_args()
    ns.out.mkdir(parents=True, exist_ok=False)
    inv = json.loads((ns.bundles / "inventory.json").read_text())
    names = [ns.case] if ns.case else list(inv)
    before = hashes()
    rows = []
    failure = None
    for name in names:
        case_out = ns.out / name
        argv = [sys.executable, "-B", "-m", "soundsight_h3_evaluator", "--bundle",
                str((ns.bundles / inv[name]["file"]).resolve()), "--out", str(case_out.resolve())]
        dut_exit = execute(argv, PACKAGE_CWD, ns.out / (name + "-dut"))
        if dut_exit != 0:
            failure = {"case": name, "stage": "DUT_CLI", "exit": dut_exit}
            rows.append(failure)
            break
        report = case_out / "report.json"
        index_path = case_out / "evidence-index.json"
        source_index = json.loads(index_path.read_text())
        actual_report_sha = hashlib.sha256(report.read_bytes()).hexdigest()
        if (source_index.get("outputs_sha256", {}).get("report.json") != actual_report_sha or
                source_index.get("bundle", {}).get("sha256") != inv[name]["sha256"] or
                source_index.get("source_sha256") != before):
            failure = {"case": name, "stage": "DUT_OUTPUT_INDEX_OR_SOURCE_IDENTITY", "exit": 1}
            rows.append(failure)
            break
        if ns.inject_checker_failure:
            obj = json.loads(report.read_text())
            obj["status"] = "PASS"  # controlled runner propagation canary
            report = ns.out / (name + "-injected-report.json")
            report.write_text(json.dumps(obj) + "\n")
        check = [sys.executable, "-B", str(ASSET / "checker.py"), "--case", name,
                 "--inventory", str((ns.bundles / "inventory.json").resolve()),
                 "--expected", str((ASSET / "expected.json").resolve()),
                 "--bundles", str(ns.bundles.resolve()), "--report", str(report.resolve())]
        check_exit = execute(check, PACKAGE_CWD, ns.out / (name + "-checker"))
        row = {"case": name, "dut_exit": dut_exit, "checker_exit": check_exit,
               "report_sha256": hashlib.sha256(report.read_bytes()).hexdigest()}
        rows.append(row)
        if check_exit != 0:
            failure = {"case": name, "stage": "CHECKER", "exit": check_exit}
            break
    after = hashes()
    summary = {"product_before": before, "product_after": after,
               "cases_requested": names, "cases_executed": rows,
               "first_failure": failure, "input_identity_stable": before == after}
    (ns.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    if failure or before != after:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
