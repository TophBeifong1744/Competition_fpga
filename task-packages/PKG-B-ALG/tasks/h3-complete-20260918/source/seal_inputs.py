"""Create or verify the exact upstream input hash ledger."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


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


def ledger(root):
    result = {}
    for relative in INPUTS:
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(relative)
        result[relative] = {"bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    actual = ledger(args.repo.resolve())
    if args.verify:
        expected = json.loads(args.out.read_text(encoding="utf-8"))
        if expected["files"] != actual:
            raise RuntimeError("INPUT_HASH_MISMATCH")
        print("PASS_INPUT_HASHES", len(actual))
        return
    if args.out.exists():
        raise FileExistsError(args.out)
    payload = {"schema": "h3-input-ledger-0.1", "files": actual,
               "external_pending": {"commit": "8f708e42caf32c1de6f30726298e3edf0e1970b6", "branch": "codex/toph/background-target-stop-20260917",
                                    "scope": "six-second real input; pending B review; not copied into this candidate"}}
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("SEALED_INPUT_HASHES", len(actual))


if __name__ == "__main__":
    main()
