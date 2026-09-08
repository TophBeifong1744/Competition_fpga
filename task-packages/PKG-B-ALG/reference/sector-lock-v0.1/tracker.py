"""Direction-only cone tracker. No waveform, source truth or speaker identity input."""
from dataclasses import dataclass
import math
import numpy as np


def vector(value):
    x = np.asarray(value, dtype=float)
    if x.shape != (3,) or not np.all(np.isfinite(x)):
        raise ValueError('direction must have three finite components')
    norm = float(np.linalg.norm(x))
    if norm < 1e-12 or not math.isfinite(norm):
        raise ValueError('direction must have nonzero finite norm')
    return x / norm


def angle(a, b):
    return float(np.degrees(np.arccos(np.clip(np.dot(a, b), -1, 1))))


@dataclass(frozen=True)
class Config:
    cone_center: tuple = (1., 0., 0.)
    cone_half_angle_deg: float = 30.
    acquire_frames: int = 5
    acquire_spread_deg: float = 8.
    track_step_deg: float = 20.
    hold_ms: float = 200.
    max_input_gap_ms: float = 30.

    def __post_init__(self):
        vector(self.cone_center)
        if isinstance(self.acquire_frames, bool) or not isinstance(self.acquire_frames, int) or self.acquire_frames < 2:
            raise ValueError('acquire_frames must be an integer >= 2')
        for key in ['cone_half_angle_deg', 'acquire_spread_deg', 'track_step_deg']:
            value = getattr(self, key)
            if not math.isfinite(value) or not 0 < value <= 90:
                raise ValueError(key)
        if not math.isfinite(self.hold_ms) or self.hold_ms < 0:
            raise ValueError('hold_ms')
        if not math.isfinite(self.max_input_gap_ms) or self.max_input_gap_ms <= 0:
            raise ValueError('max_input_gap_ms')


class Tracker:
    def __init__(self, config=Config()):
        self.config = config
        self.center = vector(config.cone_center)
        self.last_input_ms = None
        self.reset()

    def reset(self):
        """Release lock; preserve monotonic input clock across manual release."""
        self.state = 'SEARCH'
        self.candidates = []
        self.direction = None
        self.last_fresh_ms = None

    def configure(self, config):
        self.config = config
        self.center = vector(config.cone_center)
        self.reset()

    def _result(self, reason, fresh=False):
        return dict(state=self.state, fresh_valid=fresh,
                    direction=self.direction.tolist() if fresh else None,
                    display_direction=self.direction.tolist() if self.direction is not None else None,
                    stale=self.state == 'HOLD', reason=reason,
                    acquire_count=len(self.candidates), last_fresh_ms=self.last_fresh_ms,
                    display_expires_at_ms=(self.last_fresh_ms+self.config.hold_ms)
                    if self.last_fresh_ms is not None else None)

    def update(self, timestamp_ms, estimate, baseline_valid):
        t = float(timestamp_ms)
        if not math.isfinite(t) or t < 0 or (self.last_input_ms is not None and t <= self.last_input_ms):
            raise ValueError('timestamp must be finite, nonnegative and strictly increasing')
        gap_reset = self.last_input_ms is not None and t-self.last_input_ms > self.config.max_input_gap_ms
        if gap_reset:
            self.reset()
        self.last_input_ms = t
        if self.direction is not None and t-self.last_fresh_ms > self.config.hold_ms:
            self.reset()
        candidate = None
        reason = 'baseline_rejected'
        if baseline_valid:
            try:
                candidate = vector(estimate)
                reason = 'in_cone'
            except (ValueError, TypeError):
                reason = 'invalid_direction'
            if candidate is not None and angle(self.center, candidate) > self.config.cone_half_angle_deg + 1e-10:
                candidate, reason = None, 'outside_cone'
        if self.direction is not None:
            if candidate is not None and angle(self.direction, candidate) <= self.config.track_step_deg + 1e-10:
                self.direction = candidate
                self.last_fresh_ms = t
                self.state = 'LOCKED'
                return self._result('track_update', True)
            self.state = 'HOLD'
            return self._result('track_jump' if candidate is not None else reason)
        if candidate is None:
            self.candidates = []
            self.state = 'SEARCH'
            return self._result(reason)
        # Every acquisition direction must be close to every previous one;
        # consecutive small steps alone must not accept arbitrary accumulated drift.
        if any(angle(candidate, old) > self.config.acquire_spread_deg + 1e-10 for old in self.candidates):
            self.candidates = []
        self.candidates.append(candidate)
        self.state = 'ACQUIRE'
        if len(self.candidates) >= self.config.acquire_frames:
            self.direction = vector(np.mean(self.candidates, axis=0))
            self.candidates = []
            self.state = 'LOCKED'
            self.last_fresh_ms = t
            return self._result('acquired', True)
        return self._result('gap_reset_acquire' if gap_reset else 'acquiring')
