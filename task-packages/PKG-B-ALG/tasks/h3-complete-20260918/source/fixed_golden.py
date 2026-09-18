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
COMMON_AVAILABILITY_DELAY_SAMPLES = 8
FRAC_LAG = 12
FRAC_DIR = 20
FRAC_ANGLE = 8
TWIDDLE_FRAC = 30
PAIRS = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))
PAIR_DELTAS = ((1, 0), (1, 1), (0, 1), (0, 1), (-1, 1), (-1, 0))
PAIR_LENGTH_SQ = tuple(dx * dx + dy * dy for dx, dy in PAIR_DELTAS)
# 40 mm * 48000 samples/s / 343 m/s = 1920/343 samples per edge.
# The maximum legal Q12 code is floor((1920/343)*sqrt(length_sq)*2**12).
# All physical-boundary decisions below are exact integer comparisons.
EDGE_DELAY_NUM = 1920
EDGE_DELAY_DEN = 343


def physical_limit_q12(length_sq: int) -> int:
    if length_sq not in (1, 2):
        raise ValueError("only an edge or diagonal of the frozen square is legal")
    numerator = EDGE_DELAY_NUM**2 * length_sq * (1 << FRAC_LAG) ** 2
    return math.isqrt(numerator // EDGE_DELAY_DEN**2)


def physical_tau_legal_q12(tau_q12: int, length_sq: int) -> bool:
    return abs(int(tau_q12)) <= physical_limit_q12(length_sq)


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


def lag_q12(correlation: np.ndarray, length_sq: int) -> dict:
    corr = np.asarray(correlation, dtype=np.int64)
    if corr.shape != (N,):
        raise ValueError("1024 correlation points required")
    limit_q12 = physical_limit_q12(length_sq)
    limit = (limit_q12 + (1 << FRAC_LAG) - 1) // (1 << FRAC_LAG)
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
    legal = physical_tau_legal_q12(tau, length_sq)
    competitors = [int(corr[lag % N]) for lag in lags if abs(lag - peak) > 1]
    second = max(competitors, default=0)
    margin_q15 = rne_div((center - second) << 15, max(abs(center), 1))
    return {"valid": legal, "reason": "VALID" if legal else "TAU_BOUND", "peak": peak,
            "delta_q12": delta, "tau_q12": tau, "peak_code": center,
            "separated_margin_q15": margin_q15, "physical_limit_q12": limit_q12,
            "pair_length_sq": length_sq}


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


def _delayed(signal: np.ndarray, delay: int) -> np.ndarray:
    output = np.zeros(len(signal), dtype=np.int64)
    if delay < len(signal):
        output[delay:] = signal[:-delay] if delay else signal
    return output


def control_timeline(angle_q8: int) -> list[dict]:
    """One tracker drives acquisition, discontinuity, reacquisition and expiry.

    The 1441-sample gap at 4513 must be consumed by causal_audio. The 19-degree
    switch and rejected 70-degree candidate are injected control vectors, not
    additional claims about acoustic DOA.
    """
    tracker = FixedTracker()
    rows = []
    schedule = [(N + i * 512, angle_q8, True, "repeated_synthetic_doa") for i in range(5)]
    schedule += [(4513, angle_q8, True, "injected_sample_discontinuity")]
    schedule += [(4513 + i * 512, angle_q8, True, "reacquisition_after_gap") for i in range(1, 5)]
    schedule += [(7073, 19 << FRAC_ANGLE, True, "injected_switch_19deg"),
                 (7585, 70 << FRAC_ANGLE, True, "injected_jump_70deg")]
    schedule += [(ready, None, False, "injected_no_candidate")
                 for ready in range(8097, 18100, 512)]
    for ready, angle, accepted, source in schedule:
        previous_ready = tracker.last_ready
        state = tracker.update(ready, angle, accepted)
        discontinuity = source == "injected_sample_discontinuity"
        if discontinuity and (previous_ready != 3072 or ready - previous_ready != 1441
                              or state["reason"] != "gap_reset_acquire"):
            raise AssertionError("gap vector did not reset the live tracker")
        rows.append({"ready_sample": ready,
                     "available_emit_sample": ready + COMMON_AVAILABILITY_DELAY_SAMPLES,
                     "input_angle_q8_deg": angle, "input_accepted": accepted,
                     "source": source, "discontinuity": discontinuity,
                     "input_gap_samples": ready - previous_ready if discontinuity else 0,
                     **state})
    return rows


def _weights_at(start_weights: list[int], target: int, start: int, sample: int,
                fade_samples: int) -> list[int]:
    alpha = min(1 << 12, max(0, rne_div((sample - start) << 12, fade_samples)))
    result = [rne_div(weight * ((1 << 12) - alpha) +
                      ((1 << 12) if i == target else 0) * alpha, 1 << 12)
              for i, weight in enumerate(start_weights)]
    result[0] += (1 << 12) - sum(result)
    if any(weight < 0 for weight in result):
        raise RuntimeError("nonconvex integer fade")
    return result


def causal_audio(pcm: np.ndarray, control_rows: list[dict], *,
                 delay: int = COMMON_AVAILABILITY_DELAY_SAMPLES,
                 fade_samples: int = 480) -> tuple[dict[str, np.ndarray], dict]:
    """Render one common delayed clock; no future direction may affect past PCM."""
    x = np.asarray(pcm, dtype=np.int64)
    if x.ndim != 2 or x.shape[0] != 4 or x.shape[1] <= 16682 + fade_samples + delay:
        raise ValueError("four-channel timeline must include acquisition and expiry")
    if any(row["available_emit_sample"] != row["ready_sample"] + delay
           for row in control_rows):
        raise ValueError("control and audio availability delays disagree")
    if any(left["ready_sample"] >= right["ready_sample"]
           for left, right in zip(control_rows, control_rows[1:])):
        raise ValueError("control rows must be in increasing sample order")
    beam0, manual_info = das_block(x, delay_q12_from_angle(0))
    beam19, switched_info = das_block(x, delay_q12_from_angle(19 << FRAC_ANGLE))
    bank = np.stack((_delayed(x[0], delay), _delayed(beam0, delay),
                     _delayed(beam19, delay)))
    automatic = np.zeros(x.shape[1], dtype=np.int64)
    weights = np.zeros((x.shape[1], 3), dtype=np.int64)
    targets = np.zeros(x.shape[1], dtype=np.int64)
    events = []
    start_weights = [1 << 12, 0, 0]
    target = 0
    start = 0
    expiry_emit = None
    next_event = 0
    for n in range(x.shape[1]):
        if target and expiry_emit is not None and n > expiry_emit:
            start_weights = _weights_at(start_weights, target, start, n, fade_samples)
            events.append({"kind": "EXPIRE_TO_SINGLE", "emit_sample": n,
                           "expired_at_emit_sample": expiry_emit})
            target, start, expiry_emit = 0, n, None
        while next_event < len(control_rows) and control_rows[next_event]["available_emit_sample"] <= n:
            row = control_rows[next_event]
            if row.get("discontinuity", False):
                if row["fresh_valid"] or row["state"] not in ("ACQUIRE", "SEARCH"):
                    raise AssertionError("discontinuity must invalidate the old beam")
                previous_expiry = expiry_emit
                start_weights = _weights_at(start_weights, target, start, n, fade_samples)
                target, start, expiry_emit = 0, n, None
                events.append({"kind": "DISCONTINUITY_TO_SINGLE",
                               "ready_sample": row["ready_sample"], "emit_sample": n,
                               "input_gap_samples": row["input_gap_samples"],
                               "target": 0, "previous_expiry_emit_sample": previous_expiry,
                               "new_expiry_emit_sample": None})
            elif row["fresh_valid"]:
                new_target = 1 if row["angle_q8_deg"] == 0 else 2 if row["angle_q8_deg"] == 19 << FRAC_ANGLE else None
                if new_target is None:
                    raise ValueError("unmapped injected direction")
                if new_target != target:
                    start_weights = _weights_at(start_weights, target, start, n, fade_samples)
                    target, start = new_target, n
                    events.append({"kind": "FRESH_SELECT", "ready_sample": row["ready_sample"],
                                   "emit_sample": n, "target": target})
                expiry_emit = row["valid_through_sample"] + delay
            elif row["state"] == "HOLD":
                events.append({"kind": "HOLD_NO_REFRESH", "ready_sample": row["ready_sample"],
                               "emit_sample": n, "valid_through_emit_sample": expiry_emit})
            elif row["state"] == "SEARCH" and target:
                start_weights = _weights_at(start_weights, target, start, n, fade_samples)
                target, start, expiry_emit = 0, n, None
                events.append({"kind": "SEARCH_TO_SINGLE", "ready_sample": row["ready_sample"],
                               "emit_sample": n})
            next_event += 1
        row_weights = _weights_at(start_weights, target, start, n, fade_samples)
        weights[n] = row_weights
        targets[n] = target
        automatic[n], overflow = saturate(rne_div(sum(int(w) * int(bank[i, n])
                                                      for i, w in enumerate(row_weights)), 1 << 12), 24)
        if overflow:
            raise RuntimeError("synthetic automatic output saturated")
    if np.array_equal(bank[1], automatic):
        raise RuntimeError("MANUAL_AUTO_IDENTICAL_BACKFILL_REGRESSION")
    first_fresh = next(row for row in control_rows if row["fresh_valid"])
    first_available = first_fresh["available_emit_sample"]
    if not np.array_equal(automatic[:first_available + 1], bank[0, :first_available + 1]):
        raise RuntimeError("PRE_ACQUISITION_FALLBACK_REGRESSION")
    arrays = {"audio_pcm": x, "single": bank[0], "manual": bank[1],
              "automatic": automatic, "auto_weights_q12": weights,
              "auto_target_bank": targets}
    detail = {"clock": "all outputs indexed by common physical emission sample",
              "frame_direction_ready_at_frame_end": True,
              "common_availability_delay_samples": delay, "fade_samples": fade_samples,
              "first_fresh_ready_sample": first_fresh["ready_sample"],
              "first_fresh_available_emit_sample": first_available,
              "first_nonzero_beam_weight_sample": int(np.flatnonzero(weights[:, 1:].sum(axis=1))[0]),
              "events": events, "control_rows": control_rows,
              "manual": manual_info, "switched_beam": switched_info,
              "manual_equals_automatic": False}
    return arrays, detail


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
        lag = lag_q12(correlations[k], PAIR_LENGTH_SQ[k])
        pair_rows.append(lag)
        ifft_flags.append(flags)
    doa = doa_q20(pair_rows)
    angle = doa.get("azimuth_q8_deg") if doa.get("valid") else None
    if angle is None:
        raise RuntimeError("synthetic full-chain probe did not produce a valid DOA")
    tracker_rows = control_timeline(angle)
    audio_pcm = np.tile(np.asarray(pcm, dtype=np.int64), (1, 20))
    audio_arrays, audio_detail = causal_audio(audio_pcm, tracker_rows)
    arrays = {"pcm": np.asarray(pcm, dtype=np.int64), "hann": hann_u18f17(), "windowed": windowed,
              "fft29": spectra29, "fft25_half": spectra25, "phat": phat_codes,
              "phat_mask": masks, "ifft_real": correlations, **audio_arrays}
    result = {"window_overflow": window_overflow, "adapter_overflow": adapter_overflow,
              "fft_flags": fft_flags, "ifft_flags": ifft_flags, "pairs": pair_rows, "doa": doa,
              "tracker": tracker_rows,
              "audio_timeline": audio_detail,
              "stage_shapes": {key: list(value.shape) for key, value in arrays.items()}}
    return arrays, result


def json_dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
