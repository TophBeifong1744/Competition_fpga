"""Positive, mutated-DUT and restored-DUT XSim demonstration; author test only."""
import argparse
import json
from pathlib import Path
import shutil
import sys
from run_xsim import run, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vivado-bin", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = Path(args.output).resolve()
    if output.exists():
        parser.error("Use a new output directory")
    output.mkdir(parents=True)
    summary = {"status": "RUNNING", "scope": "author demonstration, not independent B review",
               "script_sha256": digest(__file__), "runs": []}
    cases = [("pcm4", root / "examples/pcm4/case.json", "PASS_SIMULATION"),
             ("elastic", root / "examples/elastic/case.json", "PASS_SIMULATION")]
    try:
        for label, old, new in (
            ("bad_data", "out_data <= in_data;", "out_data <= in_data ^ 1'b1;"),
            ("bad_ready", "!out_valid || out_ready", "out_ready"),
        ):
            fixture = output / "fixtures" / label
            fixture.mkdir(parents=True)
            for path in (root / "examples/elastic").iterdir():
                if path.is_file():
                    shutil.copyfile(path, fixture / path.name)
            dut = fixture / "elastic_stage.v"
            content = dut.read_text(encoding="utf-8")
            if content.count(old) != 1:
                raise ValueError("Mutation no longer matches exactly once; update test explicitly")
            dut.write_text(content.replace(old, new), encoding="utf-8")
            cases.append((label, fixture / "case.json", "FAIL_SIMULATION"))
        cases.append(("restored", root / "examples/elastic/case.json", "PASS_SIMULATION"))
        for name, case, expected in cases:
            code, result = run(case, args.vivado_bin, output / name)
            ok = result["status"] == expected and result["stage"] == "simulate" and code == (0 if expected.startswith("PASS") else 1)
            item = {"name": name, "expected": expected, "actual": result["status"],
                    "matched": ok, "checks": result.get("checks"), "first_failure": result.get("first_failure"),
                    "result": name + "/result.json", "result_sha256": digest(output / name / "result.json")}
            summary["runs"].append(item)
            print(json.dumps(item), flush=True)
            if not ok:
                raise RuntimeError("Unexpected run outcome: " + name)
        summary["status"] = "PASS_DEMONSTRATION"
    except Exception as exc:
        summary.update(status="FAIL_OR_BLOCKED", error=str(exc))
    finally:
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return 0 if summary["status"] == "PASS_DEMONSTRATION" else 1


if __name__ == "__main__":
    sys.exit(main())
