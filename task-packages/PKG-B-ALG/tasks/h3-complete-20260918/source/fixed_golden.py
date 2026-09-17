"""Portable four-channel integer golden candidate.

This is an executable arithmetic specification, not AMD FFT RTL equivalence.
The AMD 29-bit forward FFT and 25-bit inverse FFT evidence are kept separate in
the budget.  Every custom arithmetic node uses round-to-nearest ties-to-even;
custom overflow saturates and records a flag.  A vendor-IP overflow would make
the frame invalid and is never repaired by this model.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np

N = 1024
FRAC_LAG = 12
FRAC_DIR = 20
FRAC_ANGLE = 8
TWIDDLE_FRAC = 30
PAIRS = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))
PAIR_DELTAS = ((1, 0), (1, 1), (0, 1), (0, 1), (-1, 1), (-1, 0))
BOUNDS = tuple(math.hypot(dx * 0.04, dy * 0.04) * 48000 / 343 for dx, dy in PAIR_DELTAS)


def rne_div(n: int, d: int) -> int:
    if d <= 0:
        raise ValueError("positive denominator required")
    sign = -1 if n < 0 else 1
    q, r = divmod(abs(n), d)
    if 2 * r > d or (2 * r == d and q & 1):
        q += 1
    return sign * q


def rne_shift(n: int, shift: int) -> int:
    return rne_div(n, 1 << shift) if shift >= 0 else n << -shift


def saturate(n: int, width: int, signed: bool = True) -> tuple[int, bool]:
    lo = -(1 << (width - 1)) if signed else 0
    hi = (1 << (width - int(signed))) - 1
    return max(lo, min(hi, n)), not lo <= n <= hi


def hann_u18f17() -> np.ndarray:
    values = [round(0.5 * (1.0 - math.cos(2.0 * math.pi * i / (N - 1))) * (1 << 17)) for i in range(N)]
    return np.asarray(values, dtype=np.int64)


def window_pcm(pcm: np.ndarray, coefficients: np.ndarray | None = None) -> tuple[np.ndarray, int]:
    x = np.asarray(pcm, dtype=np.int64)
    if x.shape != (4, N):
        raise ValueError("expected four channels by 1024 samples")
    if np.any(x < -(1 << 23)) or np.any(x > (1 << 23) - 1):
        raise ValueError("PCM outside signed24")
    c = hann_u18f17() if coefficients is None else np.asarray(coefficients, dtype=np.int64)
    if c.shape != (N,) or np.any(c < 0) or np.any(c > (1 << 17)):
        raise ValueError("invalid U18F17 Hann table")
    out = np.empty_like(x)
    overflow = 0
    for ch in range(4):
        for i in range(N):
            v, ov = saturate(rne_shift(int(x[ch, i]) * int(c[i]), 17), 24)
            out[ch, i] = v
            overflow += int(ov)
    return out, overflow


def _bit_reverse(values: list[tuple[int, int]]) -> list[tuple[int, int]]:
    bits = int(math.log2(len(values)))
    out = [None] * len(values)
    for i, value in enumerate(values):
        r = int(f"{i:0{bits}b}"[::-1], 2)
        out[r] = value
    return out


def fixed_fft(samples: Iterable[tuple[int, int]], *, inverse: bool, width: int) -> tuple[np.ndarray, dict]:
    """Radix-2 portable golden: Q30 twiddles and one RNE right shift/stage."""
    values = [(int(a), int(b)) for a, b in samples]
    if len(values) != N:
        raise ValueError("1024 complex samples required")
    lo, hi = -(1 << (width - 1)), (1 << (width - 1)) - 1
    if any(not (lo <= a <= hi and lo <= b <= hi) for a, b in values):
        raise ValueError("FFT input outside configured width")
    values = _bit_reverse(values)
    overflow = 0
    stage_hashes = []
    size = 2
    direction = 1.0 if inverse else -1.0
    while size <= N:
        half = size // 2
        table = []
        for j in range(half):
            angle = direction * 2.0 * math.pi * j / size
            table.append((round(math.cos(angle) * (1 << TWIDDLE_FRAC)),
                          round(math.sin(angle) * (1 << TWIDDLE_FRAC))))
        for base in range(0, N, size):
            for j, (wr, wi) in enumerate(table):
                ar, ai = values[base + j]
                br, bi = values[base + j + half]
                tr = rne_shift(wr * br - wi * bi, TWIDDLE_FRAC)
                ti = rne_shift(wr * bi + wi * br, TWIDDLE_FRAC)
                candidates = ((ar + tr, ai + ti), (ar - tr, ai - ti))
                for offset, pair in ((j, candidates[0]), (j + half, candidates[1])):
                    rr, ov0 = saturate(rne_shift(pair[0], 1), width)
                    ii, ov1 = saturate(rne_shift(pair[1], 1), width)
                    values[base + offset] = (rr, ii)
                    overflow += int(ov0) + int(ov1)
        stage_bytes = np.asarray(values, dtype="<i8").tobytes()
        stage_hashes.append(hashlib.sha256(stage_bytes).hexdigest())
        size *= 2
    return np.asarray(values, dtype=np.int64), {"overflow_count": overflow, "stage_sha256": stage_hashes}


def adapt_fft29_to_s25(fft29: np.ndarray) -> tuple[np.ndarray, int]:
    out = np.empty_like(fft29)
    overflow = 0
    for index, value in np.ndenumerate(fft29):
        q, ov = saturate(rne_shift(int(value), 4), 25)
        out[index] = q
        overflow += int(ov)
    return out, overflow


def _load_phat_model(root: Path):
    path = root / "task-packages/PKG-B-ALG/tasks/phat-fixed-03/phat_model.py"
    spec = importlib.util.spec_from_file_location("h3_phat_model", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def conjugate_complete(half: np.ndarray) -> np.ndarray:
    if half.shape != (513, 2):
        raise ValueError("513 complex bins required")
    full = np.empty((N, 2), dtype=np.int64)
    full[:513] = half
    for k in range(1, 512):
        full[N - k, 0] = half[k, 0]
        full[N - k, 1] = -half[k, 1]
    return full


def lag_q12(correlation: np.ndarray, bound: float) -> dict:
    corr = np.asarray(correlation, dtype=np.int64)
    if corr.shape != (N,):
        raise ValueError("1024 correlation points required")
    limit = math.ceil(bound)
    lags = list(range(-limit, limit + 1))
    peak = max(lags, key=lambda lag: (int(corr[lag % N]), -lags.index(lag)))
    center = int(corr[peak % N])
    left = int(corr[(peak - 1) % N])
    right = int(corr[(peak + 1) % N])
    denominator = left - 2 * center + right
    numerator = (left - right) << 11
    if denominator < 0:
        numerator, denominator = -numerator, -denominator
    delta = 0 if denominator == 0 else rne_div(numerator, denominator)
    delta = max(-(1 << 11), min(1 << 11, delta))
    tau = peak * (1 << FRAC_LAG) + delta
    legal = abs(tau) <= round((bound + 0.05) * (1 << FRAC_LAG))
    competitors = [int(corr[lag % N]) for lag in lags if abs(lag - peak) > 1]
    second = max(competitors, default=0)
    margin_q15 = rne_div((center - second) << 15, max(abs(center), 1))
    return {"valid": legal, "reason": "VALID" if legal else "TAU_BOUND", "peak": peak,
            "delta_q12": delta, "tau_q12": tau, "peak_code": center,
            "separated_margin_q15": margin_q15}


def doa_q20(pair_lags: list[dict], pair_deltas=PAIR_DELTAS) -> dict:
    """Solve the fixed-point 2-D least-squares direction vector.

    Production calls use the frozen six square-array baselines.  The optional
    geometry argument exists so the checker can exercise the rank-deficient
    failure branch, which is structurally unreachable after selecting any
    three distinct baselines from the frozen square geometry.
    """
    if len(pair_lags) != len(pair_deltas):
        raise ValueError("one geometry row is required for every pair lag")
    valid = [(pair_deltas[k], int(row["tau_q12"])) for k, row in enumerate(pair_lags) if row.get("valid")]
    if len(valid) < 3:
        return {"valid": False, "reason": "INSUFFICIENT_PAIRS", "valid_pairs": len(valid)}
    sxx = sum(dx * dx for (dx, _), _tau in valid)
    syy = sum(dy * dy for (_, dy), _tau in valid)
    sxy = sum(dx * dy for (dx, dy), _tau in valid)
    bx = sum(dx * tau for (dx, _), tau in valid)
    by = sum(dy * tau for (_, dy), tau in valid)
    determinant = sxx * syy - sxy * sxy
    if determinant == 0:
        return {"valid": False, "reason": "RANK_DEFICIENT", "valid_pairs": len(valid)}
    # u = inv(M)*v/a, a=(0.04*48000/343)=1920/343 samples.
    ux = rne_div((syy * bx - sxy * by) * 343 * (1 << (FRAC_DIR - FRAC_LAG)), determinant * 1920)
    uy = rne_div((sxx * by - sxy * bx) * 343 * (1 << (FRAC_DIR - FRAC_LAG)), determinant * 1920)
    residual_sq = 0
    for (dx, dy), tau in valid:
        predicted = rne_div((dx * ux + dy * uy) * 1920 * (1 << FRAC_LAG), 343 * (1 << FRAC_DIR))
        residual_sq += (predicted - tau) ** 2
    norm_sq = ux * ux + uy * uy
    residual_ok = residual_sq <= len(valid) * (1 << (FRAC_LAG - 1)) ** 2
    norm_ok = round(0.1 * (1 << FRAC_DIR)) ** 2 <= norm_sq <= round(1.3 * (1 << FRAC_DIR)) ** 2
    accepted = residual_ok and norm_ok
    return {"valid": accepted, "reason": "VALID" if accepted else "GEOMETRY_REJECT",
            "valid_pairs": len(valid), "ux_q20": ux, "uy_q20": uy,
            "residual_sum_square_q24": residual_sq, "norm_square_q40": norm_sq,
            "azimuth_q8_deg": atan2_q8(uy, ux) if ux or uy else None}


_CORDIC_ATAN_Q16 = tuple(round(math.degrees(math.atan(2.0 ** -i)) * (1 << 16)) for i in range(24))


def atan2_q8(y: int, x: int) -> int:
    if x == 0 and y == 0:
        raise ValueError("zero vector")
    offset = 0
    if x < 0:
        original_y = y
        x, y = -x, -y
        offset = (180 if original_y >= 0 else -180) << 16
    angle = 0
    for i, step in enumerate(_CORDIC_ATAN_Q16):
        old_x, old_y = x, y
        if old_y > 0:
            x = old_x + (old_y >> i)
            y = old_y - (old_x >> i)
            angle += step
        elif old_y < 0:
            x = old_x - (old_y >> i)
            y = old_y + (old_x >> i)
            angle -= step
    return rne_shift(angle + offset, 16 - FRAC_ANGLE)


@dataclass
class TrackerConfig:
    half_angle_q8: int = 30 << 8
    acquire_frames: int = 5
    acquire_spread_q8: int = 8 << 8
    track_step_q8: int = 20 << 8
    hold_samples: int = 9600
    max_gap_samples: int = 1440


class FixedTracker:
    def __init__(self, config: TrackerConfig = TrackerConfig()):
        self.config = config
        self.last_ready = None
        self.reset()

    def reset(self):
        self.state = "SEARCH"
        self.candidates = []
        self.angle = None
        self.last_fresh = None

    @staticmethod
    def distance(a: int, b: int) -> int:
        full = 360 << FRAC_ANGLE
        delta = abs(a - b) % full
        return min(delta, full - delta)

    def update(self, ready_sample: int, angle_q8: int | None, accepted: bool) -> dict:
        if type(ready_sample) is not int or ready_sample < 0 or (self.last_ready is not None and ready_sample <= self.last_ready):
            raise ValueError("strictly increasing nonnegative sample clock required")
        gap = self.last_ready is not None and ready_sample - self.last_ready > self.config.max_gap_samples
        if gap:
            self.reset()
        self.last_ready = ready_sample
        if self.angle is not None and ready_sample - self.last_fresh > self.config.hold_samples:
            self.reset()
        candidate = angle_q8 if accepted and angle_q8 is not None and abs(angle_q8) <= self.config.half_angle_q8 else None
        if self.angle is not None:
            if candidate is not None and self.distance(self.angle, candidate) <= self.config.track_step_q8:
                self.angle, self.last_fresh, self.state = candidate, ready_sample, "LOCKED"
                return self.result("track_update", True)
            self.state = "HOLD"
            return self.result("track_jump" if candidate is not None else "candidate_rejected", False)
        if candidate is None:
            self.candidates = []
            self.state = "SEARCH"
            return self.result("candidate_rejected", False)
        if any(self.distance(candidate, old) > self.config.acquire_spread_q8 for old in self.candidates):
            self.candidates = []
        self.candidates.append(candidate)
        self.state = "ACQUIRE"
        if len(self.candidates) >= self.config.acquire_frames:
            self.angle = rne_div(sum(self.candidates), len(self.candidates))
            self.candidates = []
            self.last_fresh = ready_sample
            self.state = "LOCKED"
            return self.result("acquired", True)
        return self.result("gap_reset_acquire" if gap else "acquiring", False)

    def result(self, reason: str, fresh: bool) -> dict:
        return {"state": self.state, "fresh_valid": fresh, "angle_q8_deg": self.angle if fresh else None,
                "display_angle_q8_deg": self.angle, "reason": reason,
                "last_fresh_sample": self.last_fresh,
                "valid_through_sample": None if self.last_fresh is None else self.last_fresh + self.config.hold_samples}


def delay_q12_from_angle(angle_q8: int) -> list[int]:
    angle = (angle_q8 / (1 << FRAC_ANGLE)) * math.pi / 180.0
    ux, uy = math.cos(angle), math.sin(angle)
    positions = ((0, 0), (1, 0), (1, 1), (0, 1))
    scale = 0.04 * 48000 / 343
    return [round((x * ux + y * uy) * scale * (1 << FRAC_LAG)) for x, y in positions]


def das_block(pcm: np.ndarray, delays_q12: list[int]) -> tuple[np.ndarray, dict]:
    x = np.asarray(pcm, dtype=np.int64)
    if x.ndim != 2 or x.shape[0] != 4 or len(delays_q12) != 4:
        raise ValueError("four channels and four delays required")
    out = np.zeros(x.shape[1], dtype=np.int64)
    saturation = 0
    for n in range(x.shape[1]):
        acc = 0
        for ch, delay in enumerate(delays_q12):
            position = n * (1 << FRAC_LAG) - int(delay)
            left = position // (1 << FRAC_LAG)
            frac = position - left * (1 << FRAC_LAG)
            a = int(x[ch, left]) if 0 <= left < x.shape[1] else 0
            b = int(x[ch, left + 1]) if 0 <= left + 1 < x.shape[1] else 0
            acc += a * ((1 << FRAC_LAG) - frac) + b * frac
        value, ov = saturate(rne_div(acc, 4 << FRAC_LAG), 24)
        out[n] = value
        saturation += int(ov)
    return out, {"saturation_count": saturation, "delays_q12": [int(v) for v in delays_q12]}


def full_chain(pcm: np.ndarray, root: Path) -> tuple[dict, dict]:
    windowed, window_overflow = window_pcm(pcm)
    spectra29 = np.empty((4, N, 2), dtype=np.int64)
    fft_flags = []
    for ch in range(4):
        inputs = [(int(value) << 4, 0) for value in windowed[ch]]
        spectra29[ch], flags = fixed_fft(inputs, inverse=False, width=29)
        fft_flags.append(flags)
    spectra25, adapter_overflow = adapt_fft29_to_s25(spectra29[:, :513])
    phat = _load_phat_model(root)
    band = [7 <= k <= 85 for k in range(513)]
    phat_codes = np.zeros((6, 513, 2), dtype=np.int64)
    masks = np.zeros((6, 513), dtype=np.uint8)
    correlations = np.zeros((6, N), dtype=np.int64)
    pair_rows = []
    ifft_flags = []
    for k, (i, j) in enumerate(PAIRS):
        row = phat.phat_pair(spectra25[i].tolist(), spectra25[j].tolist(), band,
                             ip_overflow=bool(window_overflow or adapter_overflow or any(f["overflow_count"] for f in fft_flags)))
        masks[k] = np.asarray(row["mask"], dtype=np.uint8)
        if not row["valid"]:
            pair_rows.append({"valid": False, "reason": row["reason"]})
            ifft_flags.append({"overflow_count": 0, "not_run": True})
            continue
        phat_codes[k] = np.asarray(row["output"], dtype=np.int64)
        corr_complex, flags = fixed_fft(conjugate_complete(phat_codes[k]), inverse=True, width=25)
        correlations[k] = corr_complex[:, 0]
        lag = lag_q12(correlations[k], BOUNDS[k])
        pair_rows.append(lag)
        ifft_flags.append(flags)
    doa = doa_q20(pair_rows)
    angle = doa.get("azimuth_q8_deg") if doa.get("valid") else None
    tracker = FixedTracker()
    tracker_rows = []
    for frame_index in range(5):
        tracker_rows.append(tracker.update(N + frame_index * 512, angle, doa.get("valid", False)))
    manual, manual_info = das_block(pcm, delay_q12_from_angle(0))
    automatic, automatic_info = das_block(pcm, delay_q12_from_angle(tracker.angle or 0))
    arrays = {"pcm": np.asarray(pcm, dtype=np.int64), "hann": hann_u18f17(), "windowed": windowed,
              "fft29": spectra29, "fft25_half": spectra25, "phat": phat_codes,
              "phat_mask": masks, "ifft_real": correlations,
              "single": np.asarray(pcm[0], dtype=np.int64), "manual": manual, "automatic": automatic}
    result = {"window_overflow": window_overflow, "adapter_overflow": adapter_overflow,
              "fft_flags": fft_flags, "ifft_flags": ifft_flags, "pairs": pair_rows, "doa": doa,
              "tracker": tracker_rows, "manual": manual_info, "automatic": automatic_info,
              "stage_shapes": {key: list(value.shape) for key, value in arrays.items()}}
    return arrays, result


def json_dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
