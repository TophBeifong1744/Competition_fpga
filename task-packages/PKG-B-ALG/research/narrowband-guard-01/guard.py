"""Experimental frequency-concentration guard; no truth, sector or history input."""
import sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'payload/model/python'))
import six_mic_baseline_core as b
import weighted_gcc as weighted
from audio_frames import to_six_mic_baseline
from six_mic_localize import solve_delays

def concentration(samples):
    """Median across 15 pairs of largest-three-bin cross-amplitude fraction."""
    x=np.fft.rfft(samples*np.hanning(b.N),axis=1)
    f=np.fft.rfftfreq(b.N,1/b.FS);band=(f>=b.BAND[0])&(f<=b.BAND[1]);values=[]
    for i,j in b.PAIRS:
        amp=np.abs(x[i]*x[j].conj())[band]
        values.append(float(np.sort(amp)[-3:].sum()/max(float(amp.sum()),1e-15)))
    return float(np.median(values))

def capped_gcc(samples):
    x=np.fft.rfft(samples*np.hanning(b.N),axis=1);f=np.fft.rfftfreq(b.N,1/b.FS)
    band=(f>=b.BAND[0])&(f<=b.BAND[1]);delays=[]
    for i,j in b.PAIRS:
        cross=x[i]*x[j].conj();amp=np.abs(cross)
        mask=band&(amp>=.02*max(float(amp[band].max()),1e-15))
        if mask.sum()<12:delays.append(np.nan);continue
        # Keep beta=.75 relative weighting below cap; cap at 1.5 x retained-bin median weight.
        weights=amp**.25;cap=1.5*float(np.median(weights[mask]))
        spectrum=np.where(mask,cross/np.maximum(amp,1e-15)*np.minimum(weights,cap),0)
        corr=np.fft.irfft(spectrum,n=b.N)
        bound=np.linalg.norm(b.POS[i]-b.POS[j])/b.C*b.FS
        lags=np.arange(-int(np.ceil(bound)),int(np.ceil(bound))+1)
        peak=int(lags[np.argmax(corr[lags%b.N])]);ym,y0,yp=corr[(peak-1)%b.N],corr[peak%b.N],corr[(peak+1)%b.N]
        denom=ym-2*y0+yp;delta=np.clip(.5*(ym-yp)/denom,-.5,.5) if denom < -1e-15 else 0.
        tau=peak+delta;delays.append(tau if abs(tau)<=bound+.05 else np.nan)
    return np.array(delays)

def localize(frame,method):
    if method not in ['fallback035','cap150']:raise ValueError('unknown guard')
    samples=to_six_mic_baseline(frame)
    with np.errstate(over='raise',invalid='raise',divide='raise'):
        score=concentration(samples);trigger=method=='fallback035' and score>=.35
        delays=weighted.gcc(samples,1 if trigger else .75) if method=='fallback035' else capped_gcc(samples)
        result=solve_delays(delays)
    return frame.summary()|result|dict(angular_error_deg=None,guard_score=score,guard_trigger=bool(trigger))
