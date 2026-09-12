"""Frozen amplitude/configuration scan; imports the unchanged chain."""
import argparse
import ctypes as C
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import platform
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'integration'))
import chain

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj): p.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf-8')

class Forward:
    def __init__(self,engine,config):
        self.engine=engine;self.width=config['width'];self.shifts=config['shifts']
        self.state=engine.create(chain.abi.Generics(10,2,0,0,self.width,24,1,0,1,1,0))
        assert self.state
    def run(self,win):
        outputs=[];flags=[]
        for channel in win:
            codes=channel*(1<<(self.width-25))
            assert np.all(codes>=-(1<<(self.width-1))) and np.all(codes<(1<<(self.width-1)))
            re=(C.c_double*1024)(*[int(v)/2**(self.width-1) for v in codes])
            im=(C.c_double*1024)();ro=(C.c_double*1024)();io=(C.c_double*1024)()
            shifts=(C.c_int*10)(*self.shifts)
            out=chain.abi.Outputs(ro,1024,io,1024,0,0)
            assert self.engine.sim(self.state,chain.abi.Inputs(10,re,1024,im,1024,shifts,10,1),C.byref(out))==0
            assert out.xk_re_size==out.xk_im_size==1024
            raw=np.column_stack((ro,io))*2**(self.width-1)
            assert np.all(raw==np.rint(raw))
            outputs.append(raw.astype(np.int64));flags.append(bool(out.overflow))
        raw=np.array(outputs);shift=0;packed=raw.copy()
        while np.any(packed< -2**24) or np.any(packed>=2**24):
            shift+=1
            packed=np.array([chain.phat.rne_shift(int(v),shift) for v in raw.flat],dtype=np.int64).reshape(raw.shape)
        # Epsilon is transformed with the FFT scale and the shared exponent.
        exponent=2*(self.width-2-shift-sum(self.shifts))
        epsilon=Fraction(1,10**15)*Fraction(2)**exponent
        assert 0<epsilon<1 # permits the existing explicit zero/nonzero PHAT path
        return raw,packed,flags,shift,str(epsilon)
    def close(self): self.engine.destroy(self.state)

class Replay:
    """Reuse the original entire downstream chain with precomputed forward outputs."""
    def __init__(self,engine,packed,flags):
        self.engine=engine;self.packed=packed;self.flags=flags;self.index=0
    def transform(self,codes,forward):
        if not forward:return self.engine.transform(codes,False)
        k=self.index;self.index+=1
        return self.packed[k],self.flags[k]

