"""Pinned four-channel recording -> aligned single/manual/diagnostic-auto WAVs."""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import sys
import traceback

import numpy as np

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
ROOT = PARENT.parents[3]
MANUAL = PARENT.parent/'real-audio-compare-01'
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(PARENT))
sys.path.insert(0, str(MANUAL))
from tracking import Config, DiagnosticSession
from h1_reader import ReaderSession
from audio_frames import adapt_h1
from render_audio import delays_for, render_interval, write_wav
from mixer import mix_timeline

spec=importlib.util.spec_from_file_location('parent_comparison',PARENT/'verify.py')
comparison=importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def verify_inputs():
    pins = load(HERE/'pins.json')
    # Validate the complete earlier snapshot without modifying its strict
    # directory-inventory verifier to hide this new, explicit revision directory.
    for relative, expected in load(PARENT/'MANIFEST.json').items():
        if sha(PARENT/relative) != expected: raise ValueError('PARENT_SNAPSHOT_CHANGED: '+relative)
    for relative, expected in (load(PARENT/'pins.json') | pins).items():
        if sha(ROOT/relative) != expected: raise ValueError('PIN_MISMATCH: '+relative)
    return load(PARENT/'pins.json') | pins


def prepare_events(frames, ids, a, b, interval_index, cfg):
    origin = int(ids[0])
    interval_origin = int(ids[a])-origin
    fs = cfg['sample_rate_hz']
    session = DiagnosticSession(Config(**cfg['tracker']))
    session.begin_interval(interval_index)
    vectors = [None]
    events = []
    for frame in frames:
        if frame['interval_index'] != interval_index: continue
        first, last = frame['row_start'], frame['row_stop']-1
        if not a <= first <= last < b:
            raise ValueError('FRAME_CROSSES_INTERVAL')
        if frame['first_sample_id'] != str(int(ids[first])) or frame['last_sample_id'] != str(int(ids[last])):
            raise ValueError('FRAME_SAMPLE_ID_MISMATCH')
        relative_end = int(ids[last])-origin+1
        ready_ms = relative_end/fs*1000
        if ready_ms != frame['frame_ready_ms']:
            raise ValueError('FRAME_READY_MISMATCH')
        result = session.update(ready_ms,frame['projection'],interval_index=interval_index,
                                reset_before=frame['reset_before'])
        # Frozen frame records are replayed, not replaced by scene position.
        stats=dict(float_values=0,discrete_values=0,max_abs_error=0.)
        comparison.compare_values(frame['tracker'],result['tracker'],'tracker',stats)
        route = result['diagnostic_route']
        vector = route['direction']
        if vector not in vectors: vectors.append(vector)
        target = vectors.index(vector)
        last_fresh_count = None
        if target:
            # Recover sample clock from the frame that last refreshed the lock.
            fresh = result['tracker']['last_fresh_ms']
            last_fresh_count = round(fresh*fs/1000)-interval_origin
        events.append(dict(frame_index=frame['frame_index'],ready=relative_end-interval_origin,
            ready_ms=ready_ms,target=target,mode=route['mode'],state=result['tracker']['state'],
            fresh=result['tracker']['fresh_valid'],
            tracker_replay_max_abs_error=stats['max_abs_error'],
            valid_through=last_fresh_count+cfg['tracker']['hold_ms']*fs/1000 if target else None))
    return vectors, events


def render_clean(x, vectors, events, cfg, audio):
    fs = cfg['sample_rate_hz']
    positions = np.asarray(cfg['positions_m'])
    radius = int(math.ceil(np.linalg.norm(positions-positions[0],axis=1).max()*fs/cfg['sound_speed_m_s']))
    start, stop = radius, len(x)-radius
    if stop <= start: raise ValueError('INTERVAL_TOO_SHORT_FOR_COMMON_CROP')
    dmanual = delays_for(positions,0,audio['manual_azimuth_deg'],0,fs,cfg['sound_speed_m_s'])
    _, manual, left, right = render_interval(x,dmanual)
    if left > start or right < stop: raise ValueError('MANUAL_CROP_NOT_COVERED')
    manual = manual[start-left:stop-left]
    bank = [x[start:stop,0].copy()]
    delays = [None]
    for vector in vectors[1:]:
        u = np.asarray(vector,dtype=float)
        if u.shape != (3,) or not np.isfinite(u).all() or abs(np.linalg.norm(u)-1) > 1e-12 or abs(u[2]) > 1e-12:
            raise ValueError('HORIZONTAL_UNIT_VECTOR_REQUIRED')
        # Same sign/reference as unchanged delays_for(), avoiding re-quantizing angles.
        d = (positions-positions[0])@u*fs/cfg['sound_speed_m_s']
        if np.max(np.abs(d)) > radius: raise ValueError('DAS_DELAY_EXCEEDS_CAUSAL_RADIUS')
        _, beam, left, right = render_interval(x,d)
        if left > start or right < stop: raise ValueError('AUTOMATIC_CROP_NOT_COVERED')
        bank.append(beam[start-left:stop-left]); delays.append(d.tolist())
    bank = np.asarray(bank)
    auto, weights, targets = mix_timeline(bank,start,stop,events,audio['fade_samples'])
    return dict(single=bank[0],manual=manual,automatic=auto,weights=weights,targets=targets,
                start=start,stop=stop,radius=radius,delays=delays,manual_delays=dmanual.tolist())


