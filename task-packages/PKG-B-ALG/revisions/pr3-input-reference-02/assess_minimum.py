"""Compare native generation to exact-hash-validated RIR reconstruction.

Numerical differences are descriptive, never an alternative acceptance policy.
"""
import argparse
from pathlib import Path
import numpy as np
import reference_inputs as r

def errors(a,b):
    d=np.asarray(a)-np.asarray(b);scale=float(np.max(np.abs(b)))
    return dict(max_abs=float(np.max(np.abs(d))),rms=float(np.sqrt(np.mean(d*d))),relative_l2=float(np.linalg.norm(d)/np.linalg.norm(b)),
        max_abs_over_reference_peak=float(np.max(np.abs(d))/scale),nonidentical_values=int(np.count_nonzero(a!=b)),
        canonical_array_bytes_equal=r.s.array_hash(a)==r.s.array_hash(b))

def main(out):
    out.mkdir(parents=True,exist_ok=False);r.write(out/'environment.json',r.common.environment())
    refs=r.References();native=r.s.make_rir;results=[]
    wanted=[('tone900__front__early_late',2026091500),('tone1200__front__early_late',2026091700),('band__az32__early_late',2026091700)]
    for condition,seed in wanted:
        row=next(x for x in refs.index['coverage'] if (r.historical(x)['condition'],r.historical(x)['seed'])==(condition,seed))
        m=r.historical(row);plan=row['plan']
        r.s.make_rir=native
        a,am=r.study.generate(plan,m['noise'],m['direction'],m['room'],seed)
        ar,_=native(plan,m['direction'],m['room'],seed)
        refs.install()
        b,bm=r.study.generate(plan,m['noise'],m['direction'],m['room'],seed)
        r.common.DIFF.input(m,bm) # Only a verified historical reference is used below.
        br,_=refs.make_rir(plan,m['direction'],m['room'],seed)
        results.append(dict(condition=condition,seed=seed,native_hashes={k:dict(historical=m[k],native=am[k],equal=m[k]==am[k]) for k in ['input_sha256','target_sha256','noise_sha256','rir_sha256']},
            reference_four_hashes_exact=True,waveform_error=errors(a.samples,b.samples),rir_error=errors(ar,br)))
    r.write(out/'assessment.json',dict(status='PASS_REFERENCE_EXACT',cases=results,
        interpretation='This CPU with recorded dispatch settings only, not A Intel hardware. Native mismatches remain mismatches. No numerical tolerance used for input acceptance.',
        file_bytes='Reference NPZ container SHA and canonical little-endian float64 array SHA checked separately in References; generated waveforms are memory arrays, not preexisting files.'))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);main(p.parse_args().out.resolve())
