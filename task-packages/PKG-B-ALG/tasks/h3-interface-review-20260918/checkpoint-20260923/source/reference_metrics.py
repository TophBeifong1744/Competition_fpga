"""Fixed-scale component metric. No source-WAV alignment or gain fitting."""
import numpy as np

def component_snr(target_outputs, noise_outputs, mask, *, reference_kind):
    if reference_kind not in ('synthetic_test','array_components_with_receipt'):
        raise ValueError('array component provenance required; playback WAV unsupported')
    if set(target_outputs)!=set(noise_outputs) or 'single' not in target_outputs:
        raise ValueError('same branches and mic0 reference required')
    m=np.asarray(mask)
    if m.dtype!=np.bool_ or m.ndim!=1 or not m.any():raise ValueError('nonempty boolean mask')
    result={}
    for k in target_outputs:
        t=np.asarray(target_outputs[k],dtype=float);n=np.asarray(noise_outputs[k],dtype=float)
        if t.shape!=m.shape or n.shape!=m.shape or not np.isfinite(t).all() or not np.isfinite(n).all():
            raise ValueError('same aligned finite sample clock required')
        et=float(np.sum(t[m]**2));en=float(np.sum(n[m]**2))
        if et<=0 or en<=0:raise ValueError('positive component energy required')
        result[k]=dict(target_energy=et,interference_energy=en,snr_db=float(10*np.log10(et/en)))
    baseline=result['single']['snr_db']
    for row in result.values():row['delta_snr_db_vs_mic0']=row['snr_db']-baseline
    return dict(reference_kind=reference_kind,samples=int(m.sum()),branches=result,
                formal_approval=False,require_same_mixture_derived_control_for_all_components=True)
