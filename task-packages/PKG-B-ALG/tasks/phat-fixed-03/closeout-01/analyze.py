"""Read-only archive analysis. No vendor model, new scenes or acceptance gates."""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
ARCHIVE = HERE.parent / 'dynamic-range/evidence/run01'
sys.path.insert(0, str(HERE.parent / 'integration'))
import chain

LINES = [0.001, 0.01, 0.1, 0.5, 1.0]  # Post-hoc research references, NOT acceptance.

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')

def csvwrite(path, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

def stats(values):
    x = np.abs(np.array(values, dtype=float))
    return dict(n=len(x), median=float(np.median(x)) if len(x) else None,
                p95=float(np.quantile(x, .95)) if len(x) else None,
                p99=float(np.quantile(x, .99)) if len(x) else None,
                maximum=float(x.max()) if len(x) else None,
                **{f'gt_{t}': int(np.count_nonzero(x > t)) for t in LINES})

def window_float_pairs(win):
    # Float PHAT/IFFT after archived integer window: isolate pre-FFT losses.
    spectra = np.fft.rfft(win / 2**23, axis=1)
    result = []
    for i, j in chain.baseline.PAIRS:
        z = spectra[i] * spectra[j].conj(); amp = abs(z)
        mask = np.array(chain.BAND) & (amp >= .02 * max(float(amp[chain.BAND].max()), 1e-15))
        p = dict(mask=mask.tolist(), valid=False)
        if mask.sum() >= 12:
            corr = np.fft.irfft(np.where(mask, z/np.maximum(amp, 1e-15), 0), n=1024)
            bound = np.linalg.norm(chain.baseline.POS[i]-chain.baseline.POS[j])/chain.baseline.C*chain.baseline.FS
            p.update(chain.peak(corr, bound, False))
        result.append(p)
    return result

def compare(a, b):
    both = a['valid'] and b['valid']
    return dict(valid_changed=a['valid'] != b['valid'],
                newly_valid=not a['valid'] and b['valid'], lost_valid=a['valid'] and not b['valid'],
                mask_changed=sum(x != y for x, y in zip(a['mask'], b['mask'], strict=True)),
                peak_changed=(a['peak'] != b['peak']) if both else None,
                delta=b['tau_samples']-a['tau_samples'] if both else None)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args(); args.out.mkdir(parents=True, exist_ok=False)
    packing = json.loads((ARCHIVE/'packing.json').read_text())
    compressed = (ARCHIVE/'frames.json.gz').read_bytes(); raw = gzip.decompress(compressed)
    assert len(compressed) == packing['compressed_bytes'] and len(raw) == packing['original_bytes']
    assert hashlib.sha256(compressed).hexdigest() == packing['compressed_sha256']
    assert hashlib.sha256(raw).hexdigest() == packing['original_sha256']
    frames = json.loads(raw); del raw
    old = json.loads((ARCHIVE/'summary.json').read_text())
    sources = {}
    for name, expected in old['sources'].items():
        relative = 'task-packages/' + name.replace('\\', '/').split('/task-packages/', 1)[1]
        assert sha(ROOT/relative) == expected, relative
        sources[relative] = expected
    protocol = json.loads((HERE.parent/'dynamic-range/protocol.json').read_text())
    rows, stages, numerical, identities = [], [], [], []
    for r in frames:
        path = ARCHIVE/r['npz']; assert sha(path) == r['npz_sha256'], path
        meta = {k: r[k] for k in ['case', 'seed', 'az', 'el', 'scenario', 'peak_exponent']}
        with np.load(path, allow_pickle=False) as z:
            inp, pcm, win = [z[k] for k in ['input_float', 'pcm', 'windowed']]
            np.testing.assert_array_equal(pcm, np.clip(np.rint(inp*2**23), -2**23, 2**23-1))
            np.testing.assert_array_equal(win, np.rint(pcm*np.array(chain.COEFFICIENTS)/2**17))
            wp = window_float_pairs(win)
            assert [p['mask'] for p in wp] == r['integer_window_float_masks']
            stage_paths = [('pcm_vs_float', r['float_pairs'], r['pcm_float_pairs']),
                           ('window_vs_pcm', r['pcm_float_pairs'], wp),
                           ('window_vs_float', r['float_pairs'], wp)]
            for label, refs, acts in stage_paths:
                for pair, (a, b) in enumerate(zip(refs, acts, strict=True)):
                    stages.append(dict(**meta, stage=label, pair=pair, ref_valid=a['valid'], actual_valid=b['valid'], **compare(a,b)))
            ideals = np.fft.fft(win, axis=1)
            for candidate, config in protocol['candidates'].items():
                c = r['candidates'][candidate]
                rawfft, packed = z[candidate+'_raw_fft'], z[candidate+'_packed_fft']
                shift = c['common_right_shift']
                np.testing.assert_array_equal(packed, np.rint(rawfft/2**shift))
                scale = 2.**(config['width']-25-sum(config['shifts']))
                expected = np.stack((ideals.real, ideals.imag), axis=-1)*scale
                err = rawfft - expected
                fft_bad = any(c['flags']['fft_overflow'])
                numerical.append(dict(**meta, candidate=candidate, common_right_shift=shift,
                    fft_overflow=fft_bad, pcm_peak=int(abs(pcm).max()), window_peak=int(abs(win).max()),
                    pcm_zero_fraction=float(np.mean(pcm==0)), window_zero_fraction=float(np.mean(win==0)),
                    pcm_max_error_codes=float(abs(pcm-inp*2**23).max()),
                    window_max_error_codes=float(abs(win-pcm*np.hanning(1024)).max()),
                    fft_band_nonzero_components=int(np.count_nonzero(rawfft[:,7:86])),
                    fft_max_component_error_raw_codes=float(abs(err).max()) if not fft_bad else None,
                    fft_rms_component_error_raw_codes=float(np.sqrt(np.mean(err**2))) if not fft_bad else None,
                    fft_max_error_unscaled_window_codes=float(abs(err).max()/scale) if not fft_bad else None,
                    packing_max_error_raw_codes=float(abs(packed*2**shift-rawfft).max())))
                for pair, (a, b) in enumerate(zip(r['float_pairs'], c['pairs'], strict=True)):
                    d = compare(a,b); assert d == c['vs_float'][pair]
                    assert compare(r['pcm_float_pairs'][pair],b) == c['vs_pcm'][pair]
                    rows.append(dict(**meta, candidate=candidate, pair=pair, float_valid=a['valid'],
                        fixed_valid=b['valid'], fft_overflow=fft_bad, ifft_overflow=any(c['flags']['ifft_overflow']), **d))
                    stages.append(dict(**meta, stage=candidate+'_vs_window', pair=pair,
                        ref_valid=wp[pair]['valid'], actual_valid=b['valid'], **compare(wp[pair],b)))
            identities.append(dict(case=r['case'], file=r['npz'], sha256=r['npz_sha256'], arrays=len(z.files)))
    groups = []
    # Keep stress separate; joint strata preserve seed/scenario/direction correlations.
    for dims in [('candidate','peak_exponent'), ('candidate','peak_exponent','scenario'),
                 ('candidate','peak_exponent','seed'), ('candidate','peak_exponent','seed','scenario','az','el')]:
        buckets = {}
        for r in rows:
            if r['peak_exponent'] is not None:
                key = tuple(r[d] for d in dims); buckets.setdefault(key, []).append(r)
        for key, rr in buckets.items():
            groups.append(dict(stratum='/'.join(dims), **dict(zip(dims,key)), frames=len({r['case'] for r in rr}),
                pairs=len(rr), float_valid=sum(r['float_valid'] for r in rr), fixed_valid=sum(r['fixed_valid'] for r in rr),
                lost_valid=sum(r['lost_valid'] for r in rr), newly_valid=sum(r['newly_valid'] for r in rr),
                peak_changed=sum(r['peak_changed'] is True for r in rr), mask_changed=sum(r['mask_changed'] for r in rr),
                **stats([r['delta'] for r in rr if r['delta'] is not None])))
    amps = [g for g in groups if g['stratum']=='candidate/peak_exponent']
    # Independent aggregation must recover every archived amplitude group.
    for g in amps:
        original = next(x for x in old['groups'] if x['candidate']==g['candidate'] and x['peak_exponent']==g['peak_exponent'])
        for k in ['frames','pairs','float_valid','fixed_valid','lost_valid','newly_valid','mask_changed','peak_changed']:
            assert g[k] == original[k], (k,g)
        assert g['maximum'] == original['max_tau_delta']
    reference_ranges = []
    for candidate in protocol['candidates']:
        aa = sorted([g for g in amps if g['candidate']==candidate], key=lambda g:g['peak_exponent'])
        for line in LINES:
            last = 0
            for g in aa:
                if g['fixed_valid'] != g['pairs'] or g['n'] != g['pairs'] or g['maximum'] > line: break
                last = g['peak_exponent']
            reference_ranges.append(dict(candidate=candidate, research_line_samples=line,
                contiguous_tested_prefix_from_2_minus_1_to_exponent=last or None))
    stage_groups = []
    for label in sorted({r['stage'] for r in stages}):
        for exponent in range(1,25):
            rr = [r for r in stages if r['stage']==label and r['peak_exponent']==exponent]
            stage_groups.append(dict(stage=label, peak_exponent=exponent, pairs=len(rr),
                ref_valid=sum(r['ref_valid'] for r in rr), actual_valid=sum(r['actual_valid'] for r in rr),
                validity_changes=sum(r['valid_changed'] for r in rr), peak_changed=sum(r['peak_changed'] is True for r in rr),
                mask_changed=sum(r['mask_changed'] for r in rr), **stats([r['delta'] for r in rr if r['delta'] is not None])))
    csvwrite(args.out/'pairs.csv', rows); csvwrite(args.out/'stage-pairs.csv', stages)
    csvwrite(args.out/'numerical-loss.csv', numerical); csvwrite(args.out/'amplitude.csv', amps)
    csvwrite(args.out/'stage-amplitude.csv', stage_groups)
    write(args.out/'strata.json', groups); write(args.out/'research-lines.json', reference_ranges)
    worst = sorted([r for r in rows if r['delta'] is not None and r['peak_exponent'] is not None], key=lambda r:abs(r['delta']), reverse=True)[:30]
    write(args.out/'tail-cases.json', worst)
    write(args.out/'verification.json', dict(status='AUTHOR_ARCHIVE_ANALYSIS_NOT_ACCEPTANCE',
        input_commit='bff45e7bbedab321fc4815e1432f1575c750edc4', frames=len(frames), candidate_pairs=len(rows),
        verified_npz=identities, sources=sources, analysis_sha256=sha(Path(__file__)),
        frames_compressed_sha256=packing['compressed_sha256'], frames_decompressed_sha256=packing['original_sha256'],
        archived_amplitude_groups_recovered=len(amps), integer_PCM_window_and_packing_arrays_checked=True,
        quantile_method='numpy linear; absolute delta; jointly valid pairs only; no IID confidence intervals',
        research_lines=LINES, python=sys.version, numpy=np.__version__,
        output_hashes={p.name:sha(p) for p in sorted(args.out.iterdir()) if p.is_file()}))
    print(f'Verified {len(frames)} NPZ / {len(rows)} candidate pairs / {len(amps)} archived amplitude groups')

if __name__ == '__main__': main()
