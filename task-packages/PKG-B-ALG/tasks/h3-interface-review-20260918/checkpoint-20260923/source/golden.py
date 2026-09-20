"""New per-stage golden on eight real probes; preserves old run05 golden."""
import argparse
import math
import numpy as np
from common import ROOT,BATCH,load,dump,sha,config,new_output
from candidates import features
from integer_gate import stage,fixed,IntegerActivity

def execute(study,out):
    cfg=config();summary=load(study/'summary.json')
    noise=[math.ceil(v) for v in load(study/'calibration.json')['noise_power_codes_squared']]
    phat=fixed._load_phat_model(ROOT)
    reports=[]
    for report in summary['reports']:
        name=report['capture']
        paths=[ROOT/p for p in summary['pins'] if p.endswith('/'+name+'/raw.bin')]
        assert len(paths)==1
        raw=np.fromfile(paths[0],dtype='<u4').reshape(-1,8)[:,2:6].view('<i4').astype(np.int64)
        interval=report['audio']['evaluation_reference_rows']
        start=512*(int(interval[0])//512+1)
        pcm=raw[start:start+1024]
        arrays,detail=stage(pcm)
        fp=np.array(features(pcm)['band_power'])
        detail.update(capture=name,start=start,float_power=fp.tolist(),
            relative_power_difference=((arrays['band_power'].astype(float)-fp)/np.maximum(fp,1)).tolist())
        # Unmodified run05 arithmetic on this new uncentered real frame.
        windowed,wov=fixed.window_pcm(pcm.T)
        sp=[];flags=[]
        for ch in range(4):
            y,f=fixed.fixed_fft([(int(v)<<4,0) for v in windowed[ch]],inverse=False,width=29)
            sp.append(y);flags.append(f)
        sp=np.asarray(sp);half,aov=fixed.adapt_fft29_to_s25(sp[:,:513])
        codes=np.zeros((6,513,2),dtype=np.int64);mask=np.zeros((6,513),dtype=np.uint8)
        correlations=np.zeros((6,1024),dtype=np.int64);lags=[];ifft_flags=[]
        invalid=bool(wov or aov or any(f['overflow_count'] for f in flags))
        for k,(i,j) in enumerate(fixed.PAIRS):
            p=phat.phat_pair(half[i].tolist(),half[j].tolist(),[7<=v<=85 for v in range(513)],ip_overflow=invalid)
            mask[k]=p['mask']
            if not p['valid']:
                lags.append(dict(valid=False,reason=p['reason']));ifft_flags.append(dict(not_run=True));continue
            codes[k]=p['output']
            z,f=fixed.fixed_fft(fixed.conjugate_complete(codes[k]),inverse=True,width=25)
            ifft_flags.append(f);correlations[k]=z[:,0]
            lags.append(fixed.lag_q12(correlations[k],fixed.PAIR_LENGTH_SQ[k]))
        if any(f.get('overflow_count',0) for f in ifft_flags):
            lags=[dict(valid=False,reason='IFFT_OVERFLOW') for _ in lags]
        detail.update(uncentered_fft_flags=flags,ifft_flags=ifft_flags,pairs=lags,doa=fixed.doa_q20(lags))
        arrays.update(doa_windowed=windowed,doa_fft29=sp,doa_fft25=half,phat=codes,mask=mask,ifft=correlations)
        # Explicit manual DUT steering configurations, not a DOA accuracy assertion.
        angle=0 if report['nominal_deg'] is None else report['nominal_deg']
        delays=fixed.delay_q12_from_angle(round(angle*256))
        audio,ainfo=fixed.das_block(pcm.T,delays)
        arrays['manual_das']=audio[8:-8];detail['manual_das']=ainfo
        gate=IntegerActivity(noise,cfg)
        detail['repeated_frame_three_steps']=[gate.update(arrays['band_power'],detail['overflow']) for _ in range(3)]
        detail['repeated_frame_is_synthetic_duration_probe']=True
        np.savez_compressed(out/(name+'.npz'),**arrays)
        detail['arrays']={k:dict(shape=list(v.shape),dtype=str(v.dtype),sha256=__import__('hashlib').sha256(v.tobytes()).hexdigest()) for k,v in arrays.items()}
        reports.append(detail)
    dump(out/'summary.json',dict(status='PORTABLE_INTEGER_CONTRACT_GOLDEN_ONLY',noise_u64=noise,reports=reports,
        amd_bitexact=False,full_float_study_equivalence=False,production_freeze=False))
    dump(out/'SHA256.json',{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()})
    print('PASS_NEW_INTEGER_PROBES',len(reports),sum(len(r['arrays']) for r in reports))

if __name__=='__main__':
    from pathlib import Path
    p=argparse.ArgumentParser();p.add_argument('--study',type=Path,required=True);p.add_argument('--out',required=True)
    a=p.parse_args();execute(a.study,new_output(a.out))
