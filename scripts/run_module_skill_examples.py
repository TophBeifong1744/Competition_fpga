"""Adapt frozen Skill examples to the repository layout; diagnostic use only."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skill" / "fpga-module-verification"
SOURCE_MOVES = {
    "rtl/acquisition/pcm4_signext_pack.v": "project/rtl/acquisition/pcm4_signext_pack.v",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def new_output(value):
    output = Path(value).resolve()
    diagnostics = REPO / "codex_out"
    if output == diagnostics or diagnostics not in output.parents:
        raise ValueError("Use a new directory below repository codex_out")
    if output.exists():
        raise ValueError("Use a new output directory; previous evidence is immutable")
    return output


def derive_case(name, output):
    original = SKILL / "examples" / name / "case.json"
    case = json.loads(original.read_text(encoding="utf-8-sig"))
    sources = []
    mappings = []
    for value in case["sources"]:
        old = (original.parent / value).resolve()
        relative = old.relative_to(REPO).as_posix()
        source = REPO / SOURCE_MOVES.get(relative, relative)
        if not source.is_file():
            raise ValueError("Missing source: " + str(source))
        sources.append(str(source))
        mappings.append({"original": value, "resolved": str(source), "sha256": digest(source)})
    contract = (original.parent / case["contract"]).resolve(strict=True)
    case["sources"] = sources
    case["contract"] = str(contract)
    derived = output / "cases" / name / "case.json"
    derived.parent.mkdir(parents=True)
    derived.write_text(json.dumps(case, indent=2) + "\n", encoding="utf-8")
    return derived, {
        "name": name,
        "original_case": str(original.relative_to(REPO)),
        "original_case_sha256": digest(original),
        "derived_case": str(derived.relative_to(output)),
        "derived_case_sha256": digest(derived),
        "contract": str(contract.relative_to(REPO)),
        "contract_sha256": digest(contract),
        "sources": mappings,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=("all", "pcm4", "elastic"), default="all")
    parser.add_argument("--output", required=True)
    parser.add_argument("--vivado-bin", help="Explicit Vivado 2025.2 bin directory")
    parser.add_argument("--timeout", type=float, default=90)
    parser.add_argument("--prepare-only", action="store_true", help="Write derived cases without running XSim")
    args = parser.parse_args()
    if not args.prepare_only and not args.vivado_bin:
        parser.error("--vivado-bin is required unless --prepare-only is used")
    if not 0 < args.timeout <= 3600:
        parser.error("--timeout must be positive and <= 3600 seconds")
    try:
        output = new_output(args.output)
        output.mkdir(parents=True)
    except (ValueError, OSError) as exc:
        print("BLOCKED_INPUT:", exc)
        return 2
    runner = SKILL / "scripts" / "run_xsim.py"
    summary = {
        "status": "RUNNING",
        "scope": "layout-adapted positive examples; diagnostic only, not Skill or product approval",
        "adapter_sha256": digest(Path(__file__)),
        "runner": str(runner.relative_to(REPO)),
        "runner_sha256": digest(runner),
        "not_run": ["negative mutations", "synthesis", "timing", "cdc", "board", "system"],
        "cases": [],
    }
    exit_code = 0
    try:
        names = ("pcm4", "elastic") if args.case == "all" else (args.case,)
        for name in names:
            derived, entry = derive_case(name, output)
            summary["cases"].append(entry)
            if args.prepare_only:
                entry["status"] = "NOT_RUN"
                continue
            run_output = output / "runs" / name
            command = [sys.executable, "-B", str(runner), "--case", str(derived),
                       "--vivado-bin", args.vivado_bin, "--output", str(run_output),
                       "--timeout", str(args.timeout)]
            entry["command"] = command
            entry["cwd"] = str(REPO)
            completed = subprocess.run(command, cwd=REPO, check=False)
            entry["exit_code"] = completed.returncode
            result_path = run_output / "result.json"
            if result_path.is_file():
                result = json.loads(result_path.read_text(encoding="utf-8"))
                entry.update(status=result["status"], stage=result.get("stage"),
                             checks=result.get("checks"), result=str(result_path.relative_to(output)),
                             result_sha256=digest(result_path))
            if completed.returncode != 0:
                exit_code = completed.returncode
                break
        summary["status"] = ("FAILED_OR_BLOCKED" if exit_code else
                             "PREPARED_NOT_RUN" if args.prepare_only else "DIAGNOSTIC_ONLY")
    except (ValueError, KeyError, OSError) as exc:
        summary.update(status="BLOCKED_INPUT", error=str(exc))
        exit_code = 2
    finally:
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": summary["status"], "summary": str(output / "summary.json")}))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
