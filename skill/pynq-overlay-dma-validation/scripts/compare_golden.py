#!/usr/bin/env python3
"""Compare actual output with a portable golden file and emit JSON evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare_bytes(expected: bytes, actual: bytes) -> dict[str, Any]:
    common = min(len(expected), len(actual))
    mismatches = [index for index in range(common) if expected[index] != actual[index]]
    mismatch_count = len(mismatches) + abs(len(expected) - len(actual))
    first = mismatches[0] if mismatches else (common if len(expected) != len(actual) else None)
    return {
        "expected_count": len(expected),
        "actual_count": len(actual),
        "mismatch_count": mismatch_count,
        "first_mismatch": first,
        "max_absolute_error": None,
    }


def numeric_list(path: Path) -> list[float]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in value):
        raise ValueError(f"{path} must contain a flat JSON array of numbers")
    numbers = [float(item) for item in value]
    if not all(math.isfinite(item) for item in numbers):
        raise ValueError(f"{path} contains NaN or infinity")
    return numbers


def compare_numbers(expected: list[float], actual: list[float], atol: float, rtol: float) -> dict[str, Any]:
    common = min(len(expected), len(actual))
    mismatch_indexes: list[int] = []
    maximum = 0.0
    for index in range(common):
        error = abs(actual[index] - expected[index])
        maximum = max(maximum, error)
        if error > atol + rtol * abs(expected[index]):
            mismatch_indexes.append(index)
    mismatch_count = len(mismatch_indexes) + abs(len(expected) - len(actual))
    first = mismatch_indexes[0] if mismatch_indexes else (common if len(expected) != len(actual) else None)
    return {
        "expected_count": len(expected),
        "actual_count": len(actual),
        "mismatch_count": mismatch_count,
        "first_mismatch": first,
        "max_absolute_error": maximum,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected", required=True, type=Path)
    parser.add_argument("--actual", required=True, type=Path)
    parser.add_argument("--format", choices=("bytes", "json-numbers"), default="bytes")
    parser.add_argument("--atol", type=float, default=0.0)
    parser.add_argument("--rtol", type=float, default=0.0)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.atol < 0 or args.rtol < 0:
        raise SystemExit("atol and rtol must be non-negative")
    expected_path = args.expected.resolve()
    actual_path = args.actual.resolve()
    if args.format == "bytes":
        comparison = compare_bytes(expected_path.read_bytes(), actual_path.read_bytes())
    else:
        comparison = compare_numbers(numeric_list(expected_path), numeric_list(actual_path), args.atol, args.rtol)
    report = {
        "tool": "pynq-overlay-dma-validation/compare_golden.py",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if comparison["mismatch_count"] == 0 else "FAIL",
        "format": args.format,
        "atol": args.atol,
        "rtol": args.rtol,
        "expected_path": str(expected_path),
        "actual_path": str(actual_path),
        "expected_sha256": sha256(expected_path),
        "actual_sha256": sha256(actual_path),
        **comparison,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
