"""One command: actual tests, independent analytic demo, WAVs and provenance."""
import argparse, hashlib, json, platform, subprocess, sys, wave
from pathlib import Path
import numpy as np
from fixed_das import FixedDAS,FS,C,POSITIONS
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def array_sha(a):return hashlib.sha256(np.asarray(a,dtype='<f8').tobytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def db(a,b):return float(10*np.log10(np.mean(a*a)/np.mean(b*b)))

def render(n,u,tones):
    """Analytic continuous plane wave: x_m[n]=s(n+r_m dot u fs/c).
    No use of implementation interpolation to generate the test input.
    """
    time=(n[:,None]+POSITIONS@u*FS/C)/FS
    return sum(a*np.sin(2*np.pi*f*time+p) for f,a,p in tones)

def stream(x,u,block_size):
    b=FixedDAS(u);ys=[];masks=[]
    for start in range(0,len(x),block_size):
        y,v=b.process(x[start:start+block_size],first_sample_id=start);ys.append(y);masks.append(v)
    return np.concatenate(ys),np.concatenate(masks),b.describe()

def wav(path,data,gain):
    pcm=np.rint(np.asarray(data)*gain*32767)
    assert np.max(np.abs(pcm))<32767,'no clipping permitted'
    with wave.open(str(path),'wb') as f:
        f.setnchannels(1 if pcm.ndim==1 else pcm.shape[1]);f.setsampwidth(2);f.setframerate(FS)
        f.writeframes(pcm.astype('<i2').tobytes())

def run(out):
    out.mkdir(parents=True,exist_ok=False)
    protected=['six_mic_baseline_core.py','six_mic_localize.py','six_mic_track.py','sector_tracker.py','audio_frames.py']
    original={name:sha(ROOT/'payload/model/python'/name) for name in protected}
    command=[sys.executable,'-B',str(HERE/'test_fixed_das.py')]
    with (out/'tests.txt').open('w',encoding='utf-8') as log:
        result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    write(out/'test-result.json',dict(command=command,exit_code=result.returncode))
    if result.returncode:raise RuntimeError('tests failed; preserved tests.txt')
    count=FS*3;n=np.arange(count);u=np.array([1.,0,0]);other=np.array([-1.,0,0])
    target_tones=[(530,.5,.1),(1030,.4,.6),(1870,.3,.9),(3170,.2,1.2)]
    noise_tones=[(710,.5,.3),(1390,.4,.8),(2530,.3,.5),(3730,.2,1.4)]
    target=render(n,u,target_tones);noise=render(n,other,noise_tones);x=target+noise
    y,valid,description=stream(x,u,512)
    yt,_,_=stream(target,u,512);yn,_,_=stream(noise,u,512)
    alternate,mask,_=stream(x,u,137)
    np.testing.assert_array_equal(y,alternate);np.testing.assert_array_equal(valid,mask)
    np.testing.assert_allclose(y,yt+yn,rtol=0,atol=2e-15)
    delay=description['common_delay_samples']
    single=np.zeros(count);single[delay:]=x[:-delay,0]
    st=np.zeros(count);st[delay:]=target[:-delay,0]
    sn=np.zeros(count);sn[delay:]=noise[:-delay,0]
    # Identical interior interval for all scores; warm-up and ends excluded.
    start,stop=256,count-256;selection=slice(start,stop);assert valid[selection].all()
    before=db(st[selection],sn[selection]);after=db(yt[selection],yn[selection])
    gain=.8/max(np.max(np.abs(x)),np.max(np.abs(y)),np.max(np.abs(single)))
    wav(out/'six-channel-input.wav',x,gain)
    wav(out/'single-reference-delayed.wav',single,gain)
    wav(out/'fixed-direction-das.wav',y,gain)
    # Bound linear interpolation magnitude independently across the declared band.
    fractions=np.mod(np.array(description['channel_delay_samples']),1)
    frequencies=np.linspace(300,4000,1001)
    response=np.abs((1-fractions[:,None])+fractions[:,None]*np.exp(-2j*np.pi*frequencies[None,:]/FS))
    metrics=dict(input_kind='synthetic analytic tones, not speech; plane wave; no room reverb',
        target_direction=u.tolist(),interferer_direction=other.tolist(),target_tones=target_tones,interferer_tones=noise_tones,
        samples=count,block_size=512,alternate_block_size=137,block_outputs_bit_identical=True,linearity_checked=True,
        evaluation_samples=[start,stop],invalid_startup_samples=int(np.count_nonzero(~valid)),
        single_target_to_interferer_db=before,das_target_to_interferer_db=after,improvement_db=after-before,
        comparison='known component powers through identical filters; this one fixed synthetic scenario, not general SNR/real speech validation',
        common_wav_gain=gain,pcm='int16, common gain and rounding; WAV input is quantized audition copy, not exact float input',
        input_float64_time_by_channel_sha256=array_sha(x),output_float64_sha256=array_sha(y),
        interpolation_min_channel_gain_db=float(20*np.log10(response.min())),
        beamformer=description)
    write(out/'metrics.json',metrics)
    assert original=={name:sha(ROOT/'payload/model/python'/name) for name in protected}
    write(out/'run.json',dict(status='PASS_FIXED_DIRECTION_SYNTHETIC_ONLY',python=sys.version,numpy=np.__version__,platform=platform.platform(),
        source_sha256={p.name:sha(p) for p in HERE.glob('*.py')},unchanged_default_sources=original,
        outputs={p.name:sha(p) for p in out.iterdir() if p.is_file()},scope='No tracking integration, no hardware or H3 acceptance; no final tail flush'))
    print(json.dumps(metrics,ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);run(p.parse_args().out.resolve())
