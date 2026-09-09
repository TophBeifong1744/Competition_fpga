"""Measure removed estimator-spectrum contribution, not semantic target information."""
from pathlib import Path
import importlib.util,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'payload/model/python'))
import six_mic_baseline_core as b
from audio_frames import to_six_mic_baseline
spec=importlib.util.spec_from_file_location('frozen_loo_features',ROOT/'research/leave-band-out-01/features.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)

def impacts(frame,bands):
    x=np.fft.rfft(to_six_mic_baseline(frame)*np.hanning(b.N),axis=1);f=np.fft.rfftfreq(b.N,1/b.FS)
    full=(f>=300)&(f<=4000);result=[dict(removed_bins=[],removed_mass_fraction=[],removed_f2_fraction=[]) for _ in bands]
    for i,j in b.PAIRS:
        z=x[i]*x[j].conj();amp=np.abs(z);mask=full&(amp>=.02*max(float(amp[full].max()),1e-15))
        weights=amp**.25;cap=1.5*float(np.median(weights[mask])) if mask.any() else 0.
        magnitude=np.abs(np.where(mask,z/np.maximum(amp,1e-15)*np.minimum(weights,cap),0))
        total=float(magnitude.sum());f2total=float((magnitude*f*f).sum())
        for k,(lo,hi) in enumerate(bands):
            removed=mask&(f>=lo)&((f<=hi) if k==len(bands)-1 else (f<hi))
            result[k]['removed_bins'].append(int(removed.sum()))
            result[k]['removed_mass_fraction'].append(float(magnitude[removed].sum()/total) if total else 0.)
            result[k]['removed_f2_fraction'].append(float((magnitude[removed]*f[removed]**2).sum()/f2total) if f2total else 0.)
    return result

def assess(full,deleted,impact,config,loo_config):
    statuses=[];eligible=[];qualified_counts=[]
    tau=np.array([np.nan if t is None else t for t in full['pair_delays_samples']])
    for k,(r,m) in enumerate(zip(deleted,impact)):
        count=np.array(m['removed_bins']);fraction=np.array(m['removed_mass_fraction'])
        other=np.array([np.nan if t is None else t for t in r['pair_delays_samples']]);common=np.isfinite(tau)&np.isfinite(other)
        qualified=common&(count>=config['minimum_removed_bins'])&(fraction>=config['minimum_removed_mass'])&(fraction<=config['maximum_removed_mass'])
        n=int(qualified.sum());qualified_counts.append(n)
        if not full['valid']:status='full_rejected'
        elif not np.any(count):status='no_change'
        elif not r['valid'] or common.sum()<loo_config['minimum_joint_pairs_per_deletion']:status='uncomparable'
        elif n<config['minimum_qualified_pairs']:status='weak_or_excessive'
        else:status='effective';eligible.append(k)
        statuses.append(status)
    selected=[r if k in eligible else r|dict(valid=False) for k,r in enumerate(deleted)]
    diagnostic=old.assess(full,selected,loo_config)
    return diagnostic|dict(impact_statuses=statuses,qualified_pair_counts=qualified_counts)

screen=old.screen
