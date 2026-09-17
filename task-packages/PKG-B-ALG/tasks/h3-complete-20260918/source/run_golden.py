"""Generate a new, non-overwriting H3 software-golden run."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform

import numpy as np

from fixed_golden import (BOUNDS, FRAC_LAG, FixedTracker, TrackerConfig, doa_q20,
                          full_chain, json_dump, lag_q12, rne_div, saturate)
from presence import evaluate as presence


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def deterministic_pcm() -> np.ndarray:
    state = 0x13579BDF
    source = []
    for _ in range(1040):
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        source.append(((state >> 8) & 0xFFFF) - 32768)
    source = np.asarray(source, dtype=np.int64) * 32
    pcm = np.zeros((4, 1024), dtype=np.int64)
    # mic1/mic2 are six samples later than mic0/mic3: deterministic +X-like probe.
    pcm[0] = source[8:1032]
    pcm[3] = source[8:1032]
    pcm[1] = source[14:1038]
    pcm[2] = source[14:1038]
    return pcm


def boundary_vectors() -> dict:
    zero_lags = [{"valid": True, "tau_q12": 0} for _ in range(6)]
    rank_rows = [{"valid": True, "tau_q12": 0} for _ in range(3)]
    rank_geometry = ((1, 0), (2, 0), (3, 0))
    tracker = FixedTracker(TrackerConfig())
    trace = [tracker.update(1024 + i * 512, 0, True) for i in range(5)]
    trace.append(tracker.update(1024 + 5 * 512, 19 << 8, True))
    trace.append(tracker.update(1024 + 5 * 512 + 9601, None, False))
    return {
        "rounding": {"positive_half_even": rne_div(5, 2), "positive_half_odd": rne_div(7, 2),
                     "negative_half_even": rne_div(-5, 2), "negative_half_odd": rne_div(-7, 2)},
        "saturation": {"positive": saturate(1 << 23, 24), "negative": saturate(-(1 << 23) - 1, 24)},
        "presence": {"zero": presence(np.zeros((1024, 4), dtype=np.int64)),
                     "low": presence(np.ones((1024, 4), dtype=np.int64) * 2047),
                     "positive_endpoint": presence(np.ones((1024, 4), dtype=np.int64) * ((1 << 23) - 1)),
                     "negative_endpoint": presence(np.ones((1024, 4), dtype=np.int64) * (-(1 << 23))),
                     "stream_error": presence(np.ones((1024, 4), dtype=np.int64) * 5000, stream_error=True)},
        "doa": {"zero_norm": doa_q20(zero_lags),
                "rank_deficient": doa_q20(rank_rows, rank_geometry)},
        "tracker": trace,
        "lag_bounds_q12": [round(v * (1 << FRAC_LAG)) for v in BOUNDS]
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    pcm = deterministic_pcm()
    arrays, chain = full_chain(pcm, args.repo.resolve())
    stages = args.out / "golden-stages.npz"
    np.savez_compressed(stages, **arrays)
    result = {"status": "PASS_PORTABLE_SOFTWARE_INTEGER_GOLDEN_ONLY",
              "environment": {"python": platform.python_version(), "numpy": np.__version__, "platform": platform.platform()},
              "stage_archive": {"file": stages.name, "sha256": sha(stages),
                                  "arrays": {key: {"shape": list(value.shape), "dtype": str(value.dtype),
                                                    "sha256": hashlib.sha256(value.astype("<i8", copy=False).tobytes()).hexdigest()}
                                             for key, value in arrays.items()}},
              "chain": chain, "boundary_vectors": boundary_vectors(),
              "limits": ["Portable integer model is not an AMD FFT bit-exact replacement.",
                         "Synthetic vectors verify arithmetic/control coverage, not acoustic accuracy.",
                         "RTL, integrated timing, real-time audio output and H3 acceptance are NOT_RUN."]}
    json_dump(args.out / "golden-summary.json", result)
    json_dump(args.out / "SHA256.json", {p.name: sha(p) for p in sorted(args.out.iterdir()) if p.is_file()})
    print(json.dumps({"status": result["status"], "arrays": len(arrays),
                      "doa_valid": chain["doa"].get("valid", False)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
