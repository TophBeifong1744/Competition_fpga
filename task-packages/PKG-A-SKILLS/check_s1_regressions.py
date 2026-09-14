"""Record runner/structure checks and X/Z/capacity mutants after the S1 repair."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skill/fpga-module-verification"
sys.path.insert(0, str(SKILL / "scripts"))
from run_xsim import run, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--vivado-bin", required=True)
    parser.add_argument("--validator", type=Path, required=True)
    parser.add_argument("--validator-python", required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {"scope": "AUTHOR_SELF_TEST_NOT_B_ACCEPTANCE", "script_sha256": digest(__file__),
              "python": sys.version, "checks": []}
    for label, argv in (
        ("unit", [sys.executable, "-B", "-m", "unittest", "discover", "-s", str(SKILL / "tests"), "-v"]),
        ("structure", [args.validator_python, "-X", "utf8", str(args.validator), str(SKILL)]),
    ):
        target = out / label
        target.mkdir()
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=120)
        (target / "stdout.log").write_bytes(result.stdout)
        (target / "stderr.log").write_bytes(result.stderr)
        item = {"name": label, "argv": argv, "cwd": str(ROOT), "exit_code": result.returncode,
                "recorded_utc": datetime.now(timezone.utc).isoformat(),
                "stdout_sha256": digest(target / "stdout.log"), "stderr_sha256": digest(target / "stderr.log")}
        (target / "command.json").write_text(json.dumps(item, indent=2) + "\n", encoding="utf-8")
        report["checks"].append(item)
        if result.returncode:
            raise RuntimeError(label)
    for label, old, new in (
        ("payload-x", "out_data <= in_data;", "out_data <= {WIDTH{1'bx}};"),
        ("payload-z", "out_data <= in_data;", "out_data <= {WIDTH{1'bz}};"),
        ("capacity", "!out_valid || out_ready", "1'b1"),
    ):
        fixture = out / "fixtures" / label
        shutil.copytree(SKILL / "examples/elastic", fixture)
        dut = fixture / "elastic_stage.v"
        source = dut.read_text(encoding="utf-8")
        assert source.count(old) == 1
        dut.write_text(source.replace(old, new), encoding="utf-8")
        code, result = run(fixture / "case.json", args.vivado_bin, out / label)
        ok = code == 1 and result["stage"] == "simulate" and result["status"] == "FAIL_SIMULATION"
        item = {"name": label, "matched": ok, "status": result["status"],
                "first_failure": result.get("first_failure"), "result_sha256": digest(out / label / "result.json")}
        report["checks"].append(item)
        (out / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(item), flush=True)
        if not ok:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