def execute(out):
    pins = verify_inputs()
    cfg = load(PARENT/'config.json')
    audio = load(HERE/'config.json')
    if audio != dict(version='four-channel-auto-audio-0.1',manual_azimuth_deg=0,fade_samples=480,
                     pcm_bits=24,preview_common_gain=32,reference_channel=0,
                     schedule='reference_sample_clock_zero_compute_delay',crop='all_horizontal_radius'):
        raise ValueError('UNSUPPORTED_AUDIO_CONFIG')
    before = {p.relative_to(ROOT).as_posix():sha(p) for p in list(HERE.glob('*.py'))+[HERE/'config.json',HERE/'pins.json']}
    records = []
    for item in cfg['recordings']:
        rec = ReaderSession().load(ROOT/item['directory'])
        if rec.metadata['coordinates_m'] != cfg['positions_m'] or rec.metadata['sample_rate_hz'] != cfg['sample_rate_hz']:
            raise ValueError('INPUT_CONFIG_MISMATCH')
        segment = adapt_h1(rec)
        if segment.direction_policy.startswith('forbidden'): raise ValueError('NON_ACOUSTIC_INPUT')
        frames = load(PARENT/('evidence/run01/replay/'+item['label']+'-frames.json'))
        for index,(a,b) in enumerate(segment.clean_intervals):
            vectors, events = prepare_events(frames,rec.sample_ids,a,b,index,cfg)
            r = render_clean(segment.samples[a:b],vectors,events,cfg,audio)
            start, stop = r['start'],r['stop']
            prefix = item['label']+f'-interval{index:02}'
            files=[]
            for label in ('single','manual','automatic'):
                for mode,gain in [('raw',1),('preview',audio['preview_common_gain'])]:
                    detail = write_wav(out/f'{prefix}-{label}-{mode}.wav',r[label]*gain,cfg['sample_rate_hz'])
                    detail.update(branch=label,mode=mode,gain=gain)
                    if detail['saturation_samples']: raise RuntimeError('WAV_SATURATION')
                    files.append(detail)
            np.testing.assert_array_equal(np.rint(r['single']*2**23).astype(np.int64),rec.samples[a+start:a+stop,0])
            np.savez_compressed(out/(prefix+'-mix.npz'),weights=r['weights'],targets=r['targets'])
            beam_share=1-r['weights'][:,0]
            single_only=int(np.count_nonzero(beam_share==0))
            pure_beam=int(np.count_nonzero(r['weights'][:,0]==0))
            record=dict(label=item['label'],interval=index,input_rows=[a,b],reference_rows=[a+start,a+stop],
                first_reference_sample_id=str(int(rec.sample_ids[a+start])),last_reference_sample_id=str(int(rec.sample_ids[a+stop-1])),
                samples=stop-start,duration_seconds=(stop-start)/cfg['sample_rate_hz'],common_availability_delay_samples=r['radius'],
                physical_emit_rows=[a+start+r['radius'],a+stop+r['radius']],
                bank_vectors=vectors,bank_delays_samples=r['delays'],manual_delays_samples=r['manual_delays'],
                events=events,files=files,sample_mix=dict(single_only=single_only,beam_only=pure_beam,
                    single_beam_mixed=stop-start-single_only-pure_beam),
                max_weight_step=float(np.max(np.abs(np.diff(r['weights'],axis=0)))) if len(beam_share)>1 else 0,
                automatic_vs_single_rms=float(np.sqrt(np.mean((r['automatic']-r['single'])**2))),
                direction_accepted=False,listening_completed=False)
            records.append(record)
            print(f'{prefix}: samples={stop-start}, bank={len(vectors)}, gain=32, saturation=0, mix={record["sample_mix"]}',flush=True)
    if pins != verify_inputs(): raise RuntimeError('INPUT_CHANGED')
    if any(sha(ROOT/p)!=h for p,h in before.items()): raise RuntimeError('SOURCE_CHANGED')
    result=dict(status='AUTHOR_DIAGNOSTIC_AUDIO_ONLY',parent_commit='e93169d526e9e94a98947c86d2c92bcab3c46a2e',
        config=audio,input_pins=pins,source_sha256=before,records=records,
        environment=dict(python=platform.python_version(),numpy=np.__version__,platform=platform.platform()),
        limits=['No target-presence gate or acoustic accuracy/benefit approval; quiet is an unmatched background probe.',
                'Offline cached beam bank, floating linear interpolation; not real streaming or fixed-point/RTL budget.',
                'Directions ready at reference n only; emit availability n+8 samples, zero compute-delay assumption.',
                'Individual expired beams have zero weight; fade begins before expiry, even without new events.',
                'Shared preview gain is 32; no per-branch normalization; future continuous playback pending.'])
    dump(out/'result.json',result)
    dump(out/'SHA256.json',{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()})


def main():
    ap=argparse.ArgumentParser(__doc__)
    ap.add_argument('--out',type=Path,required=True)
    out=ap.parse_args().out.resolve()
    frozen=(ROOT/'task-packages/PKG-A-ACQ').resolve()
    if out==frozen or frozen in out.parents: raise ValueError('FROZEN_INPUT_OUTPUT_PROHIBITED')
    out.mkdir(parents=True,exist_ok=False)
    try: execute(out)
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8')
        raise


if __name__=='__main__': main()
