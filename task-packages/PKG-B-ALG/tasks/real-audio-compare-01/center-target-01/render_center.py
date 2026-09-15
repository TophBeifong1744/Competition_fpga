"""New center recording entry; original reader, DAS and PCM writer unchanged."""
import argparse
import json
import math
from pathlib import Path
import platform
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import check_inputs as base
from render_audio import delays_for,render_interval,write_wav

def verify_pins(cfg):
    pins=json.loads((HERE/'pins.json').read_text(encoding='utf-8'))
    if base.sha(HERE/'pins.json')!=cfg['pins_sha256']:
        raise ValueError('PIN_MANIFEST_CHANGED')
    for name,want in pins.items():
        if base.sha(base.ROOT/name)!=want: raise ValueError('PIN_MISMATCH: '+name)
    return pins

def preview_gain(peak):
    if not math.isfinite(peak) or peak<0: raise ValueError('invalid peak')
    if peak==0: return 1.
    gain=min(128.,2.**math.floor(math.log2(.5/peak)))
    if peak*gain>.5: gain/=2  # Roundoff-safe upper bound.
    return gain

def run(out):
    out=Path(out).resolve()
    evidence=(HERE/'evidence').resolve()
    if evidence not in out.parents or out.exists():
        raise ValueError('new output directory inside this revision/evidence required')
    cfg=json.loads((HERE/'config.json').read_text(encoding='utf-8'))
    rcfg=json.loads((HERE/'render-config.json').read_text(encoding='utf-8'))
    if base.sha(HERE/'config.json')!=rcfg['input_config_sha256']:
        raise ValueError('INPUT_CONFIG_CHANGED')
    expected=dict(version='center-manual-linear-0.1',input_config_sha256=rcfg['input_config_sha256'],
        interpolation='reuse_approved_linear_render_interval',weights=[.25]*4,pcm_bits=24,
        preview_gain_rule='power_of_two_at_most_128_keep_peak_at_most_0.5',
        gain_peak_scope='all_clean_four_channel_input_and_both_output_branches',
        common_preview_gain=True,preview_gain_for_all_zero_input=1,raw_gain=1,streaming=False)
    if rcfg!=expected: raise ValueError('UNSUPPORTED_RENDER_CONFIGURATION')
    pins=verify_pins(cfg)
    rec=base.ReaderSession().load(base.ROOT/cfg['batch']/'delivery-01'/cfg['recording'])
    for key,want in [('sample_rate_hz',cfg['sample_rate_hz']),('coordinates_m',cfg['positions_m']),
                     ('channel_order',cfg['channel_order']),('acquisition_id',cfg['recording']),('source_kind','hardware-audio')]:
        if rec.metadata[key]!=want: raise ValueError('CONFIG_MISMATCH: '+key)
    segment=base.adapt_h1(rec)
    ref=cfg['channel_order'].index(cfg['reference_channel'])
    s=cfg['manual_steering']
    d=delays_for(cfg['positions_m'],ref,s['azimuth_deg'],s['elevation_deg'],cfg['sample_rate_hz'],s['sound_speed_m_s'])
    pending=[]; peak=0.
    for a,b in segment.clean_intervals:
        x=segment.samples[a:b]
        single,manual,start,stop=render_interval(x,d,ref)
        peak=max(peak,float(np.max(np.abs(x))),float(np.max(np.abs(single))),float(np.max(np.abs(manual))))
        pending.append((a,b,start,stop,single,manual))
    if not pending: raise ValueError('NO_CLEAN_INTERVAL')
    gain=preview_gain(peak)
    out.mkdir(parents=True,exist_ok=False)
    records=[]
    for idx,(a,b,start,stop,single,manual) in enumerate(pending):
        files=[]
        for label,x in [('single',single),('manual',manual)]:
            for mode,g in [('raw',1.),('preview',gain)]:
                item=write_wav(out/f'interval{idx:02}-{label}-{mode}.wav',x*g,cfg['sample_rate_hz'])
                item.update(branch=label,mode=mode,gain=g);files.append(item)
        # Fixed-scale single reference must equal the original PCM crop exactly.
        np.testing.assert_array_equal(np.rint(single*2**23).astype(np.int64),rec.samples[a+start:a+stop,ref])
        records.append(dict(interval=idx,input_row_start=a,input_row_stop=b,
            output_reference_row_start=a+start,output_reference_row_stop=a+stop,
            first_reference_sample_id=str(int(rec.sample_ids[a+start])),
            last_reference_sample_id=str(int(rec.sample_ids[a+stop-1])),
            discarded_left=start,discarded_right=b-a-stop,
            duration_s=len(single)/cfg['sample_rate_hz'],files=files))
    verify_pins(cfg)
    report=dict(status='AUTHOR_OFFLINE_RENDER_ONLY',recording=cfg['recording'],config=cfg,render_config=rcfg,
        pins=pins,compensation_delays_samples=d.tolist(),preview_peak_basis=peak,preview_common_gain=gain,
        records=records,source_sha256={p.relative_to(base.ROOT).as_posix():base.sha(p) for p in
          [Path(__file__),HERE/'config.json',HERE/'render-config.json',HERE/'pins.json']},
        environment=dict(python=platform.python_version(),numpy=np.__version__,platform=platform.platform()),
        new_recording_listening_completed=False,acoustic_gain_verified=False,
        limits=['Offline linear interpolation; frequency-dependent attenuation remains.',
                'Operator-reported center +X at 1.5m; no precise truth or clean/noise reference.',
                'No streaming, automatic steering, fixed-point DAS or board audio verification.'])
    (out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(f'PASS: {len(records)} interval(s), preview gain {gain:g}, peak basis {peak:.9f}; no input changes.')
    for r in records:
        print(f"crop [{r['output_reference_row_start']},{r['output_reference_row_stop']}), samples {r['files'][0]['frames']}, saturation {sum(f['saturation_samples'] for f in r['files'])}")
    return report

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True)
    run(ap.parse_args().out)
