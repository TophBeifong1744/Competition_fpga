"""Single non-overwriting reproduction entry for the H3 candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import re


def portable(value: str, replacements: dict[str, str]) -> str:
    for original, replacement in sorted(replacements.items(), key=lambda item: -len(item[0])):
        value = value.replace(original, replacement).replace(original.replace('\\', '/'), replacement)
    return value


def run(label, argv, cwd, log_dir, replacements):
    started = time.time()
    result = subprocess.run([str(v) for v in argv], cwd=cwd, capture_output=True, text=True)
    (log_dir / f"{label}.stdout.log").write_text(portable(result.stdout, replacements), encoding="utf-8")
    (log_dir / f"{label}.stderr.log").write_text(portable(result.stderr, replacements), encoding="utf-8")
    record = {"label": label, "argv": [portable(str(v), replacements) for v in argv], "cwd": "<REPO>", "exit_code": result.returncode,
              "started_unix": started, "elapsed_seconds": time.time() - started}
    (log_dir / f"{label}.command.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"{label} failed with {result.returncode}")
    return record


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    package = Path(__file__).resolve().parents[1]
    output = args.out.resolve()
    replacements = {str(root): "<REPO>", str(package): "<PACKAGE>",
                    str(output): "<OUT>", sys.executable: "<PYTHON>",
                    str(Path.home()): "<HOME>"}
    args.out.mkdir(parents=True, exist_ok=False)
    logs = args.out / "logs"; logs.mkdir()
    commands = []
    commands.append(run("package-manifest", [sys.executable, "-B", package / "source/seal_package.py",
                                               "--package", package, "--verify"], root, logs, replacements))
    run("input-pre", [sys.executable, "-B", package / "source/seal_inputs.py", "--repo", root,
                      "--out", package / "inputs.json", "--verify"], root, logs, replacements)
    commands.append(run("unit-tests", [sys.executable, "-B", "-m", "unittest", "discover", "-s",
                                       package / "tests", "-v"], root, logs, replacements))
    commands.append(run("golden", [sys.executable, "-B", package / "source/run_golden.py", "--repo", root,
                                   "--out", args.out / "golden"], root, logs, replacements))
    commands.append(run("golden-check", [sys.executable, "-B", package / "source/check_golden.py", "--repo", root,
                                         "--golden", args.out / "golden/golden-stages.npz",
                                         "--out", args.out / "golden-check.json"], root, logs, replacements))
    commands.append(run("real-diagnostic", [sys.executable, "-B", package / "source/evaluate_real.py", "--repo", root,
                                            "--out", args.out / "real-diagnostic"], root, logs, replacements))
    commands.append(run("budget", [sys.executable, "-B", package / "source/budget.py", "--out", args.out / "budget.json"], root, logs, replacements))
    commands.append(run("skill-scope", [sys.executable, "-B", package / "source/scope_check.py", "--repo", root,
                                        "--out", args.out / "skill-scope.json"], root, logs, replacements))
    # Existing limited-approved three-way audio is rerun unchanged; this does not
    # turn it into an objective acoustic-benefit or real-time result.
    audio = root / "task-packages/PKG-B-ALG/tasks/four-channel-track-01/audio-01"
    commands.append(run("three-way-audio", [sys.executable, "-B", audio / "reproduce.py", "--out", args.out / "three-way-audio"], root, logs, replacements))
    run("input-post", [sys.executable, "-B", package / "source/seal_inputs.py", "--repo", root,
                       "--out", package / "inputs.json", "--verify"], root, logs, replacements)
    unit_log = (logs / "unit-tests.stderr.log").read_text(encoding="utf-8")
    test_match = re.search(r"Ran (\d+) tests? in", unit_log)
    if not test_match:
        raise AssertionError("unit test count missing from log")
    result = {"status": "PASS_AUTHOR_REPRODUCTION_NOT_INDEPENDENT_REVIEW", "commands": len(commands),
              "environment": {"python": platform.python_version(), "platform": platform.platform()},
              "tests": {"h3_candidate_unittest": int(test_match.group(1)),
                        "three_way_audio_existing_package": "50 tests reported by unchanged approved entry; inspect log"},
              "not_run": ["new real-input truth metrics", "presence accuracy", "direction P50/P95",
                          "objective audio improvement", "AMD full-chain bit-exact comparison", "new RTL/XSim",
                          "integrated synthesis/timing", "real-time board audio", "real PYNQ"],
              "commands_detail": commands}
    (args.out / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    files = {p.relative_to(args.out).as_posix(): {"bytes": p.stat().st_size, "sha256": sha(p)}
             for p in sorted(args.out.rglob("*")) if p.is_file() and p.name != "SHA256.json"}
    (args.out / "SHA256.json").write_text(json.dumps(files, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(result["status"])


if __name__ == "__main__":
    main()
