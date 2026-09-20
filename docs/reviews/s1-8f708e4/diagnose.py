"""Independent raw-PCM observations; no acoustic truth or algorithm acceptance."""
import csv,hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path('F:/NUEC/review-worktrees/s1-8f708e4/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/background-target-stop-20260917')
OUT=Path(__file__).parent
raw=(ROOT/'delivery-01/c-scene-20260917-01/raw.bin').read_bytes()
u=np.frombuffer(raw,dtype='<u4').reshape(-1,8)
ids=u[:,0].astype(np.uint64)+(u[:,1].astype(np.uint64)<<32)
x=u[:,2:6].view('<i4').astype(np.float64)
assert len(raw)==9224000 and len(x)==288250
assert ids[0]==17246 and ids[-1]==305495 and np.all(np.diff(ids)==1)
assert np.all(u[:,6:]==0) and np.all((x>=-2**23)&(x<2**23))
def stats(y):
    z=y-y.mean(axis=0)
    return {'mean':y.mean(axis=0).tolist(),'raw_rms':np.sqrt(np.mean(y*y,axis=0)).tolist(),'demeaned_rms':np.sqrt(np.mean(z*z,axis=0)).tolist(),'peak_absolute':np.max(np.abs(y),axis=0).tolist()}
phases=[]
for label,a,b in [('nominal_0_2s',0,96000),('nominal_2_5s',96000,240000),('nominal_5s_end',240000,len(x))]:
    phases.append(dict(label=label,start=a,stop=b,**stats(x[a:b])))
old=json.loads((ROOT/'delivery-01/phase-statistics.json').read_text())
for a,b in zip(phases,old['phases']):assert np.allclose(a['raw_rms'],b['raw_rms'],rtol=1e-12)
# 20 ms nonoverlapping complete windows, independently demeaned. Last partial window omitted only in plot/short-time summary.
hop=960;blocks=x[:len(x)//hop*hop].reshape(-1,hop,4)
ac=blocks-blocks.mean(axis=1,keepdims=True)
rms=np.sqrt(np.mean(ac*ac,axis=1));times=(np.arange(len(blocks))+.5)*.02
with (OUT/'short-time-rms.csv').open('x',newline='') as f:
    w=csv.writer(f);w.writerow(['center_s','mic0','mic1','mic2','mic3']);w.writerows(zip(times,*rms.T))
# Welch-style Hann periodograms for descriptive band shares, not SNR.
bands=[(0,100),(100,300),(300,3400),(3400,8000),(8000,24001)]
N=4096;freq=np.fft.rfftfreq(N,1/48000);win=np.hanning(N)
spectra=[]
for phase in phases:
    y=x[phase['start']:phase['stop']]
    frames=np.stack([y[s:s+N] for s in range(0,len(y)-N+1,2048)])
    frames=frames-frames.mean(axis=1,keepdims=True)
    p=np.mean(np.abs(np.fft.rfft(frames*win[None,:,None],axis=1))**2,axis=0)
    p[1:-1]*=2
    shares=[(p[(freq>=lo)&(freq<hi)].sum(axis=0)/p.sum(axis=0)).tolist() for lo,hi in bands]
    spectra.append({'phase':phase['label'],'bands_hz':bands,'fraction_of_windowed_power':shares,'dominant_bin_hz':freq[np.argmax(p,axis=0)].tolist()})
background=np.array(phases[0]['demeaned_rms'])
ratios=[(np.array(p['demeaned_rms'])/background).tolist() for p in phases[1:]]
db=[(20*np.log10(r)).tolist() for r in ratios]
half=[]
for a in np.arange(0,6,.5):half.append({'start_s':float(a),'stop_s':float(a+.5),**stats(x[int(a*48000):int((a+.5)*48000)])})
result={'review_sha':'8f708e42caf32c1de6f30726298e3edf0e1970b6','raw_sha256':hashlib.sha256(raw).hexdigest(),'groups':len(x),'bytes':len(raw),'first_id':int(ids[0]),'last_id':int(ids[-1]),'flags_and_reserved_all_zero':True,'nominal_sample_rate_hz':48000,'seconds_by_configured_rate':len(x)/48000,'phases':phases,'demeaned_rms_ratio_to_nominal_background':ratios,'level_difference_db_not_snr':db,'half_second_bins':half,'band_observations':spectra,'channel_zero_lag_correlation':np.corrcoef(x.T).tolist(),'channels_pairwise_identical':bool(any(np.array_equal(x[:,i],x[:,j]) for i in range(4) for j in range(i))),'short_time_window_samples':hop,'short_time_omitted_tail_samples':len(x)%hop,'limits':'Operator boundaries only; no detected speech labels, true background reference, listening assessment, direction or SNR gain. Level differences are energy observations only.'}
(OUT/'diagnosis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'phases':phases,'ratio':ratios,'level_db_not_snr':db,'bands':spectra}))
