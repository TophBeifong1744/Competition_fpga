"""Limited phase check; no HDL build, board access, or package approval."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    commands, manifests = [], []

    def run(label, command, cwd):
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
        (out / (label + ".txt")).write_text(result.stdout + result.stderr, encoding="utf-8")
        commands.append({"label": label, "argv": command, "cwd": str(cwd),
                         "exit_code": result.returncode})
        return result.returncode == 0

    def manifest(folder):
        obj = json.loads((folder / "file-manifest.json").read_text(encoding="utf-8-sig"))
        entries = obj if isinstance(obj, list) else obj["files"]
        errors = []
        for item in entries:
            path = (folder / item["path"]).resolve()
            if not path.is_relative_to(folder) or not path.is_file():
                errors.append(item["path"] + ":missing/unsafe")
                continue
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest().lower() != item["sha256"].lower() or len(raw) != item["bytes"]:
                errors.append(item["path"] + ":hash/size")
        manifests.append({"folder": folder.relative_to(repo).as_posix(),
                          "count": len(entries), "errors": errors})
        return not errors

    checks = []
    acq = repo / "task-packages/PKG-A-ACQ"
    checks.append(run("h1-fixtures", [sys.executable, "-B", str(acq / "payload/scripts/check_h1_fixtures.py")], repo))
    mono = repo / "task-packages/PKG-A-H2-MONO-DIAGNOSTIC"
    for label, script, extra in [("mono-manifest", "file_manifest.py", ["verify"]),
                                 ("mono-export", "mono_delivery.py", ["verify"]),
                                 ("mono-tests", "test_delivery.py", [])]:
        checks.append(run(label, [sys.executable, "-B", "source/" + script] + extra, mono))
    for name in ("C-RTL-002", "C-RTL-003"):
        checks.append(manifest(acq / "outsourcing" / name / "submission"))

    # Match the original B submission to the exact files recorded by A's review.
    b = repo / "task-packages/PKG-B-ALG/tasks/0910-closeout"
    review = json.loads((b / "a-review-01/evidence/review-result.json").read_text())
    original = review["reviewed_commit"]
    mismatches = []
    for name, expected in review["original_files"].items():
        current = (repo / name).read_bytes()
        blob = subprocess.check_output(["git", "show", original + ":" + name], cwd=repo)
        if current != blob or hashlib.sha256(current).hexdigest() != expected:
            mismatches.append(name)
    checks.append(not mismatches)
    result = {
        "status": "PASS_PHASE_ARTIFACT_CHECKS" if all(checks) else "FAIL_PHASE_ARTIFACT_CHECKS",
        "baseline_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
        "commands": commands, "c_manifests": manifests,
        "b_reviewed_commit": original, "b_original_file_count": len(review["original_files"]),
        "b_original_mismatches": mismatches,
        "not_run": ["new HDL simulation", "new synthesis/implementation", "board measurements",
                    "full four-channel acquisition acceptance", "complete H3 algorithm approval"],
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "c_files": sum(r["count"] for r in manifests),
                      "b_files": result["b_original_file_count"]}, indent=2))
    raise SystemExit(0 if all(checks) else 1)


if __name__ == "__main__":
    main()
