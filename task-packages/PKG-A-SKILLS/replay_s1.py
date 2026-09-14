"""Replay B's frozen S1 inputs with old/new TBs; author regression, not B approval."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

REVIEW = "0ef0355642ea8719d5e4cdde0a38c531550218d4"
BROOT = "results/skill-review/b-20260914/"
ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skill/fpga-module-verification"
sys.path.insert(0, str(SKILL / "scripts"))
from run_xsim import run, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--vivado-bin", required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    sources = []
    # Only raw, already-reviewed test inputs. Do not run or alter B's pinned reproduce.py.
    for folder in ("latency-mutant", "b-latency-original", "b-latency-two-stage"):
        names = subprocess.check_output(
            ["git", "-c", f"safe.directory={ROOT.as_posix()}", "ls-tree", "-r", "--name-only", REVIEW, BROOT + folder + "/"], cwd=ROOT
        ).decode().splitlines()
        for name in names:
            raw = subprocess.check_output(
                ["git", "-c", f"safe.directory={ROOT.as_posix()}", "show", REVIEW + ":" + name], cwd=ROOT
            )
            dest = output / "b-inputs" / name.removeprefix(BROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(raw)
            sources.append({"commit": REVIEW, "git_path": name,
                            "copy": dest.relative_to(output).as_posix(), "sha256": digest(dest)})
    (output / "b-inputs.json").write_text(json.dumps(sources, indent=2) + "\n", encoding="utf-8")
    fixed = output / "fixed-mutant"
    shutil.copytree(output / "b-inputs/latency-mutant", fixed)
    # Same B DUT, contract, case and stimulus; only repaired assertions/accounting change.
    shutil.copyfile(SKILL / "examples/elastic/tb_elastic.sv", fixed / "tb_elastic.sv")
    cases = [
        ("old-tb", output / "b-inputs/latency-mutant/case.json", "PASS_SIMULATION"),
        ("new-tb", fixed / "case.json", "FAIL_SIMULATION"),
        ("b-good", output / "b-inputs/b-latency-original/case.json", "PASS_SIMULATION"),
        ("b-bad", output / "b-inputs/b-latency-two-stage/case.json", "FAIL_SIMULATION"),
    ]
    report = {"review_commit": REVIEW, "scope": "AUTHOR_SELF_TEST_NOT_B_ACCEPTANCE",
              "script_sha256": digest(__file__), "runs": []}
    for name, case, expected in cases:
        code, result = run(case, args.vivado_bin, output / name)
        ok = result["status"] == expected and result["stage"] == "simulate" and code == (0 if expected.startswith("PASS") else 1)
        item = {"name": name, "expected": expected, "status": result["status"],
                "exit_code": code, "matched": ok, "checks": result.get("checks"),
                "first_failure": result.get("first_failure"),
                "result_sha256": digest(output / name / "result.json")}
        report["runs"].append(item)
        print(json.dumps(item), flush=True)
        (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        if not ok:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
