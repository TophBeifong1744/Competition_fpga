from pathlib import Path
import sys,importlib.util
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'payload/model/python'))
import six_mic_baseline_core as b
from audio_frames import to_six_mic_baseline
from six_mic_localize import solve_delays
spec=importlib.util.spec_from_file_location('previous_subband_features',ROOT/'research/subband-confidence-01/features.py')
legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)

def estimates(frame,bands):
    x=np.fft.rfft(to_six_mic_baseline(frame)*np.hanning(b.N),axis=1);f=np.fft.rfftfreq(b.N,1/b.FS)
    band=(f>=300)&(f<=4000);delays=[[] for _ in range(len(bands)+1)];counts=[[] for _ in delays]
    for i,j in b.PAIRS:
        z=x[i]*x[j].conj();amp=np.abs(z);mask=band&(amp>=.02*max(float(amp[band].max()),1e-15))
        weights=amp**.25;cap=1.5*float(np.median(weights[mask])) if mask.any() else 0.
        spectrum=np.where(mask,z/np.maximum(amp,1e-15)*np.minimum(weights,cap),0)
        masks=[mask]+[mask&~((f>=lo)&((f<=hi) if k==len(bands)-1 else (f<hi))) for k,(lo,hi) in enumerate(bands)]
        for k,keep in enumerate(masks):
            counts[k].append(int(keep.sum()))
            if keep.sum()<12:delays[k].append(np.nan);continue
            corr=np.fft.irfft(np.where(keep,spectrum,0),n=b.N)
            bound=np.linalg.norm(b.POS[i]-b.POS[j])/b.C*b.FS
            lags=np.arange(-int(np.ceil(bound)),int(np.ceil(bound))+1);peak=int(lags[np.argmax(corr[lags%b.N])])
            ym,y0,yp=corr[(peak-1)%b.N],corr[peak%b.N],corr[(peak+1)%b.N];den=ym-2*y0+yp
            delta=np.clip(.5*(ym-yp)/den,-.5,.5) if den < -1e-15 else 0.;tau=peak+delta
            delays[k].append(tau if abs(tau)<=bound+.05 else np.nan)
    return [solve_delays(t)|dict(retained_bins=n) for t,n in zip(delays,counts)]

def assess(full,deleted,config):
    angles=[];changes=[];crossings=0;comparable=[]
    if full['valid']:
        tau=np.array([np.nan if x is None else x for x in full['pair_delays_samples']]);u=np.array(full['unit_vector'])
        full_inside=b.angle(u,np.array([1.,0,0]))<=30+1e-10
        for k,r in enumerate(deleted):
            if not r['valid']:continue
            other=np.array([np.nan if x is None else x for x in r['pair_delays_samples']]);common=np.isfinite(tau)&np.isfinite(other)
            if common.sum()<config['minimum_joint_pairs_per_deletion']:continue
            comparable.append(k);v=np.array(r['unit_vector']);angles.append(b.angle(u,v));changes.append(float(np.median(np.abs(tau[common]-other[common]))))
            crossings+=full_inside!=(b.angle(v,np.array([1.,0,0]))<=30+1e-10)
    angle=max(angles) if angles else None;change=max(changes) if changes else None
    if not full['valid']:category='full_rejected'
    elif len(comparable)<config['minimum_comparable_deletions']:category='unknown'
    elif angle>config['max_angle_change_deg'] or change>config['max_median_pair_delay_change_samples']:category='sensitive'
    else:category='stable'
    return dict(category=category,comparable_count=len(comparable),comparable_indices=comparable,max_angle_change=angle,max_median_delay_change=change,cone_crossings=int(crossings))

def screen(full,d,unknown_pass=False):
    if d['category']=='stable' or (unknown_pass and d['category']=='unknown'):return full.copy()
    return full|dict(valid=False,unit_vector=None,azimuth_deg=None,elevation_deg=None,rejection_reasons=['loo_'+d['category']])
