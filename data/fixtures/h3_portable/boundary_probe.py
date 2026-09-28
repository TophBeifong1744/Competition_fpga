"""Narrow product-boundary probe; expected values are independent integers."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if a.out.exists():
        raise FileExistsError(a.out)
    sys.path.insert(0, str(a.repo / "models/python"))
    from soundsight_h3_portable.bindings import Bindings

    bound = Bindings(a.repo)
    values = np.zeros((4, 513, 2), dtype=np.int64)
    values[0, 0, 0] = (1 << 28) - 1
    values[0, 1, 0] = 8
    values[0, 2, 0] = -8
    values[0, 3, 0] = 24
    values[0, 4, 0] = -24
    observed, overflow_count = bound.guards.checked_adapter(values, bound.fg.adapt_fft29_to_s25)
    independent = {
        "positive_max_s29": {"output": [0, 0], "overflow_components": [True, False],
                               "numeric_valid": False},
        "tie_even_codes": [0, 0, 2, -2],
    }
    actual = {"positive_max_s29": list(map(int, observed[0, 0])),
              "overflow_count": int(overflow_count),
              "tie_even_codes": [int(observed[0, k, 0]) for k in range(1, 5)]}
    result = {"scope": "direct bound fixed4 software adapter, not 8 PCM FFT transactions",
              "expected_from_B_r2_B14_02": independent, "observed": actual,
              "rne_ties_match": actual["tie_even_codes"] == independent["tie_even_codes"],
              "atomic_placeholder_match": actual["positive_max_s29"] ==
                                          independent["positive_max_s29"]["output"],
              "per_component_flags_exposed": False}
    a.out.mkdir()
    (a.out / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0 if result["rne_ties_match"] and result["atomic_placeholder_match"] else 1


if __name__ == "__main__":
    sys.exit(main())
