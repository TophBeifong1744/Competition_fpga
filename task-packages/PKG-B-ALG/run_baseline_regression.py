"""Record same-frame equivalence and independent axis golden for the six-mic entry."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'payload/model/python'))
sys.path.insert(0,str(ROOT/'payload/tb/python'))
from test_six_mic_localize import original_namespace, SNAPSHOT
from audio_frames import adapt_six_mic_baseline, iter_frames
import six_mic_localize as entry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True,type=Path)
    args = parser.parse_args()
    if args.out.exists(): parser.error('output path must be new')
    if entry.sha256(SNAPSHOT) != entry.BASELINE_SOURCE_SHA256:
        raise ValueError('original snapshot hash mismatch')
    original = original_namespace()
    records = []
    for scenario in original['SCENARIOS']:
        for az,el in [(0,0),(35,25),(180,-35)]:
            for repeat in range(3):
                truth,target,other = original['make_trial'](az,el,repeat,scenario)
                data = target+other
                segment = adapt_six_mic_baseline(data[:,1536:3072],sample_rate_hz=48000,
                    positions_m=original['POS'],source_id=f'{scenario}:{az}:{el}:{repeat}',
                    source_sha256=entry.BASELINE_SOURCE_SHA256,first_sample_id=1536)
                for frame in iter_frames(segment):
                    direct = data[:,1536+frame.row_start:1536+frame.row_stop]
                    delays = original['gcc'](direct)
                    direction,valid,residual,norm = original['solve'](delays)
                    result = entry.localize_frame(frame,truth)
                    actual = np.array([np.nan if x is None else x for x in result['pair_delays_samples']])
                    np.testing.assert_allclose(actual,delays,rtol=0,atol=1e-12,equal_nan=True)
                    if result['valid'] != bool(valid): raise ValueError('valid flag changed')
                    finite = np.isfinite(delays)
                    difference = float(np.max(np.abs(actual[finite]-delays[finite]))) if finite.any() else 0.
                    if valid: np.testing.assert_allclose(result['unit_vector'],direction,rtol=0,atol=1e-12)
                    for value,expected in [(result['residual_samples'],residual),(result['raw_vector_norm'],norm)]:
                        if np.isfinite(expected): np.testing.assert_allclose(value,expected,rtol=0,atol=1e-12)
                        elif value is not None: raise ValueError('undefined diagnostic changed')
                    records.append(dict(scenario=scenario,azimuth_deg=az,elevation_deg=el,repeat=repeat,
                        frame_index=frame.index,input_sha256=segment.provenance['samples_sha256'],
                        valid=bool(valid),maximum_delay_difference_samples=difference,
                        original_unit_vector=direction.tolist() if valid else None,
                        integrated_unit_vector=result['unit_vector'],
                        rejection_reasons=result['rejection_reasons'],status='PASS'))
    golden, arrays = [], {}
    positions = np.array([[-.02,-.02,0],[.02,-.02,0],[.02,.02,0],[-.02,.02,0],
                          [0,0,2**.5*.02],[0,0,-2**.5*.02]])
    axes = [('front',[1,0,0]),('back',[-1,0,0]),('left',[0,1,0]),('right',[0,-1,0]),
            ('up',[0,0,1]),('down',[0,0,-1])]
    for name,vector in axes:
        arrival = -positions@np.array(vector)*48000/343
        delays = np.array([arrival[i]-arrival[j] for i in range(6) for j in range(i+1,6)])
        result = entry.solve_delays(delays)
        np.testing.assert_allclose(result['unit_vector'],vector,rtol=0,atol=1e-12)
        rendered = original['render'](original['source'](np.random.default_rng(20260907)),np.array(vector))
        waveform = rendered[:,1536:2560]
        arrays[name] = waveform
        tau = original['gcc'](waveform)
        reference,valid,_,_ = original['solve'](tau)
        error = original['angle'](np.array(vector),reference)
        if not valid or error >= 3: raise ValueError('axis waveform check failed')
        golden.append(dict(name=name,expected_unit_vector=vector,ideal_delays_samples=delays.tolist(),
                           ideal_result=result,waveform_array=name,
                           original_waveform_delays_samples=tau.tolist(),
                           original_waveform_unit_vector=reference.tolist(),waveform_error_deg=error))
    args.out.mkdir(parents=True)
    np.savez(args.out/'axis-waveforms.npz',**arrays)
    entry.write_json(args.out/'axis-golden.json',golden)
    entry.write_json(args.out/'same-frame-comparison.json',records)
    entry.write_json(args.out/'report.json',dict(status='PASS',compared_frames=len(records),
        scenarios=original['SCENARIOS'],tolerance_absolute=1e-12,
        maximum_delay_difference_samples=max(r['maximum_delay_difference_samples'] for r in records),
        valid_flags_all_match=True,axis_golden_count=len(golden),
        baseline_source_sha256=entry.BASELINE_SOURCE_SHA256,
        source_sha256={p.relative_to(ROOT).as_posix():entry.sha256(p) for p in
            [Path(__file__),ROOT/'payload/tb/python/test_six_mic_localize.py',
             ROOT/'payload/model/python/six_mic_localize.py',ROOT/'payload/model/python/six_mic_baseline_core.py',
             ROOT/'payload/model/python/audio_frames.py',ROOT/'payload/model/python/h1_reader.py']},
        artifact_sha256={name:entry.sha256(args.out/name) for name in
            ['axis-waveforms.npz','axis-golden.json','same-frame-comparison.json']},
        scope='Integration equivalence and sign golden, not a new acoustic performance benchmark.'))
    print('PASS: 162 same-frame comparisons across 9 scenarios; 6 axis golden waveforms')
    return 0


if __name__ == '__main__': sys.exit(main())
