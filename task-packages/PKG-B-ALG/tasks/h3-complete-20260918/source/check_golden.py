"""Recompute and compare every archived golden array; never overwrite evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from fixed_golden import full_chain
from run_golden import boundary_vectors, deterministic_pcm


FROZEN_CHAIN_FIELDS = ("window_overflow", "adapter_overflow", "fft_flags", "ifft_flags",
                       "pairs", "doa", "tracker", "audio_timeline",
                       "stage_shapes")


def exact_json_hash(value) -> str:
    packed = json.dumps(value, ensure_ascii=False, sort_keys=True,
                        separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(packed).hexdigest()


def compare_frozen_chain(saved_chain: dict, actual_chain: dict) -> list[dict]:
    if set(saved_chain) != set(FROZEN_CHAIN_FIELDS) or set(actual_chain) != set(FROZEN_CHAIN_FIELDS):
        raise AssertionError("frozen/recomputed chain field set differs")
    rows = []
    for name in FROZEN_CHAIN_FIELDS:
        expected_hash = exact_json_hash(saved_chain[name])
        actual_hash = exact_json_hash(actual_chain[name])
        equal = saved_chain[name] == actual_chain[name]
        rows.append({"name": name, "equal": equal,
                     "frozen_sha256": expected_hash, "recomputed_sha256": actual_hash})
        if not equal:
            raise AssertionError(f"frozen chain mismatch: {name}")
    return rows


def compare_frozen_arrays(saved, actual: dict) -> list[dict]:
    if set(saved.files) != set(actual):
        raise AssertionError("archive/recomputed stage set differs")
    rows = []
    for name in sorted(saved.files):
        expected = saved[name]
        observed = actual[name]
        equal = np.array_equal(expected, observed)
        rows.append({"name": name, "shape": list(expected.shape), "equal": bool(equal),
                     "expected_sha256": hashlib.sha256(expected.astype("<i8", copy=False).tobytes()).hexdigest(),
                     "actual_sha256": hashlib.sha256(observed.astype("<i8", copy=False).tobytes()).hexdigest()})
        if not equal:
            raise AssertionError(f"stage mismatch: {name}")
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--golden", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    frozen = json.loads((args.golden.parent / "golden-summary.json").read_text(encoding="utf-8"))
    archive_sha = hashlib.sha256(args.golden.read_bytes()).hexdigest()
    if archive_sha != frozen["stage_archive"]["sha256"]:
        raise AssertionError("frozen archive byte hash mismatch")
    saved = np.load(args.golden, allow_pickle=False)
    actual, result = full_chain(deterministic_pcm(), args.repo.resolve())
    rows = compare_frozen_arrays(saved, actual)
    frozen_rows = compare_frozen_chain(frozen["chain"], result)
    actual_boundaries = boundary_vectors()
    if exact_json_hash(frozen["boundary_vectors"]) != exact_json_hash(actual_boundaries):
        raise AssertionError("frozen boundary vectors differ")
    payload = {"status": "PASS_ALL_FROZEN_STAGES_AND_EVENTS_EXACT",
               "array_count": len(rows), "arrays": rows,
               "frozen_chain_fields_checked": frozen_rows,
               "boundary_vectors_equal": True,
               "frozen_archive_byte_sha256": archive_sha}
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(payload["status"], len(rows))


if __name__ == "__main__":
    main()
