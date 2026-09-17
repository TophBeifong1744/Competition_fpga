"""Recompute and compare every archived golden array; never overwrite evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from fixed_golden import full_chain
from run_golden import deterministic_pcm


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--golden", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    saved = np.load(args.golden, allow_pickle=False)
    actual, result = full_chain(deterministic_pcm(), args.repo.resolve())
    rows = []
    for name in sorted(saved.files):
        if name not in actual:
            raise AssertionError(f"missing recomputed array: {name}")
        expected = saved[name]
        observed = actual[name]
        equal = np.array_equal(expected, observed)
        rows.append({"name": name, "shape": list(expected.shape), "equal": bool(equal),
                     "expected_sha256": hashlib.sha256(expected.astype("<i8", copy=False).tobytes()).hexdigest(),
                     "actual_sha256": hashlib.sha256(observed.astype("<i8", copy=False).tobytes()).hexdigest()})
        if not equal:
            raise AssertionError(f"stage mismatch: {name}")
    if set(saved.files) != set(actual):
        raise AssertionError("archive/recomputed stage set differs")
    payload = {"status": "PASS_ALL_STAGE_ARRAYS_EXACT", "array_count": len(rows), "arrays": rows,
               "chain_discrete": {"pairs": result["pairs"], "doa": result["doa"], "tracker": result["tracker"]}}
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(payload["status"], len(rows))


if __name__ == "__main__":
    main()
