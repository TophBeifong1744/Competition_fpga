"""Experimental capture-only variant; original tracker remains unchanged."""
from collections import deque
from dataclasses import dataclass
import math
import numpy as np
from sector_tracker import Tracker,Config,vector,angle
from six_mic_track import TrackingSession,config_from_dict
from dataclasses import asdict


@dataclass(frozen=True)
class CaptureConfig:
    required:int=5
    window_frames:int=12
    max_span_ms:float=120.

    def __post_init__(self):
        if type(self.required) is not int or type(self.window_frames) is not int or not 2<=self.required<=self.window_frames<=64:
            raise ValueError('require 2 <= quorum <= window <= 64')
        if type(self.max_span_ms) not in (int,float) or not math.isfinite(self.max_span_ms) or self.max_span_ms<=0:
            raise ValueError('max_span_ms must be positive finite, not bool')


class QuorumTracker(Tracker):
    def __init__(self,config=Config(),capture=CaptureConfig()):
        self.capture=capture
        super().__init__(config)

    def reset(self):
        super().reset()
        self.history=deque(maxlen=self.capture.window_frames)

    def update(self,timestamp_ms,estimate,baseline_valid):
        t=float(timestamp_ms)
        if not math.isfinite(t) or t<0 or (self.last_input_ms is not None and t<=self.last_input_ms):
            raise ValueError('timestamp must be finite, nonnegative and strictly increasing')
        gap=self.last_input_ms is not None and t-self.last_input_ms>self.config.max_input_gap_ms
        if gap:self.reset()
        self.last_input_ms=t
        if self.direction is not None and t-self.last_fresh_ms>self.config.hold_ms:self.reset()
        candidate=None;reason='baseline_rejected'
        if baseline_valid:
            try:candidate=vector(estimate);reason='in_cone'
            except (ValueError,TypeError):reason='invalid_direction'
            if candidate is not None and angle(self.center,candidate)>self.config.cone_half_angle_deg+1e-10:
                candidate=None;reason='outside_cone'
        # Keep locked updates, HOLD and release thresholds identical to the reference.
        if self.direction is not None:
            if candidate is not None and angle(self.direction,candidate)<=self.config.track_step_deg+1e-10:
                self.direction=candidate;self.last_fresh_ms=t;self.state='LOCKED'
                return self._result('track_update',True)
            self.state='HOLD'
            return self._result('track_jump' if candidate is not None else reason)
        self.history.append((t,candidate))
        while self.history and t-self.history[0][0]>self.capture.max_span_ms:self.history.popleft()
        self.candidates=[]
        if candidate is None:
            self.state='SEARCH'
            return self._result(reason)
        # Require the current candidate. Each selected older direction must agree
        # with all already selected directions. Greedy order is newest to oldest.
        selected=[candidate]
        for _,old in list(self.history)[:-1][::-1]:
            if old is not None and all(angle(old,other)<=self.config.acquire_spread_deg+1e-10 for other in selected):
                selected.append(old)
                if len(selected)>=self.capture.required:break
        self.candidates=selected;self.state='ACQUIRE'
        if len(selected)>=self.capture.required:
            self.direction=vector(np.mean(selected,axis=0));self.last_fresh_ms=t
            self.state='LOCKED';self.candidates=[];self.history.clear()
            return self._result('acquired',True)
        return self._result('gap_reset_acquire' if gap else 'quorum_acquiring')


class QuorumSession(TrackingSession):
    """Reuse the established frame-clock/reset adapter for the experimental tracker."""
    def __init__(self,config=Config(),capture=CaptureConfig()):
        self.tracker=QuorumTracker(config_from_dict(asdict(config)),capture)
