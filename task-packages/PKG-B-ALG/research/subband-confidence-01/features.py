"""Truth-free subband diagnostic; empirical envelope is NOT a confidence probability."""
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'payload/model/python'))
import six_mic_baseline_core as b
from audio_frames import to_six_mic_baseline
from six_mic_localize import solve_delays

def subband_candidates(frame,bands):
    x=np.fft.rfft(to_six_mic_baseline(frame)*np.hanning(b.N),axis=1)
    f=np.fft.rfftfreq(b.N,1/b.FS);full=(f>=300)&(f<=4000)
    delays=[[] for _ in bands];bins=[[] for _ in bands]
    for i,j in b.PAIRS:
        cross=x[i]*x[j].conj();amp=np.abs(cross)
        original=full&(amp>=.02*max(float(amp[full].max()),1e-15))
        for k,(low,high) in enumerate(bands):
            mask=original&(f>=low)&((f<=high) if k==len(bands)-1 else (f<high))
            bins[k].append(int(mask.sum()))
            if mask.sum()<12:delays[k].append(np.nan);continue
            spectrum=np.where(mask,cross/np.maximum(amp,1e-15),0)
            corr=np.fft.irfft(spectrum,n=b.N)
            bound=np.linalg.norm(b.POS[i]-b.POS[j])/b.C*b.FS
            lags=np.arange(-int(np.ceil(bound)),int(np.ceil(bound))+1)
            peak=int(lags[np.argmax(corr[lags%b.N])]);ym,y0,yp=corr[(peak-1)%b.N],corr[peak%b.N],corr[(peak+1)%b.N]
            den=ym-2*y0+yp;delta=np.clip(.5*(ym-yp)/den,-.5,.5) if den < -1e-15 else 0.
            tau=peak+delta;delays[k].append(tau if abs(tau)<=bound+.05 else np.nan)
    return [solve_delays(tau)|dict(retained_bins=counts) for tau,counts in zip(delays,bins)]

def assess(full,subs,config):
    good=[r for r in subs if r['valid']];vectors=[np.array(r['unit_vector']) for r in good]
    if full['valid']:vectors.append(np.array(full['unit_vector']))
    spread=max((b.angle(u,v) for i,u in enumerate(vectors) for v in vectors[i+1:]),default=None)
    angles=[b.angle(np.array([1.,0,0]),v) for v in vectors]
    cone_max=max(angles) if angles else None
    joint=0;span=None
    if len(good)>=2:
        tau=np.array([[np.nan if t is None else t for t in r['pair_delays_samples']] for r in good])
        common=np.isfinite(tau).all(axis=0);joint=int(common.sum())
        if joint:span=float(np.median(np.ptp(tau[:,common],axis=0)))
    if not full['valid']:category='full_rejected'
    elif len(good)<config['minimum_valid_subbands'] or joint<config['minimum_joint_finite_pairs']:category='unsupported'
    elif spread>config['maximum_direction_spread_deg'] or span>config['maximum_median_delay_span_samples']:category='inconsistent'
    elif cone_max>30+1e-10:category='boundary_uncertain'
    else:category='inside_supported'
    return dict(valid_subbands=len(good),joint_pairs=joint,direction_spread=spread,median_delay_span=span,cone_max=cone_max,
        category=category,consistent=category in ['boundary_uncertain','inside_supported'],inside_supported=category=='inside_supported')

def screened(full,diagnostic,boundary=False):
    accept=diagnostic['inside_supported'] if boundary else diagnostic['consistent']
    if accept:return full.copy()
    return full|dict(valid=False,unit_vector=None,azimuth_deg=None,elevation_deg=None,rejection_reasons=['subband_'+diagnostic['category']])
