"""Replay pinned real four-channel recordings into a diagnostic cone tracker."""
import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
from tracking import Config, DiagnosticSession
from h1_reader import ReaderSession
from audio_frames import FrameSpec, adapt_h1, iter_frames, framing_summary

spec = importlib.util.spec_from_file_location('four_track_diagnostic', HERE.parent/'c-board-algorithm-01/run.py')
diagnostic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnostic)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def verify_pins(pins):
    for relative, expected in pins.items():
        path = ROOT/relative
        if not path.is_file() or sha(path) != expected:
            raise ValueError('PIN_MISMATCH: '+relative)


def replay(recording, config):
    if recording.metadata['sample_rate_hz'] != config['sample_rate_hz']:
        raise ValueError('SAMPLE_RATE_MISMATCH')
    positions = np.asarray(recording.metadata['coordinates_m'], dtype=float)
    if not np.array_equal(positions, config['positions_m']):
        raise ValueError('GEOMETRY_MISMATCH')
    if recording.metadata['channel_order'] != ['mic0', 'mic1', 'mic2', 'mic3']:
        raise ValueError('CHANNEL_ORDER_MISMATCH')
    segment = adapt_h1(recording)
    if segment.direction_policy.startswith('forbidden'):
        raise ValueError('DIRECTION_FORBIDDEN_BY_READER')
    framespec = FrameSpec(**config['frame'])
    if framespec.length != 1024 or segment.sample_rate_hz != 48000:
        raise ValueError('FROZEN_DIAGNOSTIC_REQUIRES_1024_AT_48000')
    bounds = [float(np.linalg.norm(positions[j]-positions[i])*segment.sample_rate_hz/config['sound_speed_m_s'])
              for i, j in diagnostic.PAIRS]
    session = DiagnosticSession(Config(**config['tracker']))
    frames = []
    # Use clean intervals explicitly: reset immediately even for a short interval
    # with no complete frame, rather than retaining the previous interval's lock.
    iterator = iter(iter_frames(segment, framespec))
    pending = next(iterator, None)
    for interval_index, _ in enumerate(segment.clean_intervals):
        session.begin_interval(interval_index)
        while pending is not None and pending.interval_index == interval_index:
            frame = pending
            pairs, _ = diagnostic.floating(recording.samples[frame.row_start:frame.row_stop], bounds)
            projection = diagnostic.projection(pairs, positions, segment.sample_rate_hz, config['sound_speed_m_s'])
            ready_ms = frame.end_seconds_exclusive*1000
            tracked = session.update(ready_ms, projection, interval_index=interval_index,
                                     reset_before=frame.reset_before)
            frames.append(dict(
                frame_index=frame.index, interval_index=interval_index,
                reset_before=frame.reset_before, row_start=frame.row_start, row_stop=frame.row_stop,
                first_sample_id=str(frame.first_sample_id), last_sample_id=str(frame.last_sample_id),
                frame_start_ms=frame.start_seconds*1000, frame_ready_ms=ready_ms,
                pairs=pairs, projection=projection, **tracked))
            pending = next(iterator, None)
    if not frames:
        raise ValueError('NO_COMPLETE_CLEAN_FRAME')
    states = Counter(f['tracker']['state'] for f in frames)
    angles = [f['projection']['advisory_azimuth_deg'] for f in frames if f['numeric_candidate_valid']]
    fresh = [f for f in frames if f['tracker']['fresh_valid']]
    summary = dict(
        acquisition_id=recording.metadata['acquisition_id'],
        framing=framing_summary(segment, framespec), pair_order=diagnostic.PAIRS,
        bounds_samples=bounds, states={k: states[k] for k in ('SEARCH','ACQUIRE','LOCKED','HOLD')},
        numeric_consistent_frames=len(angles), fresh_frames=len(fresh),
        first_lock_ready_ms=fresh[0]['frame_ready_ms'] if fresh else None,
        consistent_azimuth_range_deg=[min(angles), max(angles)] if angles else None,
        tracker_reasons=dict(Counter(f['tracker']['reason'] for f in frames)),
        pair_reasons=dict(Counter(p['reason'] for f in frames for p in f['pairs'])),
        diagnostic_routes=dict(Counter(f['diagnostic_route']['mode'] for f in frames)),
        target_presence='unknown', direction_accepted=False,
        accuracy_deg=None, wrong_target_rate=None, audio_benefit=None,
        count_unit='overlapping frames; not independent observations or audio-duration shares')
    return frames, summary


def execute(out):
    pins = json.loads((HERE/'pins.json').read_text(encoding='utf-8'))
    config = json.loads((HERE/'config.json').read_text(encoding='utf-8'))
    verify_pins(pins)
    sources = {p.relative_to(ROOT).as_posix(): sha(p) for p in HERE.glob('*.py')}
    sources[(HERE/'config.json').relative_to(ROOT).as_posix()] = sha(HERE/'config.json')
    sources[(HERE/'pins.json').relative_to(ROOT).as_posix()] = sha(HERE/'pins.json')
    summaries = []
    for item in config['recordings']:
        directory = ROOT/item['directory']
        for filename in ('samples.csv', 'metadata.json'):
            if (directory/filename).relative_to(ROOT).as_posix() not in pins:
                raise ValueError('UNPINNED_RECORDING')
        rec = ReaderSession().load(directory)
        frames, result = replay(rec, config)
        result.update(label=item['label'], scene_context=item['scene_context'])
        dump(out/(item['label']+'-frames.json'), frames)
        summaries.append(result)
        print(json.dumps(dict(label=item['label'], states=result['states'],
                              consistent=result['numeric_consistent_frames'],
                              first_lock_ready_ms=result['first_lock_ready_ms']), ensure_ascii=False), flush=True)
    verify_pins(pins)
    verify_pins(sources)
    head = subprocess.run(['git', '-c', 'safe.directory='+ROOT.as_posix(), 'rev-parse', 'HEAD'],
                          cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    return dict(status='AUTHOR_DIAGNOSTIC_ONLY', base_commit=config['base_commit'], checkout_head=head,
                environment=dict(python=platform.python_version(), numpy=np.__version__,
                                 platform=platform.platform(), machine=platform.machine()),
                config=config, effective_tracker=asdict(Config(**config['tracker'])),
                pins=pins, sources=sources, recordings=summaries,
                timing='sample-ID relative frame-end time; idealized zero compute delay, not measured real-time latency',
                limits=['No presence gate, precision truth, direction acceptance, automatic WAV, RTL or H3 approval.',
                        'Existing floating diagnostic only; no AMD DLL, no fixed-chain revalidation.',
                        'Quiet is an unmatched background probe; candidate consistency is not speech presence.'])


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--out', type=Path, required=True, help='new evidence directory; never overwrite')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    try:
        result = execute(args.out)
        result['elapsed_host_seconds'] = time.perf_counter()-start
        dump(args.out/'summary.json', result)
        dump(args.out/'SHA256.json', {p.name: sha(p) for p in sorted(args.out.iterdir()) if p.is_file()})
    except Exception:
        (args.out/'failure.txt').write_text(traceback.format_exc(), encoding='utf-8')
        raise


if __name__ == '__main__':
    main()
