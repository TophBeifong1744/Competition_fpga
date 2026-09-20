"""Frozen-before-scoring format-scale target-presence candidate."""
from __future__ import annotations

import math
import numpy as np


def evaluate(pcm, *, rms_min_codes=2048, peak_min_codes=4096,
             minimum_active_channels=3, stream_error=False, clip_flag=False):
    x = np.asarray(pcm, dtype=np.int64)
    if x.ndim != 2 or x.shape[1] != 4 or x.shape[0] == 0:
        raise ValueError("time-by-four-channel PCM required")
    if np.any(x < -(1 << 23)) or np.any(x > (1 << 23) - 1):
        raise ValueError("PCM outside signed24")
    sum_squares = [sum(int(v) * int(v) for v in x[:, ch]) for ch in range(4)]
    peaks = [max(abs(int(v)) for v in x[:, ch]) for ch in range(4)]
    active = [ss >= len(x) * rms_min_codes * rms_min_codes and peak >= peak_min_codes
              for ss, peak in zip(sum_squares, peaks)]
    reason = "PRESENT"
    present = True
    if stream_error:
        present, reason = False, "STREAM_ERROR"
    elif clip_flag:
        present, reason = False, "CLIP_FLAG"
    elif sum(active) < minimum_active_channels:
        present, reason = False, "LOW_ENERGY"
    return {"present": present, "reason": reason, "active_channels": sum(active),
            "active_mask": active, "rms_codes_floor": [math.isqrt(ss // len(x)) for ss in sum_squares],
            "peak_abs_codes": peaks, "stream_error": bool(stream_error), "clip_flag": bool(clip_flag)}
