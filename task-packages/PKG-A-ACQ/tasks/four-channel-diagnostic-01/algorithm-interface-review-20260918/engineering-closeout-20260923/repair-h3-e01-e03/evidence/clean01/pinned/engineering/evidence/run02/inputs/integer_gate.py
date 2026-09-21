"""Executable integer gate contract candidate; portable Q30 FFT, not AMD proof."""
import numpy as np
from common import module,TASKS

fixed=module('checkpoint_fixed',TASKS/'h3-complete-20260918/source/fixed_golden.py')

def stage(pcm):
    x=np.asarray(pcm)
    if x.shape!=(1024,4) or not np.issubdtype(x.dtype,np.integer) or np.any(x < -2**23) or np.any(x >= 2**23):
        raise ValueError('signed24 1024x4 required')
    x=x.astype(np.int64)
    means=np.array([fixed.rne_div(sum(map(int,x[:,ch])),1024) for ch in range(4)],dtype=np.int64)
    centered=x-means
    window=fixed.hann_u18f17()
    weighted=np.array([[fixed.rne_shift(int(v)*int(w),17) for v,w in zip(centered[:,ch],window)] for ch in range(4)],dtype=np.int64)
    spectra=[];flags=[]
    for ch in range(4):
        y,f=fixed.fixed_fft([(int(v)<<4,0) for v in weighted[ch]],inverse=False,width=29)
        spectra.append(y);flags.append(f)
    spectra=np.asarray(spectra)
    half,overflow=fixed.adapt_fft29_to_s25(spectra[:,:513])
    denominator=sum(int(w)**2 for w in window)
    sums=[sum(int(a)**2+int(b)**2 for a,b in half[ch,7:73]) for ch in range(4)]
    numerators=[2*s*1024*(1<<34) for s in sums]
    powers=[fixed.rne_div(n,denominator) for n in numerators]
    assert all(0<=n<2**104 for n in numerators) and all(0<=p<2**64 for p in powers)
    return dict(pcm=x,mean=means,centered=centered,hann=window,windowed=weighted,
                fft29=spectra,fft25=half,band_power=np.array(powers,dtype=np.uint64)), dict(
        sum_power=sums,numerators=numerators,denominator=denominator,
        overflow=bool(overflow or any(f['overflow_count'] for f in flags)),fft_flags=flags,
        semantics='integer spectral activity contract, not bit-exact proof of float study or AMD IP')

class IntegerActivity:
    def __init__(self,noise,cfg):
        if any(int(v)!=v or v<0 or v>=2**64 for v in noise):raise ValueError('U64 noise required')
        if [cfg[k] for k in ['on_power_ratio','off_power_ratio','attack_frames','release_frames','minimum_active_channels']] != [4,2,3,3,3]:
            raise ValueError('unsupported integer contract configuration')
        self.floor=[max(int(v),int(cfg['band_rms_floor_codes'])**2) for v in noise]
        if len(self.floor)!=4 or any(v<0 or v>=2**64 for v in self.floor):raise ValueError('U64 floor')
        self.cfg=cfg;self.reset()
    def reset(self):self.active=False;self.attack=self.release=0
    def update(self,power,invalid=False):
        values=list(power)
        if any(int(v)!=v for v in values):raise ValueError('integer power required')
        p=list(map(int,values))
        if len(p)!=4 or any(v<0 or v>=2**64 for v in p):raise ValueError('U64 power')
        if invalid:self.reset();return False
        on=sum(v>=4*n for v,n in zip(p,self.floor))>=3
        off=sum(v>=2*n for v,n in zip(p,self.floor))<3
        self.attack=min(3,self.attack+1) if on else 0
        self.release=min(3,self.release+1) if off else 0
        if not self.active and self.attack>=3:self.active=True;self.release=0
        elif self.active and self.release>=3:self.active=False;self.attack=0
        return self.active
