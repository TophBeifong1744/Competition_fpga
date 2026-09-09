"""Original PHAT + original tracker -> causal audio. No truth enters tracking."""
import argparse,hashlib,json,subprocess,sys,wave
from collections import Counter
from pathlib import Path
import numpy as np
from tracked_audio import TrackedAudio,ROOT,HERE
sys.path.insert(0,str(ROOT/'payload/model/python'))
import six_mic_track as tracker
import six_mic_localize as localize
from audio_frames import iter_frames

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def wav(p,x,gain):
    pcm=np.rint(x*gain*32767);assert np.max(np.abs(pcm))<32767
    with wave.open(str(p),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000);w.writeframes(pcm.astype('<i2').tobytes())

def execute(segment):
    # Frames are processed only at their exclusive end; event applies to the
    # following NEW samples. Preloaded offline input does not permit look-ahead.
    session=tracker.TrackingSession(tracker.load_config(ROOT/'payload/config/sector-tracking.json'))
    first=int(segment.sample_ids[0])
    audio=TrackedAudio('single',480,sample_origin=first);rows=[];outputs=[];valid=[];modes=[];cursor=0
    frames=list(iter_frames(segment))
    if len(segment.clean_intervals)!=1:raise ValueError('one continuous segment required; split gaps explicitly')
    pending=None
    for frame in frames:
        stop=frame.row_stop
        if stop>cursor:
            y,v,m=audio.process(segment.samples[cursor:stop],first_sample_id=first+cursor,tracking=pending)
            outputs.append(y);valid.append(v);modes.extend(m.tolist());cursor=stop
        row=localize.localize_frame(frame) # deliberately no source truth argument
        pending=session.update(row)
        assert abs(pending['timestamp_ms']*48-stop)<1e-7
        rows.append(dict(frame=frame.index,frame_start=frame.row_start,frame_stop=stop,applies_from_sample_id=first+stop,baseline_valid=row['valid'],tracking=pending))
    if cursor<len(segment.samples):
        y,v,m=audio.process(segment.samples[cursor:],first_sample_id=first+cursor,tracking=pending);outputs.append(y);valid.append(v);modes.extend(m.tolist())
    return np.concatenate(outputs),np.concatenate(valid),rows,modes,audio.events

def run(out):
    out.mkdir(parents=True,exist_ok=False)
    frozen={p.relative_to(ROOT).as_posix():sha(p) for p in (HERE.parent/'fixed-das-01').rglob('*') if p.is_file()}
    core={name:sha(ROOT/'payload/model/python'/name) for name in ['six_mic_baseline_core.py','six_mic_localize.py','six_mic_track.py','sector_tracker.py']}
    with (out/'tests.txt').open('w',encoding='utf-8') as f:
        result=subprocess.run([sys.executable,'-B',str(HERE/'test_tracked_audio.py')],stdout=f,stderr=subprocess.STDOUT)
    if result.returncode:raise RuntimeError('tests failed; see tests.txt')
    results=[]
    for case in ['stable','drop-return','outside']:
        directory=out/case;directory.mkdir();tracker.write_demo(directory/'input',case)
        segment,_=localize.load_input(directory/'input')
        y,valid,rows,modes,events=execute(segment)
        # Independent use of existing batch tracking entry must give same states.
        reference,_=tracker.run_tracking(segment)
        assert [r['tracking'] for r in rows]==[{k:v for k,v in r['tracking'].items() if k!='angular_error_deg'} for r in reference]
        single=np.zeros(len(y));single[4:]=segment.samples[:-4,0]
        gain=.8/max(np.max(np.abs(y)),np.max(np.abs(single)),1e-12)
        wav(directory/'single-reference.wav',single,gain);wav(directory/'auto-tracked.wav',y,gain)
        write(directory/'tracking.json',rows);write(directory/'audio-events.json',events)
        states=Counter(r['tracking']['state'] for r in rows)
        if case=='outside':assert not states['LOCKED'] and np.array_equal(y,single)
        if case=='drop-return':assert states['LOCKED'] and states['HOLD'] and states['SEARCH']
        if case=='stable':assert states['LOCKED']
        record=dict(case=case,samples=len(y),invalid_startup_samples=int(sum(~valid)),tracker_states=dict(states),audio_mode_samples=dict(Counter(modes)),
            first_fresh_ready_ms=next((r['tracking']['timestamp_ms'] for r in rows if r['tracking']['fresh_valid']),None),
            common_wav_gain=gain,output_sha256=hashlib.sha256(y.astype('<f8').tobytes()).hexdigest(),
            input_hash=segment.provenance['samples_sha256'],original_tracker_identical=True,
            scope='synthetic teaching input, no SNR claim; drop-return input itself contains silence')
        write(directory/'result.json',record);results.append(record)
    assert all(sha(ROOT/n)==h for n,h in frozen.items())
    assert core=={n:sha(ROOT/'payload/model/python'/n) for n in core}
    write(out/'run.json',dict(status='PASS_SYNTHETIC_TRACKED_AUDIO',python=sys.version,numpy=np.__version__,tests=10,cases=results,
        policy='SEARCH/ACQUIRE: delayed mic0; fresh LOCKED: beam; HOLD: display_direction until original expiry; then fade to mic0',
        fade_samples=480,fade_ms=10,unchanged_fixed_task=frozen,unchanged_defaults=core,
        source_hashes={p.name:sha(p) for p in HERE.glob('*.py')},artifacts={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}))
    print(json.dumps(results,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);run(p.parse_args().out.resolve())
