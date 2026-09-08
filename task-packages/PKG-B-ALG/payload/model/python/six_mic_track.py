"""Allowed cone and legacy tracking over the unchanged six-mic baseline."""
from __future__ import annotations
import argparse
from collections import Counter
from dataclasses import asdict
import json
import math
from pathlib import Path
import platform
import sys
import numpy as np

import six_mic_localize as entry
import six_mic_baseline_core as baseline
from audio_frames import framing_summary
from h1_reader import unique_object, bad_constant
from sector_tracker import Config, Tracker, angle


def config_from_dict(data):
    """Strict public config boundary around the preserved experimental tracker."""
    expected = asdict(Config())
    if not isinstance(data,dict) or set(data) != set(expected):
        raise ValueError('tracking config must contain exactly the seven Config fields')
    center = data['cone_center']
    if (not isinstance(center,(list,tuple)) or len(center) != 3
            or any(type(x) not in (int,float) or not math.isfinite(x) for x in center)):
        raise ValueError('cone_center must be three finite numbers, not bool')
    for key in set(expected)-{'cone_center','acquire_frames'}:
        if type(data[key]) not in (int,float) or not math.isfinite(data[key]):
            raise ValueError(f'{key} must be a finite number, not bool')
    return Config(**(data | {'cone_center':tuple(center)}))


def load_config(path):
    if path is None:
        return config_from_dict(asdict(Config()))
    return config_from_dict(json.loads(Path(path).read_text(encoding='utf-8-sig'),
                                      object_pairs_hook=unique_object,parse_constant=bad_constant))


class TrackingSession:
    """One segment's clock; consumes baseline estimates only, never source truth."""
    def __init__(self, config=Config()):
        self.tracker = Tracker(config_from_dict(asdict(config)))

    def release(self):
        self.tracker.reset()

    def configure(self, config):
        # Validate before touching active state; valid changes always release lock.
        self.tracker.configure(config_from_dict(asdict(config)))

    def update(self, row):
        timestamp = row['end_seconds_exclusive'] * 1000
        reset = row['reset_before']
        if type(reset) is not bool or type(row['valid']) is not bool:
            raise ValueError('baseline valid/reset_before must be bool')
        # Reject a bad clock before reset so a malformed input cannot release a lock.
        last = self.tracker.last_input_ms
        if not math.isfinite(timestamp) or timestamp < 0 or (last is not None and timestamp <= last):
            raise ValueError('frame-ready timestamp must increase within one segment')
        if reset:
            self.tracker.reset()
        result = self.tracker.update(timestamp,row['unit_vector'],row['valid'])
        return result | dict(timestamp_ms=timestamp,input_reset=reset)


def run_tracking(segment, truth=None, config=Config()):
    rows, baseline_summary = entry.run_segment(segment,truth)
    reference = entry.truth_vector(truth.tolist() if isinstance(truth,np.ndarray) else truth)
    session = TrackingSession(config)
    output, metric_rows = [], []
    for row in rows:
        tracked = session.update(row)
        error = (angle(reference,np.asarray(tracked['direction']))
                 if reference is not None and tracked['fresh_valid'] else None)
        tracked['angular_error_deg'] = error
        output.append(dict(baseline=row,tracking=tracked))
        metric_rows.append(dict(valid=tracked['fresh_valid'],angular_error_deg=error,rejection_reasons=[]))
    summary = entry.summarize_results(metric_rows,truth_available=reference is not None)
    locks = [r['tracking']['timestamp_ms'] for r in output if r['tracking']['reason']=='acquired']
    summary.update(valid_means='fresh_valid only; HOLD never counts',
        state_counts=dict(sorted(Counter(r['tracking']['state'] for r in output).items())),
        hold_frames=sum(r['tracking']['stale'] for r in output),
        acquisitions=len(locks),first_lock_ready_ms=locks[0] if locks else None,
        acquisition_ready_times_ms=locks,
        reason_counts=dict(sorted(Counter(r['tracking']['reason'] for r in output).items())))
    return output,dict(baseline=baseline_summary,tracking=summary)


