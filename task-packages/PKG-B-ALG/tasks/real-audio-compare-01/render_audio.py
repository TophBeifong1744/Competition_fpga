"""Offline four-channel manual DAS, linear fractional delay, common valid crop.

Not a streaming/fixed-point implementation or an acoustic acceptance test.
"""
import argparse
import json
from pathlib import Path
import platform
import wave
import numpy as np
import check_inputs as inputs

def delays_for(positions, reference, azimuth, elevation, fs, speed):
    pos = np.asarray(positions, dtype=float)
    if pos.shape != (4,3) or not np.all(np.isfinite(pos)) or not 0 <= reference < 4:
        raise ValueError('four finite positions and reference required')
    if not np.all(np.isfinite([azimuth,elevation,fs,speed])) or fs <= 0 or speed <= 0:
        raise ValueError('finite angles and positive sample rate/speed required')
    az, el = np.deg2rad([azimuth,elevation])
    u = np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
    # Arrival_i - arrival_ref = -(p_i-p_ref).u/c.
    # Compensate with positive delay: output_i[n] = input_i[n-delay_i].
    return (pos-pos[reference])@u*fs/speed

def render_interval(samples, delays, reference=0):
    x = np.asarray(samples, dtype=float)
    d = np.asarray(delays, dtype=float)
    if x.ndim != 2 or x.shape[1] != 4 or len(x)==0 or d.shape != (4,):
        raise ValueError('nonempty time x four channels and four delays required')
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(d)):
        raise ValueError('nonfinite input')
    if reference not in range(4) or abs(d[reference]) > 1e-12:
        raise ValueError('reference must have zero delay')
    start = max(0, int(np.ceil(d.max())))
    stop = min(len(x), int(np.floor(len(x)-1+d.min()))+1)
    if stop <= start:
        raise ValueError('interval too short for steering delays')
    n = np.arange(start,stop)
    aligned = np.empty((len(n),4))
    for ch in range(4):
        source = n-d[ch]
        left = np.floor(source).astype(np.int64)
        weight = source-left
        right = np.minimum(left+1,len(x)-1)
        if np.any(left < 0) or np.any(source > len(x)-1):
            raise ValueError('invalid crop: no padding or circular wrap allowed')
        aligned[:,ch] = (1-weight)*x[left,ch]+weight*x[right,ch]
    return x[start:stop,reference].copy(), aligned.mean(axis=1), start, stop

def encode_pcm24(signal):
    x = np.asarray(signal,dtype=float)
    if x.ndim != 1 or not np.all(np.isfinite(x)):
        raise ValueError('finite mono signal required')
    rounded = np.rint(x*2**23)
    saturated = int(np.count_nonzero((rounded < -2**23)|(rounded > 2**23-1)))
    codes = np.clip(rounded,-2**23,2**23-1).astype(np.int64)
    packed = codes & 0xffffff
    data = np.column_stack([packed & 255,(packed>>8)&255,(packed>>16)&255]).astype(np.uint8).tobytes()
    return data, saturated

