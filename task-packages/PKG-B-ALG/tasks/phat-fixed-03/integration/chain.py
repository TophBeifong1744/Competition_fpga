"""Candidate integer window -> AMD FFT -> PHAT -> AMD IFFT -> Q12 TDOA."""
import ctypes as C
import importlib.util
import os
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
TASKS=HERE.parents[1]
PACKAGE=TASKS.parent

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod)
    return mod

phat=module('chain_phat',HERE.parent/'phat_model.py')
window=module('chain_window',TASKS/'fft-window-02/window_model.py')
abi=module('chain_fft_abi',TASKS/'fft-bitexact-01/compare_cmodel.py')
baseline=module('chain_original_baseline',PACKAGE/'payload/model/python/six_mic_baseline_core.py')
BAND=[7<=k<=85 for k in range(513)]
COEFFICIENTS=[round(float(x)*2**17) for x in np.hanning(1024)]

class FFT:
    def __init__(self,dll_path,dependencies):
        self.handles=[os.add_dll_directory(str(Path(p).resolve())) for p in [Path(dll_path).parent,dependencies]]
        self.dll=C.CDLL(str(Path(dll_path).resolve()))
        self.create=self.dll.xilinx_ip_xfft_v9_1_create_state
        self.create.argtypes=[abi.Generics];self.create.restype=C.c_void_p
        self.sim=self.dll.xilinx_ip_xfft_v9_1_bitacc_simulate
        self.sim.argtypes=[C.c_void_p,abi.Inputs,C.POINTER(abi.Outputs)];self.sim.restype=C.c_int
        self.destroy=self.dll.xilinx_ip_xfft_v9_1_destroy_state
        self.destroy.argtypes=[C.c_void_p];self.destroy.restype=None
        self.state=self.create(abi.Generics(10,2,0,0,25,24,1,0,1,1,0))
        if not self.state:raise RuntimeError('FFT allocation failed')

    def transform(self,codes,forward):
        values=np.asarray(codes)
        if values.shape!=(1024,2) or not np.issubdtype(values.dtype,np.integer):raise ValueError('integer 1024x2 required')
        if np.any(values < -2**24) or np.any(values>=2**24):raise ValueError('signed25 input overflow')
        re=(C.c_double*1024)(*[int(v)/2**24 for v in values[:,0]])
        im=(C.c_double*1024)(*[int(v)/2**24 for v in values[:,1]])
        ro,io=(C.c_double*1024)(),(C.c_double*1024)();shifts=(C.c_int*10)(*([1]*10))
        result=abi.Outputs(ro,1024,io,1024,0,0)
        if self.sim(self.state,abi.Inputs(10,re,1024,im,1024,shifts,10,int(forward)),C.byref(result)):
            raise RuntimeError('FFT model failed')
        assert result.xk_re_size==result.xk_im_size==1024
        raw=np.column_stack((ro,io))*2**24
        assert np.all(raw==np.rint(raw))
        return raw.astype(np.int64),bool(result.overflow)

    def close(self):
        self.destroy(self.state)
        for h in self.handles:h.close()

def peak(corr,bound,integer):
    bound=float(bound)
    lim=int(np.ceil(bound));lags=list(range(-lim,lim+1))
    lag=max(lags,key=lambda k:corr[k%1024]) # Stable first-max tie rule.
    ym,y0,yp=[corr[k%1024] for k in (lag-1,lag,lag+1)]
    if integer:
        ym,y0,yp=map(int,(ym,y0,yp));denom=ym-2*y0+yp
        # Correlation epsilon=1e-15 * 2^23 <1, so integer denom<0 is equivalent.
        delta=phat.rne_ratio((yp-ym)<<11,-denom) if denom<0 else 0
        delta=max(-2048,min(2048,delta));tau=lag*4096+delta
        return dict(peak=lag,tau_q12=tau,tau_samples=tau/4096,valid=abs(tau/4096)<=bound+.05)
    denom=ym-2*y0+yp
    delta=float(np.clip(.5*(ym-yp)/denom,-.5,.5)) if denom < -1e-15 else 0.
    tau=lag+delta
    return dict(peak=lag,tau_samples=tau,valid=abs(tau)<=bound+.05)

