"""Read-only stage checks and a Git-pinned evidence index; not hardware acceptance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PIN = "a91b4700a9cd55b2242eccf032451719f4cb8535"
GROUPS = {
    "a-fft29-approved-research": ["task-packages/PKG-A-ACQ/tasks/fft29-bitexact-budget-01/coverage-extension-01"],
    "a-cboard-approved-diagnostic": ["task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/c-adapter-first-20260913"],
    "b-approved-reference25-diagnostic": ["task-packages/PKG-B-ALG/tasks/c-board-algorithm-01"],
    "independent-review-records": ["docs/reviews/c-adapter-df4b756", "task-packages/PKG-B-ALG/tasks/phat-fixed-03/closeout-01/a29-coverage-review-01"],
    "c-approved-conditional-research": ["task-packages/PKG-A-ACQ/outsourcing/motor_control_plan", "task-packages/PKG-A-ACQ/outsourcing/review-status/motor-407849e"],
    "existing-active-module-library": ["sim", "rtl", "tb"],
    "scope-and-prior-reviews": ["docs/project-plan.md", "docs/phases/2026-09-13-to-10-01/A.md", "docs/phases/2026-09-13-to-10-01/B.md", "task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/current_build/B-REVIEW.md"],
}

def stamp():
    return datetime.now(timezone.utc).isoformat()

def git(*args):
    return subprocess.check_output(["git", "-c", f"safe.directory={ROOT.as_posix()}", *args], cwd=ROOT)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, obj):
    with path.open("x", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True, help="New output directory outside all frozen inputs")
    args = ap.parse_args()
    out = args.out.resolve()
    for paths in GROUPS.values():
        for p in paths:
            if out.is_relative_to(ROOT / p):
                raise ValueError("Output overlaps a frozen source")
    out.mkdir(parents=True, exist_ok=False)
    tree = {}
    for entry in git("ls-tree", "-r", "-z", PIN).split(b"\0"):
        if entry:
            meta, name = entry.split(b"\t", 1)
            mode, kind, oid = meta.decode().split()
            if kind == "blob":
                tree[name.decode("utf-8")] = oid
    records = []
    for group, prefixes in GROUPS.items():
        for p, oid in tree.items():
            if any(p == pre or p.startswith(pre + "/") for pre in prefixes):
                # Historical plan documents may subsequently change. Read pinned Git
                # bytes for these; code, data and evidence must match the working tree.
                data = git("cat-file", "blob", oid) if group == "scope-and-prior-reviews" else (ROOT/p).read_bytes()
                working_sha256 = hashlib.sha256(data).hexdigest()
                normalization = "none"
                actual = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
                if actual != oid:
                    pinned = git("cat-file", "blob", oid)
                    if group != "existing-active-module-library" or b"\0" in data or data.replace(b"\r\n", b"\n") != pinned.replace(b"\r\n", b"\n"):
                        raise ValueError("Fixed input differs: " + p)
                    normalization = "working-tree CRLF/LF only; manifest hashes pinned Git bytes"
                    data = pinned
                records.append(dict(group=group, path=p, commit=PIN, git_blob=oid,
                                    sha256=hashlib.sha256(data).hexdigest(), bytes=len(data),
                                    working_sha256=working_sha256, normalization=normalization))
    save(out/"manifest.json", dict(source_commit=PIN, purpose="Index, not blanket technical approval", files=records))
    protected = {p: sha(ROOT/p) for p in tree if p.startswith(("rtl/", "tb/", "sim/"))}
    skill = ROOT/"skill/pynq-overlay-dma-validation"
    protected.update({p.relative_to(ROOT).as_posix(): sha(p) for p in skill.rglob("*") if p.is_file()})
    pkg = "task-packages/PKG-B-ALG/tasks/c-board-algorithm-01"
    batch = "task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/c-adapter-first-20260913"
    ext = "task-packages/PKG-A-ACQ/tasks/fft29-bitexact-budget-01/coverage-extension-01"
    commands = [
        ("b-tests", [sys.executable, "-B", "-m", "unittest", "discover", "-s", pkg, "-p", "test_run.py", "-v"]),
        ("b-manifest", [sys.executable, "-B", pkg+"/verify_manifest.py"]),
        ("a-recordings", [sys.executable, "-B", batch+"/verify_delivery.py", batch+"/delivery-01", "--report", str(out/"recordings.json")]),
        ("fft-archive", [sys.executable, "-B", ext+"/source/verify_archive.py"]),
    ]
    env = os.environ.copy()
    n = int(env.get("GIT_CONFIG_COUNT", "0"))
    env.update({"GIT_CONFIG_COUNT": str(n+1), f"GIT_CONFIG_KEY_{n}": "safe.directory", f"GIT_CONFIG_VALUE_{n}": ROOT.as_posix()})
    logs = []
    for name, command in commands:
        started = stamp()
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        with (out/(name+".log")).open("xb") as f:
            f.write(result.stdout)
        logs.append(dict(name=name, command=command, started=started, ended=stamp(), exit_code=result.returncode))
        print(name, result.returncode, flush=True)
    save(out/"commands.json", logs)
    unchanged = all(sha(ROOT/p) == digest for p, digest in protected.items())
    # Recheck all frozen non-plan inputs after commands; a test must not rewrite evidence.
    unchanged = unchanged and all(sha(ROOT/r["path"]) == r["working_sha256"] for r in records if r["group"] != "scope-and-prior-reviews")
    ok = unchanged and all(r["exit_code"] == 0 for r in logs)
    save(out/"result.json", dict(status="PASS_STAGE_EVIDENCE_CHECKS_ONLY" if ok else "FAIL", actual_time=stamp(),
                                planned_checkpoint="2026-09-14", source_commit=PIN, indexed_files=len(records),
                                protected_unchanged=unchanged, no_new_rtl_or_board_run=True))
    if not ok:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
