"""Format adapters and gap-safe framing; no acoustic estimation or filtering."""
from __future__ import annotations

from dataclasses import dataclass
import copy
import hashlib
import math
import re

import numpy as np

from h1_reader import Recording

BASELINE_POSITIONS = np.array([
    [-.020, -.020, 0], [.020, -.020, 0], [.020, .020, 0],
    [-.020, .020, 0], [0, 0, np.sqrt(2) * .020], [0, 0, -np.sqrt(2) * .020]])


def _readonly(value, dtype):
    result = np.array(value, dtype=dtype, copy=True)
    result.setflags(write=False)
    return result


@dataclass(frozen=True)
class FrameSpec:
    length: int = 1024
    hop: int = 512

    def __post_init__(self):
        if type(self.length) is not int or type(self.hop) is not int:
            raise ValueError('frame length and hop must be integers, not bool')
        if not 1 <= self.hop <= self.length:
            raise ValueError('require 1 <= hop <= length; sparse sampling is unsupported')


@dataclass(frozen=True)
class InputSegment:
    """Construct with adapt_h1/adapt_six_mic_baseline; arrays own copied storage."""
    profile: str
    samples: np.ndarray  # time x channels, float64
    sample_ids: np.ndarray  # original uint64; never converted through float
    clean_intervals: tuple  # (row_start, exclusive row_stop)
    sample_rate_hz: float
    metadata: dict
    provenance: dict
    direction_policy: str


def adapt_h1(recording: Recording) -> InputSegment:
    """Adapt ReaderSession output; fixed shared PCM scale preserves channel ratios."""
    return InputSegment(
        profile='h1-four-channel-0.3',
        samples=_readonly(recording.samples.astype(np.float64) / 2**23, np.float64),
        sample_ids=_readonly(recording.sample_ids, np.uint64),
        clean_intervals=tuple((r['row_start'], r['row_stop']) for r in recording.clean_intervals),
        sample_rate_hz=float(recording.metadata['sample_rate_hz']),
        metadata=copy.deepcopy(recording.metadata),
        provenance=dict(file_sha256=copy.deepcopy(recording.file_hashes),
                        conversion='float64(pcm) / 8388608; common fixed gain',
                        error_rows=int(recording.stream_error.sum()),
                        missing_samples=sum(r['count'] for r in recording.missing_intervals)),
        direction_policy=recording.direction_policy())


def adapt_six_mic_baseline(samples, *, sample_rate_hz, positions_m,
                           source_id, source_sha256, first_sample_id=0) -> InputSegment:
    """Independent in-memory synthetic input, channel x time, for the fixed old baseline.

    The caller supplies an already continuous, usable crop. Periodic render margins
    must be excluded by the caller. No H1 schema or hardware acceptance is implied.
    source_sha256 identifies the generating source; normalized data is hashed here.
    """
    if type(sample_rate_hz) not in (int, float) or not math.isfinite(sample_rate_hz) or sample_rate_hz != 48000:
        raise ValueError('six-mic baseline requires sample_rate_hz=48000')
    x = np.asarray(samples)
    if x.ndim != 2 or x.shape[0] != 6 or x.shape[1] == 0 or x.dtype.kind != 'f':
        raise ValueError('expected nonempty floating array shaped (6, time); no automatic axis inference')
    if not np.isfinite(x).all():
        raise ValueError('samples must be finite')
    positions = np.asarray(positions_m)
    if (positions.shape != (6, 3) or positions.dtype.kind not in 'fiu'
            or not np.isfinite(positions).all()
            or not np.allclose(positions, BASELINE_POSITIONS, rtol=0, atol=1e-12)):
        raise ValueError('coordinates/order must match the fixed six-mic baseline')
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError('source_id must identify the synthetic run/crop')
    if not isinstance(source_sha256, str) or not re.fullmatch('[0-9a-f]{64}', source_sha256):
        raise ValueError('source_sha256 must be a lowercase SHA-256 of the generating source')
    count = x.shape[1]
    if type(first_sample_id) is not int or not 0 <= first_sample_id <= 2**64 - count:
        raise ValueError('sample ID range must fit uint64 without wrap')
    values = _readonly(x.T, np.float64)
    if not np.isfinite(values).all():
        raise ValueError('samples must remain finite after float64 conversion')
    ids = np.arange(count, dtype=np.uint64) + np.uint64(first_sample_id)
    return InputSegment(
        'six-mic-baseline-synthetic-v1', values, _readonly(ids, np.uint64),
        ((0, count),), 48000.,
        dict(source_id=source_id, channel_order=[f'mic{i}' for i in range(6)],
             coordinates_m=positions.tolist(), coordinate_system='x-forward_y-left_z-up',
             direction_convention='array-to-source', angle_unit='deg',
             source_kind='synthetic-acoustic', evidence_level='synthetic'),
        dict(source_id=source_id, source_sha256=source_sha256,
             samples_sha256=hashlib.sha256(values.astype('<f8').tobytes(order='C')).hexdigest(),
             conversion='channel x time to time x channel; float64; no gain change',
             error_rows=0, missing_samples=0),
        'synthetic_only_requires_algorithm_validation')


