"""Research generalized GCC: exponent-only change to the original PHAT baseline."""
import math
import numpy as np
import six_mic_baseline_core as b
from audio_frames import to_six_mic_baseline
from six_mic_localize import solve_delays


def gcc(frame,beta=0.75):
    if type(beta) not in (int,float) or not math.isfinite(beta) or not 0<beta<=1:
        raise ValueError('beta must be finite in (0,1], not bool')
    frame=np.asarray(frame)
    if frame.shape!=(6,1024) or frame.dtype.kind!='f' or not np.isfinite(frame).all():
        raise ValueError('expected finite floating 6x1024 frame')
    x=np.fft.rfft(frame*np.hanning(b.N)[None,:],axis=1)
    frequencies=np.fft.rfftfreq(b.N,1/b.FS)
    band=(frequencies>=b.BAND[0])&(frequencies<=b.BAND[1]);estimates=[]
    for i,j in b.PAIRS:
        cross=x[i]*x[j].conj();amp=np.abs(cross)
        mask=band&(amp>=.02*max(float(amp[band].max()),1e-15))
        if mask.sum()<12:estimates.append(np.nan);continue
        # beta=1 reproduces PHAT; beta<1 leaves amplitude^(1-beta) weighting.
        denominator=np.maximum(amp,1e-15)
        if beta!=1:denominator=denominator**beta
        spectrum=np.where(mask,cross/denominator,0)
        corr=np.fft.irfft(spectrum,n=b.N)
        bound=np.linalg.norm(b.POS[i]-b.POS[j])/b.C*b.FS
        lim=int(np.ceil(bound));lags=np.arange(-lim,lim+1)
        peak=int(lags[np.argmax(corr[lags%b.N])])
        ym,y0,yp=corr[(peak-1)%b.N],corr[peak%b.N],corr[(peak+1)%b.N]
        denom=ym-2*y0+yp
        delta=np.clip(.5*(ym-yp)/denom,-.5,.5) if denom < -1e-15 else 0.
        tau=peak+delta
        estimates.append(tau if abs(tau)<=bound+.05 else np.nan)
    return np.array(estimates)


def localize(frame,beta):
    try:
        with np.errstate(over='raise',invalid='raise',divide='raise'):
            result=solve_delays(gcc(to_six_mic_baseline(frame),beta))
    except (FloatingPointError,np.linalg.LinAlgError) as error:
        raise ValueError('numerical failure in weighted GCC') from error
    return frame.summary()|result|dict(angular_error_deg=None)
