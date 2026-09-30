"""Bounded CLI error-code and exclusive-output probes; no product edits."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ASSET = Path(__file__).resolve().parent
PACKAGE_CWD = ASSET.parents[2] / "models" / "python"


def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundles", required=True, type=Path)
    ap.add_argument("--existing-out", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ns = ap.parse_args()
    ns.out.mkdir(parents=True, exist_ok=False)
    rows = []
    def execute(name, cmd, expected_exit, expected_text, output=None):
        p = subprocess.run(cmd, cwd=PACKAGE_CWD, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        (ns.out / (name + ".stdout.log")).write_text(p.stdout, encoding="utf-8")
        (ns.out / (name + ".stderr.log")).write_text(p.stderr, encoding="utf-8")
        failure = json.loads((output / "failure.json").read_text()) if output is not None and (output / "failure.json").exists() else None
        found = p.stdout + p.stderr + (json.dumps(failure) if failure is not None else "")
        ok = p.returncode == expected_exit and expected_text in found
        if output is not None:
            ok = ok and failure is not None and failure.get("exit_code") == expected_exit
        row = {"name": name, "argv": cmd, "cwd": str(PACKAGE_CWD),
               "exit_code": p.returncode, "expected_exit": expected_exit,
               "expected_text": expected_text, "matched": ok}
        rows.append(row)
        (ns.out / (name + ".command.json")).write_text(json.dumps(row, indent=2)+"\n")
    bad = json.loads((ns.bundles / "c14_equal_angle.json").read_text())
    bad["runs"][0]["capture"]["drop_ranges"] = "not-a-range-list"
    bad_path = ns.out / "malformed.json"; bad_path.write_text(json.dumps(bad)+"\n")
    dst = ns.out / "malformed-out"
    execute("malformed", [sys.executable, "-B", "-m", "soundsight_h3_evaluator",
                          "--bundle", str(bad_path), "--out", str(dst)], 2, "CAPTURE_FLAGS_REQUIRED", dst)
    ident = json.loads((ns.bundles / "mixed_wrong_same_angle.json").read_text())
    source = (ns.bundles / "identity-source.txt").read_bytes()
    (ns.out / "identity-source.txt").write_bytes(source)
    ident["references"][0]["sha256"] = "0" * 64
    ident_path = ns.out / "identity-mismatch.json"; ident_path.write_text(json.dumps(ident)+"\n")
    dst = ns.out / "identity-out"
    execute("identity", [sys.executable, "-B", "-m", "soundsight_h3_evaluator",
                         "--bundle", str(ident_path), "--out", str(dst)], 3, "REFERENCE_MISMATCH", dst)
    before = hash_file(ns.existing_out / "report.json")
    execute("output_exists", [sys.executable, "-B", "-m", "soundsight_h3_evaluator",
                              "--bundle", str(ns.bundles / "c04_v749.json"),
                              "--out", str(ns.existing_out)], 2, "OUTPUT_EXISTS")
    rows[-1]["existing_report_unchanged"] = before == hash_file(ns.existing_out / "report.json")
    rows[-1]["matched"] = rows[-1]["matched"] and rows[-1]["existing_report_unchanged"]
    # Fault injection calls the exact main() with a controlled evaluator exception.
    # This verifies exit 4/failure.json without risking source drift or touching product.
    dst = ns.out / "internal-out"
    code = ("import sys; from soundsight_h3_evaluator import __main__ as m; "
            "m.evaluate=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('CONTROLLED_INTERNAL')); "
            "sys.exit(m.main(sys.argv[1:]))")
    execute("internal_injected", [sys.executable, "-B", "-c", code,
                                  "--bundle", str(ns.bundles / "c14_equal_angle.json"),
                                  "--out", str(dst)], 4, "CONTROLLED_INTERNAL", dst)
    (ns.out / "summary.json").write_text(json.dumps(rows, indent=2)+"\n")
    print(json.dumps({"cases": len(rows), "matched": sum(x["matched"] for x in rows)}))
    return 0 if all(x["matched"] for x in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
