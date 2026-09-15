"""Bind new accepted center input to existing reader and manual-delay model."""
import argparse
import json
from pathlib import Path
import platform
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import check_inputs as base
from render_audio import delays_for

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    cfg=json.loads((HERE/'config.json').read_text(encoding='utf-8'))
    pins=json.loads((HERE/'pins.json').read_text(encoding='utf-8'))
    if base.sha(HERE/'pins.json')!=cfg['pins_sha256']:
        raise ValueError('PIN_MANIFEST_CHANGED')
    for name,expected in pins.items():
        if base.sha(base.ROOT/name)!=expected: raise ValueError('PIN_MISMATCH: '+name)
    out=args.out.resolve()
    if HERE.resolve() not in out.parents or out.exists():
        raise ValueError('new output file inside this revision required')
    rec=base.ReaderSession().load(base.ROOT/cfg['batch']/'delivery-01'/cfg['recording'])
    for field,want in [('sample_rate_hz',cfg['sample_rate_hz']),('coordinates_m',cfg['positions_m']),('channel_order',cfg['channel_order'])]:
        if rec.metadata[field]!=want: raise ValueError('CONFIG_MISMATCH: '+field)
    if rec.metadata['acquisition_id']!=cfg['recording'] or rec.metadata['source_kind']!='hardware-audio':
        raise ValueError('WRONG_RECORDING')
    segment=base.adapt_h1(rec)
    np.testing.assert_array_equal(segment.samples,rec.samples.astype(float)/cfg['pcm_divisor'])
    intervals=[dict(row_start=a,row_stop=b,first_sample_id=str(int(rec.sample_ids[a])),
                    last_sample_id=str(int(rec.sample_ids[b-1])),samples=b-a) for a,b in segment.clean_intervals]
    if not intervals: raise ValueError('NO_CLEAN_INTERVAL')
    steering=cfg['manual_steering']
    delays=delays_for(cfg['positions_m'],cfg['channel_order'].index(cfg['reference_channel']),
        steering['azimuth_deg'],steering['elevation_deg'],cfg['sample_rate_hz'],steering['sound_speed_m_s'])
    # Independent +X identity. Checks configuration only; no audio synthesis/render.
    np.testing.assert_allclose(delays,[0,.04*48000/343,.04*48000/343,0],rtol=0,atol=1e-12)
    for name,expected in pins.items():
        if base.sha(base.ROOT/name)!=expected: raise ValueError('PIN_CHANGED_DURING_CHECK: '+name)
    result=dict(status='STEP1_2_INPUT_BOUND_ONLY',config_sha256=base.sha(HERE/'config.json'),
        binding_source_sha256=base.sha(Path(__file__)),pins=pins,recording=cfg['recording'],
        samples=len(rec.samples),duration_s=len(rec.samples)/cfg['sample_rate_hz'],
        clean_intervals=intervals,error_rows=int(np.count_nonzero(rec.stream_error)),
        reference_channel=cfg['reference_channel'],compensation_delays_samples=delays.tolist(),
        full_scale_peak_by_channel=np.max(np.abs(segment.samples),axis=0).tolist(),
        geometry_version=rec.metadata['geometry_version'],calibration_status=rec.metadata['calibration_status'],
        audio_generated=False,acoustic_acceptance=False,
        environment=dict(python=platform.python_version(),numpy=np.__version__,platform=platform.platform()))
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8') as f: json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False); f.write('\n')
    print(json.dumps(result,ensure_ascii=False,allow_nan=False))

if __name__=='__main__': main()