def floating(frame):
    spectra=np.fft.rfft(frame*np.hanning(1024)[None,:],axis=1)
    pairs=[];corrs=np.zeros((15,1024))
    for k,(i,j) in enumerate(baseline.PAIRS):
        z=spectra[i]*spectra[j].conj();amp=np.abs(z)
        mask=np.array(BAND)&(amp>=.02*max(float(amp[BAND].max()),1e-15))
        info=dict(mask=mask.tolist(),valid=False,reason='FEWER_THAN_12_BINS')
        if mask.sum()>=12:
            corrs[k]=np.fft.irfft(np.where(mask,z/np.maximum(amp,1e-15),0),n=1024)
            bound=np.linalg.norm(baseline.POS[i]-baseline.POS[j])/baseline.C*baseline.FS
            info.update(peak(corrs[k],bound,False));info['reason']='VALID' if info['valid'] else 'TAU_BOUND'
        pairs.append(info)
    tau=np.array([p['tau_samples'] if p['valid'] else np.nan for p in pairs])
    np.testing.assert_allclose(tau,baseline.gcc(frame),rtol=0,atol=1e-12,equal_nan=True)
    return pairs,corrs,tau

def fixed(frame,engine,force_upstream_invalid=False):
    raw=np.rint(np.asarray(frame)*2**23)
    if frame.shape!=(6,1024) or not np.all(np.isfinite(raw)):raise ValueError('finite six-mic frame required')
    clipped=np.clip(raw,-2**23,2**23-1);input_saturation=int(np.count_nonzero(raw!=clipped))
    pcm=clipped.astype(np.int64)
    win=np.array([[window.window_sample(int(v),c)[0] for v,c in zip(channel,COEFFICIENTS)] for channel in pcm])
    spectra=[];fft_flags=[]
    for channel in win:
        value,overflow=engine.transform(np.column_stack((channel,np.zeros(1024,dtype=np.int64))),True)
        spectra.append(value[:513]);fft_flags.append(overflow)
    spectra=np.array(spectra)
    # An FFT overflow in any channel invalidates the whole frame, not just one pair.
    upstream=bool(any(fft_flags) or force_upstream_invalid)
    pairs=[];phat_codes=np.zeros((15,513,2),dtype=np.int64);corrs=np.zeros((15,1024,2),dtype=np.int64)
    ifft_flags=[]
    for k,(i,j) in enumerate(baseline.PAIRS):
        a=[tuple(map(int,v)) for v in spectra[i]];b=[tuple(map(int,v)) for v in spectra[j]]
        p=phat.phat_pair(a,b,BAND,upstream)
        info=dict(valid=p['valid'],reason=p['reason'],mask=p['mask'])
        flag=False
        if p['valid']:
            phat_codes[k]=p['output']
            full=np.array(window.conjugate_complete(p['output']),dtype=np.int64)
            corrs[k],flag=engine.transform(full,False)
            if not flag:
                bound=np.linalg.norm(baseline.POS[i]-baseline.POS[j])/baseline.C*baseline.FS
                info.update(peak(corrs[k,:,0],bound,True))
                info['reason']='VALID' if info['valid'] else 'TAU_BOUND'
            else:info.update(valid=False,reason='IFFT_OVERFLOW')
        ifft_flags.append(flag);pairs.append(info)
    if any(ifft_flags):
        for info in pairs:info.update(valid=False,reason='FRAME_IFFT_OVERFLOW')
    tau=np.array([p['tau_samples'] if p['valid'] else np.nan for p in pairs])
    arrays=dict(pcm=pcm,windowed=win,fft_codes=spectra,phat_codes=phat_codes,ifft_codes=corrs)
    return pairs,tau,arrays,dict(input_saturation=input_saturation,fft_overflow=fft_flags,
        ifft_overflow=ifft_flags,forced_invalid=force_upstream_invalid)
