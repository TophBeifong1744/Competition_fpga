"""Create or verify the exact upstream input hash ledger."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


INPUTS = [
    "docs/input-scale-and-pl-ps-boundary.md",
    "docs/maintenance/skills-rereview-b-2026-09-14.md",
    "docs/reviews/four-track-f364a02/REVIEW.md",
    "task-packages/PKG-B-ALG/tasks/four-channel-track-01/config.json",
    "task-packages/PKG-B-ALG/tasks/four-channel-track-01/tracking.py",
    "task-packages/PKG-B-ALG/tasks/four-channel-track-01/evidence/run02/center-frames.json",
    "task-packages/PKG-B-ALG/tasks/four-channel-track-01/evidence/run02/quiet-frames.json",
    "task-packages/PKG-B-ALG/tasks/four-channel-track-01/audio-01/config.json",
    "task-packages/PKG-B-ALG/tasks/four-channel-track-01/audio-01/evidence/run02/audio/result.json",
    "task-packages/PKG-B-ALG/tasks/c-board-algorithm-01/H3-GAPS.md",
    "task-packages/PKG-B-ALG/tasks/c-board-algorithm-01/run.py",
    "task-packages/PKG-B-ALG/tasks/phat-fixed-03/phat_model.py",
    "task-packages/PKG-B-ALG/tasks/phat-fixed-03/integration/protocol.json",
    "task-packages/PKG-B-ALG/tasks/input-boundary-adoption-01/contract.json",
    "task-packages/PKG-A-ACQ/tasks/fft29-bitexact-budget-01/coverage-extension-01/evidence/run01/check.json",
    "task-packages/PKG-A-H3-INTEGRATION/payload/H3-CONSTRAINTS.md",
    "skill/fpga-module-verification/SKILL.md",
    "skill/pynq-overlay-dma-validation/SKILL.md"
]


def git_blob(root: Path, relative: str) -> bytes:
    result = subprocess.run(["git", "show", f"HEAD:{relative}"], cwd=root,
                            capture_output=True)
    if result.returncode:
        raise RuntimeError(f"cannot read committed Git blob: {relative}: {result.stderr.decode(errors='replace')}")
    return result.stdout


def canonical_worktree_bytes(raw: bytes, committed: bytes, relative: str) -> tuple[bytes, str]:
    if raw == committed:
        return raw, "exact"
    # The only accepted checkout transformation is CRLF for LF in a text file.
    # Hash and byte count are always for the committed Git blob, never the host
    # checkout.  This is deliberately narrower than arbitrary whitespace cleanup.
    if Path(relative).suffix.lower() in {".md", ".json", ".py", ".txt"}:
        normalized = raw.replace(b"\r\n", b"\n")
        if normalized == committed and b"\r\n" in raw:
            return normalized, "crlf_to_lf"
    raise RuntimeError(f"WORKTREE_DIFFERS_FROM_GIT_BLOB: {relative}")


def ledger(root):
    result = {}
    checkout_modes = {}
    for relative in INPUTS:
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(relative)
        committed = git_blob(root, relative)
        canonical, mode = canonical_worktree_bytes(path.read_bytes(), committed, relative)
        result[relative] = {"bytes": len(committed), "sha256": hashlib.sha256(committed).hexdigest()}
        checkout_modes[relative] = mode
        assert canonical == committed
    return result, checkout_modes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--rewrite", action="store_true", help="explicitly replace the old working-byte ledger")
    args = parser.parse_args()
    if args.verify and args.rewrite:
        parser.error("--verify and --rewrite are mutually exclusive")
    actual, modes = ledger(args.repo.resolve())
    if args.verify:
        expected = json.loads(args.out.read_text(encoding="utf-8"))
        if expected.get("schema") != "h3-git-blob-input-ledger-0.2" or expected["files"] != actual:
            raise RuntimeError("INPUT_HASH_MISMATCH")
        print("PASS_INPUT_GIT_BLOB_HASHES", len(actual),
              "CRLF_NORMALIZED", sum(mode == "crlf_to_lf" for mode in modes.values()))
        return
    if args.out.exists() and not args.rewrite:
        raise FileExistsError(args.out)
    payload = {"schema": "h3-git-blob-input-ledger-0.2",
               "byte_contract": "sha256 and bytes refer to HEAD Git blob; text checkout may only CRLF-to-LF normalize to that exact blob",
               "files": actual,
               "external_pending": {"commit": "8f708e42caf32c1de6f30726298e3edf0e1970b6", "branch": "codex/toph/background-target-stop-20260917",
                                    "scope": "six-second real input; pending B review; not copied into this candidate"}}
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("SEALED_INPUT_GIT_BLOB_HASHES", len(actual))


if __name__ == "__main__":
    main()