@dataclass(frozen=True)
class AudioFrame:
    profile: str
    index: int
    interval_index: int
    reset_before: bool  # downstream state resets before first frame of every interval
    row_start: int
    row_stop: int
    first_sample_id: int
    last_sample_id: int
    start_seconds: float  # relative to first recorded ID, NOT wall clock
    end_seconds_exclusive: float
    samples: np.ndarray  # channels x length; read-only independent copy
    sample_rate_hz: float
    direction_policy: str

    def summary(self):
        return {key: value for key, value in vars(self).items() if key != 'samples'} | {
            'shape': list(self.samples.shape), 'dtype': str(self.samples.dtype)}


def iter_frames(segment: InputSegment, spec: FrameSpec = FrameSpec()):
    """Each call frames one segment independently. No stitching, padding or window."""
    origin = int(segment.sample_ids[0])
    index = 0
    for interval_index, (start, stop) in enumerate(segment.clean_intervals):
        for row in range(start, stop - spec.length + 1, spec.hop):
            first = int(segment.sample_ids[row])
            last = int(segment.sample_ids[row + spec.length - 1])
            yield AudioFrame(
                segment.profile, index, interval_index, row == start,
                row, row + spec.length, first, last,
                (first - origin) / segment.sample_rate_hz,
                (last - origin + 1) / segment.sample_rate_hz,
                _readonly(segment.samples[row:row + spec.length].T, np.float64),
                segment.sample_rate_hz, segment.direction_policy)
            index += 1


def framing_summary(segment: InputSegment, spec: FrameSpec = FrameSpec()):
    intervals = []
    for start, stop in segment.clean_intervals:
        count = max(0, 1 + (stop - start - spec.length) // spec.hop)
        covered = (count - 1) * spec.hop + spec.length if count else 0
        intervals.append(dict(row_start=start, row_stop=stop, frames=count,
                              covered_unique_rows=covered, unused_tail_rows=stop-start-covered))
    return dict(profile=segment.profile, sample_rate_hz=segment.sample_rate_hz,
                frame_length=spec.length, hop=spec.hop,
                frame_duration_seconds=spec.length/segment.sample_rate_hz,
                hop_seconds=spec.hop/segment.sample_rate_hz,
                frames=sum(r['frames'] for r in intervals), input_rows=len(segment.samples),
                error_rows=segment.provenance['error_rows'],
                missing_samples=segment.provenance['missing_samples'],
                unused_clean_rows=sum(r['unused_tail_rows'] for r in intervals),
                intervals=intervals, direction_policy=segment.direction_policy,
                provenance=copy.deepcopy(segment.provenance))


def to_six_mic_baseline(frame: AudioFrame):
    """Guard the old gcc() input, which hardcodes six channels, N=1024, Fs=48000."""
    if (frame.profile != 'six-mic-baseline-synthetic-v1'
            or frame.samples.shape != (6, 1024) or frame.sample_rate_hz != 48000):
        raise ValueError('old six-mic GCC requires its independent synthetic profile, 6x1024 at 48000 Hz')
    return np.array(frame.samples, copy=True)