def compare(ref,actual):
    result=[]
    for a,b in zip(ref,actual,strict=True):
        both=a['valid'] and b['valid']
        result.append(dict(valid_changed=a['valid']!=b['valid'],
            newly_valid=(not a['valid']) and b['valid'],lost_valid=a['valid'] and not b['valid'],
            mask_changed=sum(x!=y for x,y in zip(a['mask'],b['mask'],strict=True)),
            peak_changed=(a['peak']!=b['peak']) if both else None,
            delta=(b['tau_samples']-a['tau_samples']) if both else None))
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dll',type=Path,required=True)
    ap.add_argument('--dependency-dir',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    assert sha(args.dll)=='79ec8ccc56cd56c4277a3c8c46ed0fca8435f6e62107854414b1672eda5575ca'
    protocol=json.loads((HERE/'protocol.json').read_text())
    engine=chain.FFT(args.dll,args.dependency_dir)
    candidates={k:Forward(engine,v) for k,v in protocol['candidates'].items()}
    records=[];input_files=[];case=0
    def run(frame,meta):
        nonlocal case
        ref,_,_=chain.floating(frame)
        pcm=np.clip(np.rint(frame*2**23),-2**23,2**23-1).astype(np.int64)
        pcmref,_,_=chain.floating(pcm/2**23)
        win=np.array([[chain.window.window_sample(int(v),c)[0] for v,c in zip(row,chain.COEFFICIENTS)] for row in pcm])
        # Float FFT after integer window isolates loss already introduced before FFT.
        spectrum=np.fft.rfft(win/2**23,axis=1)
        win_masks=[]
        for i,j in chain.baseline.PAIRS:
            amp=abs(spectrum[i]*spectrum[j].conj())
            win_masks.append((np.array(chain.BAND)&(amp>=.02*max(float(amp[chain.BAND].max()),1e-15))).tolist())
        name=f'case-{case:03d}.npz';stored=dict(input_float=frame,pcm=pcm,windowed=win)
        entry=dict(case=case,**meta,npz=name,float_pairs=ref,pcm_float_pairs=pcmref,
            integer_window_float_masks=win_masks,pcm_peak=int(abs(pcm).max()),window_peak=int(abs(win).max()),candidates={})
        for key,candidate in candidates.items():
            raw,packed,flags,shift,eps=candidate.run(win)
            replay=Replay(engine,packed,flags)
            pairs,_,arrays,chainflags=chain.fixed(frame,replay)
            assert replay.index==6 and np.array_equal(arrays['windowed'],win)
            if any(flags):assert all(not p['valid'] for p in pairs)
            if key=='reference25' and case==0:
                direct=chain.fixed(frame,engine)
                assert direct[0]==pairs
                for k in arrays:assert np.array_equal(arrays[k],direct[2][k])
            # Preserve stage arrays for reproducible numerical review, shared input once.
            for k,v in dict(raw_fft=raw,packed_fft=packed,phat=arrays['phat_codes'],ifft=arrays['ifft_codes']).items():
                stored[key+'_'+k]=v
            entry['candidates'][key]=dict(pairs=pairs,vs_float=compare(ref,pairs),vs_pcm=compare(pcmref,pairs),
                flags=chainflags,common_right_shift=shift,epsilon_codes=eps,
                raw_fft_peak=int(abs(raw).max()),band_nonzero_components=int(np.count_nonzero(raw[:,7:86])),
                max_imaginary_residual=int(abs(arrays['ifft_codes'][:,:,1]).max()))
        np.savez_compressed(args.out/name,**stored);entry['npz_sha256']=sha(args.out/name)
        records.append(entry);input_files.append(name);case+=1
    try:
        for seed in protocol['seeds']:
            for az,el in protocol['directions']:
                rng=np.random.default_rng(seed)
                target=chain.baseline.render(chain.baseline.source(rng),chain.baseline.unit(az,el))
                noise=rng.normal(size=target.shape)
                noise*=np.sqrt(np.mean(target**2)/np.mean(noise**2))
                for scenario in protocol['scenarios']:
                    frame=(target+(noise if scenario=='noise0' else 0))[:,1536:2560]
                    frame=frame/np.max(abs(frame))
                    for exponent in protocol['peak_exponents']:
                        run(frame*2.**(-exponent),dict(seed=seed,az=az,el=el,scenario=scenario,peak_exponent=exponent))
                print(f'Completed seed={seed} az={az} frames={case}',flush=True)
        t=np.arange(1024)
        for scenario in protocol['stress']:
            mono={'zero':np.zeros(1024),'dc095':np.ones(1024)*.95,
                  'alternating095':np.where(t%2,.95,-.95),'tone900_095':.95*np.sin(2*np.pi*900*t/48000)}[scenario]
            run(np.tile(mono,(6,1)),dict(seed=None,az=None,el=None,scenario=scenario,peak_exponent=None))
    finally:
        for candidate in candidates.values():candidate.close()
        engine.close()
    write(args.out/'frames.json',records)
    groups=[]
    for key in candidates:
        for exponent in protocol['peak_exponents']+[None]:
            selected=[r for r in records if r['peak_exponent']==exponent]
            d=[p for r in selected for p in r['candidates'][key]['vs_float']]
            dp=[p for r in selected for p in r['candidates'][key]['vs_pcm']]
            deltas=[abs(p['delta']) for p in d if p['delta'] is not None]
            groups.append(dict(candidate=key,peak_exponent=exponent,frames=len(selected),pairs=len(d),
                float_valid=sum(p['valid'] for r in selected for p in r['float_pairs']),
                fixed_valid=sum(p['valid'] for r in selected for p in r['candidates'][key]['pairs']),
                lost_valid=sum(p['lost_valid'] for p in d),newly_valid=sum(p['newly_valid'] for p in d),
                valid_changes_vs_pcm=sum(p['valid_changed'] for p in dp),
                mask_changed=sum(p['mask_changed'] for p in d),peak_changed=sum(p['peak_changed'] is True for p in d),
                max_tau_delta=max(deltas,default=None),
                overflow_frames=sum(any(r['candidates'][key]['flags']['fft_overflow']) for r in selected)))
    sources=[Path(__file__),HERE/'protocol.json',HERE.parent/'integration/chain.py',HERE.parent/'phat_model.py',
        chain.TASKS/'fft-window-02/window_model.py',chain.TASKS/'fft-bitexact-01/compare_cmodel.py',
        chain.PACKAGE/'payload/model/python/six_mic_baseline_core.py']
    write(args.out/'summary.json',dict(status='COMPLETED_CMODEL_RESEARCH_NOT_ACCEPTANCE',frames=case,
        comparisons=case*len(candidates),groups=groups,python=sys.version,numpy=np.__version__,platform=platform.platform(),
        sources={str(p):sha(p) for p in sources},model_sha256=sha(args.dll),
        dependencies={p.name:sha(p) for p in args.dependency_dir.glob('*.dll')}))
    print(f'Completed {case} frames / {case*len(candidates)} configuration comparisons',flush=True)

if __name__=='__main__':main()
