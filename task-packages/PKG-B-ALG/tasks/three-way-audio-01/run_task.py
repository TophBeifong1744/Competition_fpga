import argparse,hashlib,json,subprocess,sys,wave
from collections import Counter
from pathlib import Path
import numpy as np
import compare_audio as c
from audio_frames import adapt_six_mic_baseline
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ah(x):return hashlib.sha256(np.asarray(x,dtype='<f8').tobytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')

def generated_case():
    b=c.previous.localize.baseline;n=147456;rng=np.random.default_rng(2026092001)
    def probe():
        f=np.fft.rfftfreq(n,1/48000);w=np.clip((f-200)/200,0,1)*np.clip((4400-f)/600,0,1)
        x=np.fft.irfft(np.fft.rfft(rng.normal(size=n))*w,n=n);return x/np.std(x)
    target=b.render(probe(),b.unit(0,0))[:,1536:-1536]
    noise=.5*b.render(probe(),b.unit(90,0))[:,1536:-1536]
    segment=adapt_six_mic_baseline(target+noise,sample_rate_hz=48000,positions_m=b.POS,source_id='three-way-directional-interference',source_sha256=sha(Path(__file__)),first_sample_id=1536)
    return segment,target.T,noise.T

def run(out):
    out.mkdir(parents=True,exist_ok=False)
    frozen={p.relative_to(ROOT).as_posix():sha(p) for name in ['fixed-das-01','tracked-audio-01'] for p in (HERE.parent/name).rglob('*') if p.is_file()}
    with (out/'tests.txt').open('w',encoding='utf-8') as stream:
        test=subprocess.run([sys.executable,'-B',str(HERE/'test_compare.py')],stdout=stream,stderr=subprocess.STDOUT)
    if test.returncode:raise RuntimeError('tests failed; see tests.txt')
    summaries=[]
    for case in ['stable','drop-return','outside','directional-interference']:
        directory=out/case;directory.mkdir();target=noise=None
        if case=='directional-interference':
            segment,target,noise=generated_case();truth=[1.,0,0]
            np.savez_compressed(directory/'input-components.npz',target=target,interference=noise)
            source=dict(kind='new synthetic diagnostic, not heldout performance',seed=2026092001,source_length=147456,crop=[1536,145920],target=[1,0,0],interferer=[0,1,0],interferer_scale=.5,propagation='original spherical periodic renderer, interior crop, no room reverberation')
        else:
            path=HERE.parent/'tracked-audio-01/evidence/run03'/case/'input'
            segment,_=c.previous.localize.load_input(path)
            truth=[0.,1.,0.] if case=='outside' else [1.,0,0]
            source=dict(kind='unchanged previous teaching input',path=path.relative_to(ROOT).as_posix(),files={p.name:sha(p) for p in path.iterdir() if p.is_file()},
                truth_note='fixed generator geometry; drop-return truth only applicable when source active; no truth inferred from audio')
        signals,valid,rows,modes,events=c.compare(segment,truth)
        # Compare against previous automatic waveform before gain/PCM, not just counts.
        if case!='directional-interference':
            previous=json.loads((HERE.parent/'tracked-audio-01/evidence/run03'/case/'result.json').read_text())
            assert ah(signals['auto'])==previous['output_sha256']
        mask=valid.copy();mask[:256]=False;mask[-256:]=False
        if case=='drop-return':
            ids=segment.sample_ids;mask&=(ids<16000)|(ids>=30008)
        gain=.8/max(max(float(np.max(np.abs(y))) for y in signals.values()),1e-12)
        for key,y in signals.items():c.previous.wav(directory/(key+'.wav'),y,gain)
        score=c.metrics(signals,mask)
        if target is not None:
            origin=int(segment.sample_ids[0]);parts={}
            for key in signals:
                def process(x):
                    if key=='single':return c.single(x)
                    if key=='manual':return c.fixed(x,truth,origin)[0]
                    return c.replay(x,origin,rows)
                t,z=process(target),process(noise)
                np.testing.assert_allclose(t+z,signals[key],rtol=0,atol=3e-15)
                score[key]['target_to_interferer_db']=float(10*np.log10(np.mean(t[mask]**2)/np.mean(z[mask]**2)))
            reference=score['single']['target_to_interferer_db']
            for key in signals:score[key]['improvement_vs_single_db']=score[key]['target_to_interferer_db']-reference
        result=dict(case=case,source=source,manual_direction=truth,input_float64_sha256=ah(segment.samples),samples=len(segment.samples),
            sample_origin=int(segment.sample_ids[0]),evaluation_samples=int(mask.sum()),common_delay_samples=4,common_wav_gain=gain,
            metrics=score,tracker_states=dict(Counter(r['tracking']['state'] for r in rows)),audio_mode_samples=dict(Counter(modes)),
            float_output_sha256={k:ah(v) for k,v in signals.items()},
            limitations='common 4-point processing delay, no cross-correlation alignment or separate normalization; manual reference is not an upper bound; error-to-manual is not speech quality',
            truth_policy='manual only; automatic unchanged; component replay uses mixture-derived control including fallback/fades')
        write(directory/'result.json',result);write(directory/'tracking.json',rows);write(directory/'audio-events.json',events)
        np.save(directory/'evaluation-mask.npy',mask,allow_pickle=False);summaries.append(result)
    assert all(sha(ROOT/n)==h for n,h in frozen.items())
    write(out/'run.json',dict(status='PASS_THREE_WAY_SYNTHETIC',tests=5,python=sys.version,numpy=np.__version__,cases=summaries,
        source_sha256={p.name:sha(p) for p in HERE.glob('*.py')},prior_tasks_unchanged=frozen,
        artifacts={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}))
    print(json.dumps([{k:r[k] for k in ['case','metrics','tracker_states']} for r in summaries],ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);run(p.parse_args().out.resolve())
