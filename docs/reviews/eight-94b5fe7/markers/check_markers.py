import json, hashlib, wave
from pathlib import Path
import numpy as np
ROOT=Path('F:/NUEC/review-worktrees/eight-94b5fe7/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/trusted-direction-input-20260918')
OUT=Path(__file__).parent
def wav(p):
    with wave.open(str(p),'rb') as f:
        assert (f.getframerate(),f.getsampwidth(),f.getnchannels())==(48000,2,1)
        return np.frombuffer(f.readframes(f.getnframes()),'<i2').astype(float)
def match(x,t):
    t=t-t.mean(); m=len(t); n=len(x); k=2**int(np.ceil(np.log2(n+m-1)))
    numerator=np.fft.irfft(np.fft.rfft(x,k)*np.conj(np.fft.rfft(t,k)),k)[:n-m+1]
    cs=np.concatenate(([0.],np.cumsum(x))); sq=np.concatenate(([0.],np.cumsum(x*x)))
    den=np.sqrt(np.maximum(sq[m:]-sq[:-m]-(cs[m:]-cs[:-m])**2/m,0)*sum(t*t))
    scores=np.divide(abs(numerator),den,out=np.zeros_like(numerator),where=den>1e-8)
    p=int(scores.argmax()); local=x[p:p+m]-x[p:p+m].mean()
    direct=abs(float(np.dot(local,t)/np.sqrt(np.dot(local,local)*np.dot(t,t))))
    assert abs(direct-scores[p])<1e-8
    return p,direct
manifest=json.loads((ROOT/'evidence/background-confirmation-20260920-01/CURRENT-DATA-SHA256.json').read_text())
timeline=json.loads((ROOT/'playback-v1/timeline.json').read_text())
source=wav(ROOT/'playback-v1/soundsight-target-v1.wav')
templates=[wav(ROOT/'playback-v1'/f'marker-{s}.wav') for s in ['start','end']]
for template,m in zip(templates,timeline['markers']):
    assert np.array_equal(template,source[m['start_sample']:m['end_sample_exclusive']])
result={'sha':'94b5fe79d87e038e895878fb31030cded469bb33','source_sha256':hashlib.sha256((ROOT/'playback-v1/soundsight-target-v1.wav').read_bytes()).hexdigest(),'templates_equal_source_segments':True,'captures':[]}
for rel in sorted(manifest):
    if not rel.endswith('/raw.bin') or 'trusted_bg_' in rel: continue
    path=ROOT/rel; x=np.frombuffer(path.read_bytes(),'<i4').reshape(-1,8)[:,2:6].astype(float)
    archived=json.loads((path.parent.parent/'alignment.json').read_text())
    channels=[]
    for c in range(4):
        peaks=[match(x[:,c],t) for t in templates]; a,b=[p[0] for p in peaks]; scale=(b-a)/204000
        old=archived['channels'][c]
        assert a==old['start_marker']['index'] and b==old['end_marker']['index']
        assert all(abs(p[1]-old[label]['absolute_correlation'])<1e-8 for p,label in zip(peaks,['start_marker','end_marker']))
        speech=[a+(v-9600)*scale for v in timeline['speech_source_interval']]
        channels.append(dict(channel=c,start=a,end=b,correlations=[p[1] for p in peaks],apparent_scale_ppm=(scale-1)*1e6,speech_samples=speech))
    lo=max(v['speech_samples'][0] for v in channels); hi=min(v['speech_samples'][1] for v in channels)
    # Analyst-selected 0.2 s inner guard is a development mask, not calibrated timing uncertainty.
    core=[int(np.ceil(lo+9600)),int(np.floor(hi-9600))]
    result['captures'].append(dict(capture=path.parent.name,channels=channels,common_source_mapped_interval_samples=[lo,hi],provisional_inner_200ms_core_samples=core,core_seconds=[v/48000 for v in core],start_peak_spread_samples=max(v['start'] for v in channels)-min(v['start'] for v in channels),end_peak_spread_samples=max(v['end'] for v in channels)-min(v['end'] for v in channels)))
result['limits']='Correlation peak and apparent affine scale can reflect multipath/phone DSP, not hardware clock measurement or exact acoustic activity labels. 200 ms guard is arbitrary, uncalibrated, and does not guarantee removal of all reverberation. No scoring permission.'
(OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n')
for row in result['captures']:
    print(row['capture'],row['core_seconds'],'spread',row['start_peak_spread_samples'],row['end_peak_spread_samples'],'ppm',[round(c['apparent_scale_ppm'],2) for c in row['channels']])
print('PASS: independent 48 chirp peaks and correlations agree with archive; direct time-domain peak checks pass')
