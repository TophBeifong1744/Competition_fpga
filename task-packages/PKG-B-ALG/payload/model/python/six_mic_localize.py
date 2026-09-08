"""Six-mic offline baseline entry. Synthetic evidence only; no tracking or beamforming."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import platform
import sys

import numpy as np

import six_mic_baseline_core as baseline
from audio_frames import (FrameSpec, adapt_six_mic_baseline, iter_frames,
                          framing_summary, to_six_mic_baseline)
from h1_reader import unique_object, bad_constant

SCHEMA = 'ss-six-synthetic-offline-0.1'
BASELINE_SOURCE_SHA256 = 'b50cdf8eafad2b14998156e705e30f1a353ee6c4b8b3f87ce461fe8e4f086a8b'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def truth_vector(value):
    if value is None:
        return None
    if (not isinstance(value, list) or len(value) != 3
            or any(type(v) not in (int, float) for v in value)):
        raise ValueError('truth_unit_vector must be null or three real numbers, not bool')
    result = np.asarray(value, dtype=np.float64)
    if not np.isfinite(result).all() or not np.isclose(np.linalg.norm(result), 1., rtol=0, atol=1e-10):
        raise ValueError('truth_unit_vector must be finite and unit length')
    return result / np.linalg.norm(result)


def load_input(directory):
    """Separate six-mic synthetic files; H1 input is never auto-converted."""
    directory = Path(directory)
    meta = json.loads((directory/'metadata.json').read_text(encoding='utf-8-sig'),
                      object_pairs_hook=unique_object, parse_constant=bad_constant)
    required = {'schema_version', 'source_kind', 'evidence_level', 'channel_order',
                'sample_rate_hz', 'coordinates_m', 'coordinate_system',
                'direction_convention', 'angle_unit', 'source_id',
                'source_sha256', 'first_sample_id', 'crop'}
    if not isinstance(meta, dict) or not required <= meta.keys():
        raise ValueError('missing required six-mic metadata fields')
    expected = dict(schema_version=SCHEMA, source_kind='synthetic-acoustic', evidence_level='synthetic',
                    channel_order=[f'mic{i}' for i in range(6)],
                    coordinate_system='x-forward_y-left_z-up',
                    direction_convention='array-to-source', angle_unit='deg')
    for key, value in expected.items():
        if meta[key] != value:
            raise ValueError(f'unsupported {key}: six-mic synthetic profile required')
    crop = meta['crop']
    if not isinstance(crop, dict) or set(crop) != {'start', 'stop', 'reason'}:
        raise ValueError('crop must contain start, stop and reason')
    if (type(crop['start']) is not int or type(crop['stop']) is not int
            or not 0 <= crop['start'] < crop['stop']
            or not isinstance(crop['reason'], str) or not crop['reason'].strip()):
        raise ValueError('crop requires a nonempty interval and explanation')
    truth = truth_vector(meta.get('truth_unit_vector'))
    # allow_pickle=False: this interface loads numeric arrays only, never objects.
    samples = np.load(directory/'samples.npy', allow_pickle=False)
    if not isinstance(samples, np.ndarray):
        samples.close()
        raise ValueError('samples.npy must be one NPY array, not an archive')
    if samples.ndim != 2 or samples.shape[1] != crop['stop'] - crop['start']:
        raise ValueError('stored sample count must match the declared crop')
    if meta['first_sample_id'] != crop['start']:
        raise ValueError('first_sample_id must equal crop start in the synthetic source')
    segment = adapt_six_mic_baseline(samples, sample_rate_hz=meta['sample_rate_hz'],
        positions_m=meta['coordinates_m'], source_id=meta['source_id'],
        source_sha256=meta['source_sha256'], first_sample_id=meta['first_sample_id'])
    segment.provenance.update(input_file_sha256={name: sha256(directory/name)
                             for name in ['metadata.json', 'samples.npy']}, crop=crop)
    return segment, truth


def solve_delays(tau):
    """Wrap the unchanged LS solver, exposing its existing rejection checks."""
    tau = np.asarray(tau, dtype=np.float64)
    if tau.shape != (15,) or np.isinf(tau).any():
        raise ValueError('expected 15 delays in samples; missing pairs use NaN, not infinity')
    good = np.isfinite(tau)
    count = int(good.sum())
    rank = int(np.linalg.matrix_rank(baseline.B[good])) if count else 0
    direction, valid, residual, norm = baseline.solve(tau)
    reasons = []
    if count < 5:
        reasons.append('insufficient_pairs')
    if rank < 3:
        reasons.append('rank_deficient')
    if count >= 5 and rank == 3:
        if not .7 <= norm <= 1.3:
            reasons.append('norm_out_of_range')
        if not residual <= .5:
            reasons.append('residual_too_large')
    if valid:
        vector = direction.tolist()
        # Azimuth has no physical definition at exactly vertical directions.
        azimuth = (float(np.rad2deg(np.arctan2(direction[1], direction[0])))
                   if np.hypot(direction[0], direction[1]) > 1e-12 else None)
        elevation = float(np.rad2deg(np.arctan2(direction[2], np.hypot(direction[0], direction[1]))))
    else:
        vector, azimuth, elevation = None, None, None
    return dict(valid=bool(valid), rejection_reasons=reasons, unit_vector=vector,
                azimuth_deg=azimuth, elevation_deg=elevation,
                finite_pairs=count, geometry_rank=rank,
                residual_samples=float(residual) if np.isfinite(residual) else None,
                raw_vector_norm=float(norm) if np.isfinite(norm) else None,
                pair_delays_samples=[float(t) if np.isfinite(t) else None for t in tau])


def localize_frame(frame, truth=None):
    samples = to_six_mic_baseline(frame)
    if not np.isfinite(samples).all():
        raise ValueError('frame contains nonfinite samples')
    reference = truth_vector(truth.tolist() if isinstance(truth, np.ndarray) else truth)
    try:
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            result = solve_delays(baseline.gcc(samples))
    except (FloatingPointError, np.linalg.LinAlgError) as error:
        raise ValueError(f'numeric failure in baseline: {error}') from error
    result = frame.summary() | result
    result['angular_error_deg'] = (baseline.angle(reference, np.array(result['unit_vector']))
                                    if reference is not None and result['valid'] else None)
    return result


def summarize_results(rows, *, truth_available):
    total = len(rows)
    valid = sum(row['valid'] for row in rows)
    errors = [row['angular_error_deg'] for row in rows if row['valid'] and row['angular_error_deg'] is not None]
    wrong = sum(e > 30 for e in errors) if truth_available else None
    reasons = Counter(reason for row in rows for reason in row['rejection_reasons'])
    return dict(total_frames=total, valid_frames=valid, rejected_frames=total-valid,
                valid_rate=valid/total if total else None,
                truth_available=truth_available, evaluated_valid_frames=len(errors),
                p50_error_deg=float(np.percentile(errors,50)) if errors else None,
                p95_error_deg=float(np.percentile(errors,95)) if errors else None,
                accepted_wrong_over_30deg=wrong,
                wrong_rate_all_frames=wrong/total if truth_available and total else None,
                wrong_rate_valid_frames=wrong/valid if truth_available and valid else None,
                rejection_reason_counts=dict(sorted(reasons.items())),
                reason_counts_are_nonexclusive=True)


def run_segment(segment, truth=None):
    # Check even a too-short segment so the wrong profile cannot silently produce zero frames.
    if (segment.profile != 'six-mic-baseline-synthetic-v1' or segment.sample_rate_hz != 48000
            or segment.samples.shape[1] != 6):
        raise ValueError('six-mic baseline input profile required')
    truth = truth_vector(truth.tolist() if isinstance(truth, np.ndarray) else truth)
    rows = [localize_frame(frame, truth) for frame in iter_frames(segment, FrameSpec())]
    return rows, summarize_results(rows, truth_available=truth is not None)


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def write_demo(directory, scenario, azimuth, elevation, repeat):
    """Use the old generator, retain only interior samples [1536,3072)."""
    if scenario not in ['clean','band_noise0','interferer0','silence']:
        raise ValueError('unsupported demo scenario')
    if (not math.isfinite(azimuth) or not 0 <= azimuth < 360
            or not math.isfinite(elevation) or not -90 <= elevation <= 90
            or type(repeat) is not int or not 0 <= repeat <= 1000000):
        raise ValueError('require 0<=az<360, -90<=el<=90, 0<=repeat<=1000000')
    if scenario == 'silence':
        full, truth = np.zeros((6,baseline.L)), None
    else:
        truth, target, other = baseline.make_trial(azimuth, elevation, repeat, scenario)
        full = target + other
    directory = Path(directory)
    directory.mkdir()
    start, stop = baseline.START, baseline.START + baseline.N + 512
    np.save(directory/'samples.npy',full[:,start:stop],allow_pickle=False)
    write_json(directory/'metadata.json', dict(
        schema_version=SCHEMA, source_kind='synthetic-acoustic', evidence_level='synthetic',
        channel_order=[f'mic{i}' for i in range(6)], sample_rate_hz=baseline.FS,
        coordinates_m=baseline.POS.tolist(), coordinate_system='x-forward_y-left_z-up',
        direction_convention='array-to-source', angle_unit='deg',
        source_id=f'old-baseline:{scenario}:az={azimuth}:el={elevation}:repeat={repeat}:crop={start}:{stop}',
        source_sha256=sha256(baseline.__file__), first_sample_id=start,
        crop=dict(start=start,stop=stop,reason='Interior of original 4096-sample periodic render; no concatenation'),
        truth_unit_vector=truth.tolist() if truth is not None else None,
        generator=dict(scenario=scenario,azimuth_deg=azimuth,elevation_deg=elevation,
                       repeat=repeat,base_seed=baseline.SEED,baseline_source_sha256=BASELINE_SOURCE_SHA256)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--input',type=Path)
    source.add_argument('--demo',choices=['clean','band_noise0','interferer0','silence'])
    parser.add_argument('--az',type=float,default=35.)
    parser.add_argument('--el',type=float,default=25.)
    parser.add_argument('--repeat',type=int,default=0)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    try:
        if args.out.exists():
            raise ValueError('output path must be new; existing paths are never overwritten')
        if args.input is not None:
            segment, truth = load_input(args.input)
            rows, summary = run_segment(segment, truth)
            args.out.mkdir(parents=True)
        else:
            args.out.mkdir(parents=True)
            write_demo(args.out/'input',args.demo,args.az,args.el,args.repeat)
            segment, truth = load_input(args.out/'input')
            rows, summary = run_segment(segment, truth)
        write_json(args.out/'frames.json',rows)
        write_json(args.out/'summary.json',summary)
        directory = Path(__file__).resolve().parent
        write_json(args.out/'run.json',dict(
            status='COMPLETE_SYNTHETIC_ONLY', algorithm='six-mic-original-gcc-ls',
            baseline_source_sha256=BASELINE_SOURCE_SHA256,
            source_sha256={name:sha256(directory/name) for name in
                ['six_mic_baseline_core.py','six_mic_localize.py','audio_frames.py','h1_reader.py']},
            python=platform.python_version(),numpy=np.__version__,
            framing=framing_summary(segment), truth_unit_vector=truth.tolist() if truth is not None else None,
            pair_order=baseline.PAIRS, band_hz=baseline.BAND, speed_of_sound_m_s=baseline.C,
            thresholds=dict(minimum_pairs=5,minimum_rank=3,norm_range=[.7,1.3],maximum_residual_samples=.5),
            limitations=['Synthetic offline only; not H2/H3 approval.',
                         'No sector lock, tracking, beamforming or distance estimate.',
                         'Valid means baseline checks passed, not necessarily the intended source.',
                         'Overlapping frames are not independent trials; demo is not a performance benchmark.']))
    except (ValueError, OSError, OverflowError, EOFError) as error:
        print(json.dumps(dict(status='ERROR',message=str(error)),ensure_ascii=False),file=sys.stderr)
        return 2
    print(json.dumps(dict(status='COMPLETE_SYNTHETIC_ONLY',output=str(args.out),**summary),ensure_ascii=False,allow_nan=False))
    return 0


if __name__ == '__main__': sys.exit(main())
