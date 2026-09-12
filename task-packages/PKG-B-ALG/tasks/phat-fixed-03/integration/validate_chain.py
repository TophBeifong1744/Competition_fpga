"""Run the frozen experiment list; report differences without hiding failures."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import numpy as np
import chain

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def direction(tau):
    u,valid,residual,norm=chain.baseline.solve(tau)
    return dict(valid=bool(valid),unit=u.tolist() if valid else None,
        residual=float(residual) if np.isfinite(residual) else None,
        norm=float(norm) if np.isfinite(norm) else None,
        implementation='unchanged_float_LS_diagnostic_not_fixed_geometry')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--dll',type=Path,required=True)
    parser.add_argument('--dependency-dir',type=Path,required=True)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    protocol=json.loads((HERE/'protocol.json').read_text())
    assert sha(args.dll)=='79ec8ccc56cd56c4277a3c8c46ed0fca8435f6e62107854414b1672eda5575ca','Different model binary; explicit revalidation required'
    # Deterministic interpolation and sign tests on exact correlation codes.
    for lag in (-3,0,3):
        corr=np.zeros(1024,dtype=np.int64);corr[lag%1024]=100
        assert chain.peak(corr,8,True)['tau_q12']==lag*4096
    corr=np.zeros(1024,dtype=np.int64);corr[0]=10;corr[-1]=7;corr[1]=9
    assert chain.peak(corr,8,True)['tau_q12']==1024 # +1/4 sample
    corr=np.zeros(1024,dtype=np.int64);corr[-2]=corr[2]=100
    assert chain.peak(corr,8,True)['peak']==-2
    engine=chain.FFT(args.dll,args.dependency_dir)
    records=[];filenames=[];case=0
    try:
        for seed in protocol['seeds']:
            for az,el in protocol['directions_degrees']:
                rng=np.random.default_rng(seed)
                broadband=chain.baseline.source(rng)
                target=chain.baseline.render(broadband,chain.baseline.unit(az,el))
                for scenario in protocol['scenarios']:
                    samples=target.copy()
                    if scenario=='noise0':
                        noise=rng.normal(size=samples.shape)
                        noise*=np.sqrt(np.mean(samples*samples))/np.sqrt(np.mean(noise*noise))
                        samples+=noise
                    elif scenario=='tone900':
                        tone=np.sin(2*np.pi*900*np.arange(chain.baseline.L)/48000)
                        samples=chain.baseline.render(tone,chain.baseline.unit(az,el))
                    elif scenario=='missing_channel':samples[4]=0
                    elif scenario=='zero':samples[:]=0
                    frame=samples[:,1536:2560]
                    peak=float(np.max(abs(frame)))
                    peak_target=protocol['weak_common_peak_target'] if scenario=='weak' else protocol['common_peak_target']
                    gain=peak_target/peak if peak else 1.
                    frame=frame*gain # One explicit common test gain, never channel-wise.
                    ref,refcorr,reftau=chain.floating(frame)
                    fixed,tau,arrays,flags=chain.fixed(frame,engine)
                    pcm_ref,pcm_corr,pcm_tau=chain.floating(arrays['pcm']/2**23)
                    diff=[]
                    for k,(a,b,p) in enumerate(zip(ref,fixed,pcm_ref)):
                        both=a['valid'] and b['valid']
                        delta=(b['tau_samples']-a['tau_samples']) if both else None
                        diff.append(dict(pair=list(chain.baseline.PAIRS[k]),
                            mask_changed_bins=sum(x!=y for x,y in zip(a['mask'],b['mask'])),
                            mask_changed_vs_pcm_float=sum(x!=y for x,y in zip(p['mask'],b['mask'])),
                            valid_changed=a['valid']!=b['valid'], valid_changed_vs_pcm_float=p['valid']!=b['valid'],
                            peak_changed=(a.get('peak')!=b.get('peak')) if both else None,
                            tau_delta_samples=delta,
                            tau_delta_vs_pcm_float=(b['tau_samples']-p['tau_samples']) if p['valid'] and b['valid'] else None,
                            float_pair=a,fixed_pair=b,pcm_float_pair=p))
                    fixed_direction=direction(tau);ref_direction=direction(reftau)
                    angle=None
                    if fixed_direction['valid'] and ref_direction['valid']:
                        angle=chain.baseline.angle(np.array(fixed_direction['unit']),np.array(ref_direction['unit']))
                    name=f'case-{case:03d}.npz';np.savez_compressed(args.out/name,input_float=frame,
                        float_correlation=refcorr,pcm_float_correlation=pcm_corr,**arrays)
                    filenames.append(name)
                    records.append(dict(case=case,seed=seed,az=az,el=el,scenario=scenario,
                        common_gain=gain,npz=name,npz_sha256=sha(args.out/name),flags=flags,
                        pairs=diff,float_direction=ref_direction,fixed_tau_float_direction=fixed_direction,
                        direction_difference_degrees=angle,
                        ifft_imaginary_residual_max_codes=int(np.max(abs(arrays['ifft_codes'][:,:,1])))))
                    case+=1
        # Fault injection checks propagation, not that hardware overflow was induced.
        fault_frame=np.zeros((6,1024))
        pairs,taus,arrays,flags=chain.fixed(fault_frame,engine,True)
        assert all(not p['valid'] and p['reason']=='UPSTREAM_IP_OVERFLOW' for p in pairs)
        assert np.all(np.isnan(taus))
        # Application +1 endpoint saturates to signed24 positive maximum.
        _,_,arrays,flags=chain.fixed(np.ones((6,1024)),engine)
        assert flags['input_saturation']==6144 and np.all(arrays['pcm']==2**23-1)
    finally:engine.close()
    scenario_stats={}
    for scenario in protocol['scenarios']:
        selected=[r for r in records if r['scenario']==scenario]
        pairs=[p for r in selected for p in r['pairs']]
        deltas=[abs(p['tau_delta_samples']) for p in pairs if p['tau_delta_samples'] is not None]
        angles=[r['direction_difference_degrees'] for r in selected if r['direction_difference_degrees'] is not None]
        scenario_stats[scenario]=dict(frames=len(selected),pairs=len(pairs),
            float_valid_pairs=sum(p['float_pair']['valid'] for p in pairs),fixed_valid_pairs=sum(p['fixed_pair']['valid'] for p in pairs),
            valid_changes=sum(p['valid_changed'] for p in pairs),mask_changed_bins=sum(p['mask_changed_bins'] for p in pairs),
            mask_changed_vs_pcm_float=sum(p['mask_changed_vs_pcm_float'] for p in pairs),
            peak_changes=sum(p['peak_changed'] is True for p in pairs),
            max_abs_tau_delta_samples=max(deltas,default=None),
            float_valid_directions=sum(r['float_direction']['valid'] for r in selected),
            fixed_tau_float_valid_directions=sum(r['fixed_tau_float_direction']['valid'] for r in selected),
            max_direction_difference_degrees=max(angles,default=None))
    source_paths=[HERE/'chain.py',Path(__file__),HERE/'protocol.json',
        chain.PACKAGE/'payload/model/python/six_mic_baseline_core.py',HERE.parent/'phat_model.py',
        chain.TASKS/'fft-window-02/window_model.py',chain.TASKS/'fft-bitexact-01/compare_cmodel.py']
    summary=dict(status='COMPLETED_RESEARCH_COMPARISON_NOT_ACCEPTANCE',frames=len(records),pairs=len(records)*15,
        interpolation_sign_checks=5,upstream_invalid_injection_pass=True,positive_one_saturations=6144,
        scenario_stats=scenario_stats,
        model_dll_sha256=sha(args.dll),source_sha256={str(p):sha(p) for p in source_paths},
        dependencies={p.name:sha(p) for p in args.dependency_dir.glob('*.dll')},
        python=sys.version,numpy=np.__version__,platform=platform.platform(),
        limitations=['No new XSim for this combined chain','PHAT/window/interpolation are Python integer models',
            'Geometry bounds and LS remain float; tracker and audio not run',
            'Positive-one and forced-invalid are software tests, not induced IP overflow recovery',
            'Synthetic six-mic study only; shared test gain is not frozen acquisition gain'])
    (args.out/'frames.json').write_text(json.dumps(records,indent=2,allow_nan=False)+'\n')
    (args.out/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(status=summary['status'],frames=case,scenario_stats=scenario_stats),indent=2))

if __name__=='__main__':main()
