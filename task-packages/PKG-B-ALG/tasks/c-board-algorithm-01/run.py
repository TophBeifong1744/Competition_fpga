"""C-board diagnostic increment; reuses strict reader and reference25 integer models.

No acoustic accuracy acceptance. No tracker/default changes. Outputs never overwrite.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import time
import numpy as np
import importlib.util
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

chain = module('c_board_chain', HERE.parent/'phat-fixed-03/integration/chain.py')
reader = module('c_board_reader', HERE.parents[1]/'payload/model/python/h1_reader.py')
PAIRS = [(i, j) for i in range(4) for j in range(i+1, 4)]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')

def quality(corr, bound, integer):
    p = chain.peak(corr, bound, integer)
    lim = int(np.ceil(bound))
    lags = np.arange(-lim, lim+1)
    values = np.asarray(corr)[lags % 1024].astype(float)
    peak = float(corr[p['peak'] % 1024])
    competitors = values[np.abs(lags-p['peak']) > 1]
    second = float(competitors.max()) if len(competitors) else 0.
    p.update(bound_samples=float(bound), search_limit=lim,
             edge_peak=abs(p['peak']) == lim, peak_height=peak,
             separated_peak_margin=(peak-second)/max(abs(peak), 1e-30),
             global_peak_lag=int((int(np.argmax(corr))+512) % 1024-512),
             reason='VALID' if p['valid'] else 'TAU_BOUND')
    return p

def floating(pcm, bounds):
    spectra = np.fft.rfft(pcm.T/2**23*np.hanning(1024), axis=1)
    corrs = np.zeros((6, 1024))
    rows = []
    for k, (i, j) in enumerate(PAIRS):
        z = spectra[i]*spectra[j].conj()
        amp = np.abs(z)
        mask = np.array(chain.BAND) & (amp >= .02*max(float(amp[chain.BAND].max()), 1e-15))
        row = dict(valid=False, reason='FEWER_THAN_12_BINS', bins=int(mask.sum()))
        if mask.sum() >= 12:
            corrs[k] = np.fft.irfft(np.where(mask, z/np.maximum(amp, 1e-15), 0), n=1024)
            row.update(quality(corrs[k], bounds[k], False))
        rows.append(row)
    return rows, corrs

def fixed(pcm, bounds, engine):
    win = np.array([[chain.window.window_sample(int(v), c)[0]
                     for v, c in zip(ch, chain.COEFFICIENTS)] for ch in pcm.T])
    spectra, flags = [], []
    for ch in win:
        sp, flag = engine.transform(np.column_stack((ch, np.zeros(1024, dtype=np.int64))), True)
        spectra.append(sp[:513]); flags.append(flag)
    spectra = np.asarray(spectra)
    corr = np.zeros((6, 1024, 2), dtype=np.int64)
    phat_codes = np.zeros((6, 513, 2), dtype=np.int64)
    masks = np.zeros((6, 513), dtype=bool)
    rows, iflags = [], []
    for k, (i, j) in enumerate(PAIRS):
        p = chain.phat.phat_pair(spectra[i].tolist(), spectra[j].tolist(), chain.BAND, any(flags))
        masks[k] = p['mask']
        row = dict(valid=p['valid'], reason=p['reason'], bins=sum(p['mask']))
        flag = False
        if p['valid']:
            phat_codes[k] = p['output']
            corr[k], flag = engine.transform(np.array(chain.window.conjugate_complete(p['output']), dtype=np.int64), False)
            if not flag:
                row.update(quality(corr[k, :, 0], bounds[k], True))
        rows.append(row); iflags.append(flag)
    if any(iflags):
        for row in rows:
            row.update(valid=False, reason='FRAME_IFFT_OVERFLOW')
    return rows, dict(windowed=win, fft_codes=spectra, phat_codes=phat_codes,
                     masks=masks, ifft_codes=corr), dict(fft_overflow=flags, ifft_overflow=iflags,
                     forward_calls=4, inverse_calls=sum(r['bins'] >= 12 for r in rows) if not any(flags) else 0)

def projection(rows, positions, fs, sound_speed):
    valid = [k for k, r in enumerate(rows) if r['valid']]
    result = dict(direction_accepted=False, reason='INSUFFICIENT_PAIRS', valid_pairs=len(valid))
    if len(valid) < 3:
        return result
    # X_i conj(X_j) yields arrival_i-arrival_j = (position_j-position_i).u / c.
    matrix = np.array([(positions[j]-positions[i])[:2]*fs/sound_speed for k, (i, j) in enumerate(PAIRS) if k in valid])
    delay = np.array([rows[k]['tau_samples'] for k in valid])
    u, _, rank, _ = np.linalg.lstsq(matrix, delay, rcond=None)
    if rank < 2:
        result['reason'] = 'RANK_DEFICIENT'; return result
    residual = float(np.sqrt(np.mean((matrix@u-delay)**2)))
    norm = float(np.linalg.norm(u))
    advisory = residual <= .5 and .1 <= norm <= 1.3
    result.update(projection_xy=u.tolist(), projection_norm=norm, residual_samples=residual,
                  advisory_azimuth_deg=float(np.degrees(np.arctan2(u[1], u[0]))),
                  advisory_consistent=advisory,
                  reason='UNCALIBRATED_NEARFIELD_NO_TRUTH' if advisory else 'PROJECTION_INCONSISTENT')
    return result

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--dll', required=True)
    ap.add_argument('--dependencies', required=True)
    args = ap.parse_args()
    config = json.loads((HERE/'config.json').read_text(encoding='utf-8'))
    if (config['frame'], config['band_bins'], config['relative_mask'], config['minimum_bins'], config['candidate']) != (1024, [7,85], .02, 12, 'reference25'):
        raise ValueError('UNSUPPORTED_MODEL_CONFIGURATION')
    if not 1 <= config['hop'] <= 1024 or config['sound_speed_m_s'] <= 0:
        raise ValueError('INVALID_FRAME_OR_SOUND_SPEED_CONFIGURATION')
    if args.out.resolve() == ROOT or ROOT not in HERE.parents:
        raise ValueError('invalid output')
    batch = ROOT/config['batch']
    if batch.resolve() == args.out.resolve() or batch.resolve() in args.out.resolve().parents:
        raise ValueError('output cannot be inside frozen batch')
    inputs = [batch/'GEOMETRY.md']
    for name in config['recordings']:
        inputs += [batch/'delivery-01'/name/file for file in ('samples.csv', 'metadata.json')]
    expected = json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))
    actual = {p.relative_to(ROOT).as_posix(): sha(p) for p in inputs}
    if actual != expected:
        raise ValueError('FROZEN_INPUT_HASH_MISMATCH')
    if sha(args.dll) != config['dll_sha256']:
        raise ValueError('FFT_MODEL_HASH_MISMATCH')
    args.out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    engine = chain.FFT(args.dll, args.dependencies)
    summaries = []
    try:
        for name in config['recordings']:
            recording = reader.ReaderSession().load(batch/'delivery-01'/name)
            fs = recording.metadata['sample_rate_hz']
            positions = np.asarray(recording.metadata['coordinates_m'])
            if fs != 48000 or positions.tolist() != config['positions_m']:
                raise ValueError('UNSUPPORTED_RECORDING_CONFIGURATION')
            bounds = [float(np.linalg.norm(positions[i]-positions[j])*fs/config['sound_speed_m_s']) for i,j in PAIRS]
            frames, stages = [], []
            covered = 0
            for region in recording.clean_intervals:
                count = 0
                for start in range(region['row_start'], region['row_stop']-1024+1, config['hop']):
                    pcm = recording.samples[start:start+1024]
                    fl, fc = floating(pcm, bounds)
                    fx, arrays, flags = fixed(pcm, bounds, engine)
                    arrays.update(pcm=pcm, float_corr=fc)
                    stages.append(arrays)
                    frames.append(dict(row_start=start, first_sample_id=str(int(recording.sample_ids[start])),
                        last_sample_id=str(int(recording.sample_ids[start+1023])), floating=fl, reference25=fx,
                        floating_projection=projection(fl, positions, fs, config['sound_speed_m_s']),
                        reference25_projection=projection(fx, positions, fs, config['sound_speed_m_s']), flags=flags))
                    count += 1
                if count: covered += 1024+(count-1)*config['hop']
            if not frames: raise ValueError('NO_COMPLETE_CLEAN_FRAME')
            np.savez_compressed(args.out/(name+'-stages.npz'), **{k: np.stack([s[k] for s in stages]) for k in stages[0]})
            dump(args.out/(name+'-frames.json'), frames)
            paired = [(a,b) for f in frames for a,b in zip(f['floating'],f['reference25'])]
            both = [(a,b) for a,b in paired if a['valid'] and b['valid']]
            summary = dict(recording=name, frames=len(frames), analyzed_unique_rows=covered,
                excluded_rows=len(recording.samples)-covered, pair_order=PAIRS, bounds_samples=bounds,
                floating_reasons=dict(Counter(a['reason'] for a,b in paired)),
                reference25_reasons=dict(Counter(b['reason'] for a,b in paired)),
                validity_disagreements=sum(a['valid'] != b['valid'] for a,b in paired),
                both_valid_pairs=len(both), peak_changes=sum(a['peak'] != b['peak'] for a,b in both),
                max_delay_difference_samples=max((abs(a['tau_samples']-b['tau_samples']) for a,b in both), default=None),
                floating_advisory_consistent=sum(f['floating_projection'].get('advisory_consistent',False) for f in frames),
                reference25_advisory_consistent=sum(f['reference25_projection'].get('advisory_consistent',False) for f in frames),
                fft_overflows=sum(sum(f['flags']['fft_overflow']) for f in frames),
                ifft_overflows=sum(sum(f['flags']['ifft_overflow']) for f in frames),
                forward_calls=sum(f['flags']['forward_calls'] for f in frames),
                inverse_calls=sum(f['flags']['inverse_calls'] for f in frames), direction_accepted=False)
            summaries.append(summary)
            print(json.dumps(summary, ensure_ascii=False), flush=True)
    finally:
        engine.close()
    if actual != {p.relative_to(ROOT).as_posix(): sha(p) for p in inputs}:
        raise RuntimeError('INPUT_CHANGED_DURING_RUN')
    dump(args.out/'summary.json', dict(status='AUTHOR_DIAGNOSTIC_ONLY', config=config, recordings=summaries,
        inputs=actual, environment=dict(python=platform.python_version(),numpy=np.__version__,platform=platform.platform(),
        dll_sha256=sha(args.dll)), elapsed_host_seconds=time.perf_counter()-started,
        note='Host time is not FPGA cycle evidence; reference25 retained; no full H3 or acoustic acceptance.'))

if __name__ == '__main__':
    main()