def write_wav(path, signal, fs):
    data, saturated = encode_pcm24(signal)
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1); w.setsampwidth(3); w.setframerate(int(fs)); w.writeframes(data)
    with wave.open(str(path),'rb') as w:
        if (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes()) != (1,3,int(fs),len(signal)):
            raise RuntimeError('WAV header verification failed')
        raw = np.frombuffer(w.readframes(w.getnframes()),dtype=np.uint8).reshape(-1,3).astype(np.int64)
    decoded = raw[:,0]+(raw[:,1]<<8)+(raw[:,2]<<16)
    decoded = np.where(decoded >= 2**23,decoded-2**24,decoded)
    expected = np.clip(np.rint(signal*2**23),-2**23,2**23-1).astype(np.int64)
    np.testing.assert_array_equal(decoded,expected)
    return dict(file=path.name,sha256=inputs.sha(path),frames=len(signal),
        saturation_samples=saturated,peak_abs=float(np.max(np.abs(signal))),
        rms=float(np.sqrt(np.mean(signal**2))),
        pcm_roundtrip_exact=True,
        max_quantization_error=float(np.max(np.abs(decoded/2**23-signal))))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out',type=Path,required=True)
    args = ap.parse_args()
    here = inputs.HERE
    cfg = json.loads((here/'config.json').read_text(encoding='utf-8'))
    rcfg = json.loads((here/'render-config.json').read_text(encoding='utf-8'))
    manifest = inputs.ROOT/cfg['input_manifest']
    if inputs.sha(manifest) != cfg['input_manifest_sha256']:
        raise ValueError('HISTORICAL_MANIFEST_MISMATCH')
    hashes = json.loads(manifest.read_text(encoding='utf-8'))
    for name,expected in hashes.items():
        if inputs.sha(inputs.ROOT/name) != expected: raise ValueError('INPUT_HASH_MISMATCH: '+name)
    if rcfg['input_config_sha256'] != inputs.sha(here/'config.json'):
        raise ValueError('INPUT_CONFIG_CHANGED')
    if rcfg['interpolation'] != 'linear' or rcfg['weights'] != [.25]*4:
        raise ValueError('UNSUPPORTED_RENDER_CONFIGURATION')
    gain = rcfg['preview_common_gain']
    if not isinstance(gain,(int,float)) or not np.isfinite(gain) or gain <= 0:
        raise ValueError('positive preview gain required')
    reference = cfg['channel_order'].index(cfg['reference_channel'])
    steering = cfg['manual_steering']
    delays = delays_for(cfg['positions_m'],reference,steering['azimuth_deg'],steering['elevation_deg'],cfg['sample_rate_hz'],steering['sound_speed_m_s'])
    out = args.out.resolve()
    batch = (inputs.ROOT/cfg['batch']).resolve()
    if out == batch or batch in out.parents: raise ValueError('frozen input output prohibited')
    out.mkdir(parents=True,exist_ok=False)
    records = []
    session = inputs.ReaderSession()
    for name in cfg['recordings']:
        rec = session.load(batch/'delivery-01'/name)
        for key,val in [('sample_rate_hz',cfg['sample_rate_hz']),('channel_order',cfg['channel_order']),('coordinates_m',cfg['positions_m'])]:
            if rec.metadata[key] != val: raise ValueError('CONFIGURATION_MISMATCH: '+key)
        segment = inputs.adapt_h1(rec)
        if not segment.clean_intervals: raise ValueError('NO_CLEAN_INTERVAL')
        for index,(a,b) in enumerate(segment.clean_intervals):
            # Never concatenate recordings, cross errors, or retain padded boundaries.
            single,manual,start,stop = render_interval(segment.samples[a:b],delays,reference)
            prefix = f'{name}-interval{index:02}'
            files=[]
            for label,signal in [('single',single),('manual',manual)]:
                for mode,g in [('raw',1.),('preview',gain)]:
                    result = write_wav(out/f'{prefix}-{label}-{mode}.wav',signal*g,cfg['sample_rate_hz'])
                    result.update(branch=label,mode=mode,gain=g)
                    files.append(result)
            records.append(dict(recording=name,interval=index,source_row_start=a+start,source_row_stop=a+stop,
                first_reference_sample_id=str(int(rec.sample_ids[a+start])),
                last_reference_sample_id=str(int(rec.sample_ids[a+stop-1])),
                discarded_left=start,discarded_right=b-a-stop,
                output_duration_s=len(single)/cfg['sample_rate_hz'],files=files))
            print(f'{name}: {len(single)} paired samples; crop [{a+start},{a+stop}); saturation='+str(sum(f['saturation_samples'] for f in files)),flush=True)
    for name,expected in hashes.items():
        if inputs.sha(inputs.ROOT/name) != expected: raise RuntimeError('INPUT_CHANGED_DURING_RUN')
    report = dict(status='AUTHOR_OFFLINE_RENDER_ONLY',input_hashes=hashes,
        input_config=cfg,render_config=rcfg,compensation_delays_samples=delays.tolist(),
        delay_definition='output_i[n]=input_i[n-delay_i]; relative to mic0, not an additional delay applied to single reference',
        records=records,environment=dict(python=platform.python_version(),numpy=np.__version__,platform=platform.platform()),
        sources={p.relative_to(inputs.ROOT).as_posix():inputs.sha(p) for p in
            [Path(__file__),here/'check_inputs.py',here/'config.json',here/'render-config.json',inputs.MODEL/'h1_reader.py',inputs.MODEL/'audio_frames.py']},
        listening_completed=False,acoustic_acceptance=False,
        limits=['Linear interpolation has fractional-delay-dependent frequency attenuation; no calibrated gain claim.',
                'Finite offline valid crop; no streaming state, fixed-point DAS, tracker, or automatic beam.',
                '0.667 second uncalibrated near-field recording; trial steering is not ground truth.'])
    (out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print('PASS: generated 24-bit WAVs and verified decoded PCM; see result.json for limitations.')

if __name__ == '__main__': main()