def write_demo(directory, scenario):
    """Long continuous synthetic teaching signal; never concatenate old trials."""
    if scenario not in ['stable','drop-return','outside','band_noise0','interferer0']:
        raise ValueError('unsupported tracking demo')
    rng = np.random.default_rng(20260908)
    length = 49152
    def source():
        frequencies = np.fft.rfftfreq(length,1/48000)
        weight = np.clip((frequencies-200)/200,0,1)*np.clip((4400-frequencies)/600,0,1)
        signal = np.fft.irfft(np.fft.rfft(rng.normal(size=length))*weight,n=length)
        return signal/np.std(signal)
    direction = baseline.unit(90 if scenario=='outside' else 0,0)
    data = baseline.render(source(),direction)
    truth = direction
    if scenario == 'drop-return':
        # Controlled simultaneous channel mute; this is not a measured room decay.
        data[:,16000:30000] = 0
        truth = None  # no static truth assertion over an interval with no active source
    elif scenario == 'band_noise0':
        data += np.array([source() for _ in range(6)])
    elif scenario == 'interferer0':
        data += baseline.render(source(),baseline.unit(90,0))
    start,stop = 1536,length-1536
    directory = Path(directory); directory.mkdir()
    np.save(directory/'samples.npy',data[:,start:stop],allow_pickle=False)
    entry.write_json(directory/'metadata.json',dict(
        schema_version=entry.SCHEMA,source_kind='synthetic-acoustic',evidence_level='synthetic',
        channel_order=[f'mic{i}' for i in range(6)],sample_rate_hz=48000,
        coordinates_m=baseline.POS.tolist(),coordinate_system='x-forward_y-left_z-up',
        direction_convention='array-to-source',angle_unit='deg',source_id=f'tracking-teaching:{scenario}:seed=20260908',
        source_sha256=entry.sha256(__file__),first_sample_id=start,
        crop=dict(start=start,stop=stop,reason='Interior continuous render; no old-trial concatenation'),
        truth_unit_vector=truth.tolist() if truth is not None else None,
        generator=dict(scenario=scenario,seed=20260908,length=length,
                       source_mute_rows=[16000,30000] if scenario=='drop-return' else None,
                       note='Teaching synthetic example; not a replacement for SIM6-002 performance evidence')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--input',type=Path)
    source.add_argument('--demo',choices=['stable','drop-return','outside','band_noise0','interferer0'])
    parser.add_argument('--config',type=Path)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        if args.out.exists(): raise ValueError('output path must be new')
        if args.input is not None:
            segment,truth = entry.load_input(args.input)
            rows,summary = run_tracking(segment,truth,config)
            args.out.mkdir(parents=True)
        else:
            args.out.mkdir(parents=True)
            write_demo(args.out/'input',args.demo)
            segment,truth = entry.load_input(args.out/'input')
            rows,summary = run_tracking(segment,truth,config)
        entry.write_json(args.out/'frames.json',rows)
        entry.write_json(args.out/'summary.json',summary)
        entry.write_json(args.out/'tracking-config.json',asdict(config))
        directory = Path(__file__).resolve().parent
        entry.write_json(args.out/'run.json',dict(status='COMPLETE_SYNTHETIC_ONLY',
            config=asdict(config),normalized_cone_center=Tracker(config).center.tolist(),
            config_file_sha256=entry.sha256(args.config) if args.config else None,
            source_sha256={name:entry.sha256(directory/name) for name in
                ['six_mic_track.py','sector_tracker.py','six_mic_localize.py',
                 'six_mic_baseline_core.py','audio_frames.py','h1_reader.py']},
            python=platform.python_version(),numpy=np.__version__,framing=framing_summary(segment),
            timestamp_convention='frame end exclusive, milliseconds relative to segment first sample',
            limitations=['No speaker identity; same-cone competitor can be tracked.',
                         'Five reliable consecutive frames may prevent acquisition in noise.',
                         'HOLD display only; consumer must expire display when no further frames arrive.',
                         'Synthetic offline only; no H2/H3 approval or audio enhancement.']))
    except (ValueError,TypeError,OSError,OverflowError,EOFError) as error:
        print(json.dumps(dict(status='ERROR',message=str(error)),ensure_ascii=False),file=sys.stderr)
        return 2
    print(json.dumps(dict(status='COMPLETE_SYNTHETIC_ONLY',output=str(args.out),**summary),allow_nan=False))
    return 0


if __name__=='__main__': sys.exit(main())
