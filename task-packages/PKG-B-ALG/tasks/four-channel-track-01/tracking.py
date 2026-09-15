"""Offline diagnostic adapter; no target-presence or production DOA acceptance.

Reuse the frozen tracker. A planar projection supplies azimuth under an explicit
horizontal assumption. route_at is a streaming, last-snapshot contract, not a
retrospective audio renderer. Call begin_interval at a clean interval boundary,
even before its first full frame; query only for available samples in that interval.
"""
import copy
import math
from pathlib import Path
import sys

MODEL = Path(__file__).resolve().parents[2] / 'payload/model/python'
sys.path.insert(0, str(MODEL))
from sector_tracker import Config, Tracker


def horizontal_candidate(projection):
    # direction_accepted stays false in the upstream diagnostic. Do not promote
    # an advisory-consistency flag into acoustic or target-presence acceptance.
    if projection.get('advisory_consistent') is not True:
        return None, projection.get('reason', 'NO_CONSISTENT_PROJECTION')
    az = projection.get('advisory_azimuth_deg')
    if isinstance(az, bool) or not isinstance(az, (int, float)) or not math.isfinite(az):
        return None, 'NONFINITE_OR_MISSING_AZIMUTH'
    a = math.radians(az)
    return [math.cos(a), math.sin(a), 0.0], 'HORIZONTAL_DIAGNOSTIC_CANDIDATE'


class DiagnosticSession:
    def __init__(self, config=Config()):
        self.tracker = Tracker(config)
        self.interval_index = None
        self.snapshot = None
        self.ready_ms = None

    def begin_interval(self, interval_index):
        if type(interval_index) is not int or interval_index < 0:
            raise ValueError('nonnegative integer interval index required')
        self.tracker.reset()
        self.interval_index = interval_index
        self.snapshot = None
        self.ready_ms = None

    def update(self, ready_ms, projection, *, interval_index, reset_before=False):
        # Validate the clock BEFORE resetting, so a bad event does not discard lock.
        t = float(ready_ms)
        last = self.tracker.last_input_ms
        if not math.isfinite(t) or t < 0 or (last is not None and t <= last):
            raise ValueError('ready time must be finite and strictly increasing')
        if type(interval_index) is not int or interval_index < 0:
            raise ValueError('nonnegative integer interval index required')
        direction, reason = horizontal_candidate(projection)
        if reset_before or interval_index != self.interval_index:
            self.begin_interval(interval_index)
        result = self.tracker.update(t, direction, direction is not None)
        self.ready_ms = t
        self.snapshot = result
        return dict(candidate_direction=direction, candidate_reason=reason,
                    numeric_candidate_valid=direction is not None,
                    target_presence='unknown', direction_accepted=False,
                    horizontal_assumption=True, tracker=copy.deepcopy(result),
                    diagnostic_route=self.route_at(t, interval_index=interval_index))

    def route_at(self, timestamp_ms, *, interval_index):
        """Read the last snapshot without refreshing its lifetime.

        An expiry is inclusive, matching Tracker's existing `age > hold_ms` rule.
        A call after expiry returns single-mic even with no new frame. Past queries
        before the latest frame's ready time fail closed to single-mic; playback
        history must be built by replaying events in time order.
        """
        t = float(timestamp_ms)
        if not math.isfinite(t) or t < 0:
            raise ValueError('finite nonnegative route timestamp required')
        if type(interval_index) is not int or interval_index < 0:
            raise ValueError('nonnegative integer interval index required')
        route = dict(mode='single', single_channel='mic0', direction=None,
                     diagnostic_only=True, direction_accepted=False,
                     query_ms=t, measurement_ready_ms=self.ready_ms,
                     fresh_at_query=False, valid_through_ms=None)
        if interval_index != self.interval_index or self.snapshot is None:
            return route | dict(reason='NO_RESULT_IN_INTERVAL')
        if t < self.ready_ms:
            return route | dict(reason='FRAME_NOT_READY')
        result = self.snapshot
        expiry = result['display_expires_at_ms']
        if result['display_direction'] is None:
            return route | dict(reason=result['reason'])
        if expiry is None or t > expiry:
            return route | dict(reason='DIRECTION_EXPIRED')
        return route | dict(
            mode='hold' if result['state'] == 'HOLD' else 'tracked',
            direction=list(result['display_direction']),
            reason=result['reason'], valid_through_ms=expiry,
            fresh_at_query=result['fresh_valid'] and t == self.ready_ms,
            last_fresh_ms=result['last_fresh_ms'],
            direction_age_ms=t-result['last_fresh_ms'])
