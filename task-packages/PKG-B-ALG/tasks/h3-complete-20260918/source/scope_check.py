"""Incremental 9/18 scope check for the two already approved Skills."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


SKILLS = {
    "SKL-001": {
        "approved_sha": "a7e1ea976da91ba735af5c0a79fffdc7d10c121f",
        "path": "skill/fpga-module-verification",
        "approved_scope": "module simulation only",
        "normal_cases": ["pcm4 signed extension", "elastic ready-valid normal and reset recovery"],
        "failure_cases": ["bad data", "bad ready", "two-stage latency", "full-slot capacity", "X/Z propagation"],
        "unknown_case": "historical independent signed8 saturation fault is reusable evidence",
        "migration_case": "NOT_RUN; no new unknown module/tool-version migration executed for 9/18",
        "hardware": "NOT_RUN"
    },
    "SKL-002": {
        "approved_sha": "3ac597d1d16982e0a5c5a114202ca8568dc28d8f",
        "path": "skill/pynq-overlay-dma-validation",
        "approved_scope": "offline static/mock only",
        "profiles": ["thermal signed16 96-byte synthetic profile", "pixel uint32 128-byte synthetic profile"],
        "failure_cases": ["cache stale", "timeout and abort timeout", "short output", "duplicate evidence ID",
                          "release failure", "large integer 2**120 one-code mismatch"],
        "hardware": "NOT_RUN_REAL_PYNQ"
    }
}


def git(root, *args):
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    root = args.repo.resolve()
    _, head, _ = git(root, "rev-parse", "HEAD")
    results = {}
    for name, item in SKILLS.items():
        ancestor_code, _, ancestor_err = git(root, "merge-base", "--is-ancestor", item["approved_sha"], head)
        diff_code, diff, diff_err = git(root, "diff", "--name-only", f"{item['approved_sha']}..{head}", "--", item["path"])
        path = root / item["path"]
        if ancestor_code or diff_code or not path.is_dir():
            raise RuntimeError(f"{name} scope identity failed: {ancestor_err} {diff_err}")
        files = [path / "SKILL.md", path / "README.md"]
        results[name] = item | {"approved_sha_is_ancestor": True, "changed_files_since_approved_sha": diff.splitlines() if diff else [],
                                "entry_hashes": {p.relative_to(root).as_posix(): sha(p) for p in files},
                                "decision": "REUSE_APPROVED_SCOPE_NO_FULL_RERUN",
                                "license_and_source": "retained from approved package; no path change"}
    payload = {"status": "PASS_INCREMENTAL_SCOPE_IDENTITY_ONLY", "checkout_head": head,
               "review_rule": "2026-09-17 incremental review; unchanged approved paths reused",
               "skills": results,
               "limits": ["No new independent Skill acceptance is issued by A author work.",
                          "SKL-001 remains module-simulation limited, not production RTL or board proof.",
                          "SKL-002 real PYNQ remains NOT_RUN and bonus risk remains open."]}
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])


if __name__ == "__main__":
    main()
