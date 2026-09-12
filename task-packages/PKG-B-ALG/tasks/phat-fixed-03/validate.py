"""Boundary and fresh-seed tests. This is software arithmetic, not PHAT RTL."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import random
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
import numpy as np
from phat_model import *

HERE=Path(__file__).resolve().parent

def oracle(z):
    with localcontext() as ctx:
        ctx.prec=90
        r,i=map(Decimal,z)
        magnitude=(r*r+i*i).sqrt()
        return tuple(int((v/magnitude*2**23).to_integral_value(rounding=ROUND_HALF_EVEN)) for v in (r,i))

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seed-offset',type=int,default=0);args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    assert 0<EPSILON_CODES<1
    tested=0
    for n in range(-1500,1501):
        assert rne_ratio(n,128)==round(Fraction(n,128));tested+=1
    zs=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,-1), (3,4), (49,1), (50,0)]
    for e in range(1,50):
        zs += [(2**e-1,1),(2**e,2**e-1),(-2**e,2**e-1)]
    rng=random.Random(2026091301+args.seed_offset)
    zs += [(rng.randrange(-2**49,2**49),rng.randrange(-2**49,2**49)) for _ in range(4096)]
    max_error=0;worst=None;max_recip_difference=0;max_old_error=0
    for z in zs:
        actual,info=normalize(z);expected=oracle(z)
        error=max(abs(a-b) for a,b in zip(actual,expected))
        direct=tuple(rne_ratio(v<<(23+MAG_FRAC),info['magnitude_code']) for v in z)
        old,_=normalize(z,16)
        max_old_error=max(max_old_error,max(abs(a-b) for a,b in zip(old,expected)))
        max_recip_difference=max(max_recip_difference,max(abs(a-b) for a,b in zip(actual,direct)))
        if error>max_error:max_error=error;worst=dict(input=z,actual=actual,oracle=expected)
    # Finite regression envelope, not a project acceptance threshold.
    assert max_error<=2,(max_error,worst)
    assert max_recip_difference<=2,max_recip_difference
    assert normalize((0,0))[1]['valid'] is False
    boundary_masks=[mask_for([(100,0),(2,0),(1,0),(0,0)],[True]*4),
                    mask_for([(50,0),(1,0),(0,0)],[True]*3)]
    assert boundary_masks==[[True,True,False,False],[True,True,False]]
    band=[7<=k<=85 for k in range(513)]
    zeros=[(0,0)]*513
    for count in (0,11,12):
        a=zeros.copy();b=zeros.copy()
        for k in range(7,7+count):a[k]=b[k]=(1,0)
        res=phat_pair(a,b,band)
        assert res['valid']==(count>=12)
    assert phat_pair(a,b,band,True)['reason']=='UPSTREAM_IP_OVERFLOW'
    trials=[];mask_mismatch=0;pair_mismatch=0;maximum_code_error=0
    # New spectra across large/small code magnitudes, including quantized zeros.
    for trial in range(96):
        rng=random.Random(2026091400+trial+args.seed_offset)
        limit=2**(trial%23)
        a=[(rng.randrange(-limit,limit),rng.randrange(-limit,limit)) for _ in range(513)]
        b=[(rng.randrange(-limit,limit),rng.randrange(-limit,limit)) for _ in range(513)]
        res=phat_pair(a,b,band)
        z=np.array([complex(*cross(x,y)) for x,y in zip(a,b)])
        amp=np.abs(z);bm=np.array(band)
        mask=bm & (amp>=.02*max(float(amp[bm].max()),float(EPSILON_CODES)))
        valid=int(mask.sum())>=12
        mask_mismatch+=int(np.count_nonzero(mask!=res['mask']))
        pair_mismatch+=int(valid!=res['valid'])
        err=0
        if valid:
            reference=np.where(mask,z/np.maximum(amp,float(EPSILON_CODES)),0)
            actual=np.array([complex(*v) for v in res['output']])
            err=float(max(max(abs(actual.real-reference.real*2**23)),max(abs(actual.imag-reference.imag*2**23))))
            maximum_code_error=max(maximum_code_error,err)
        trials.append(dict(seed=2026091400+trial+args.seed_offset,input_limit_codes=limit,valid=valid,kept_bins=sum(res['mask']),max_component_error_codes=err))
    assert mask_mismatch==pair_mismatch==0
    # Show loss before PHAT: valid floating spectra disappear at one FFT-code rounding.
    a=np.zeros(513,dtype=complex);b=a.copy();a[7:86]=.25;b[7:86]=.25
    amp=np.abs(a*np.conj(b));floating_mask=np.array(band)&(amp>=.02*max(float(amp[band].max()),float(EPSILON_CODES)))
    assert floating_mask.sum()==79 and not phat_pair(zeros,zeros,band)['valid']
    result=dict(status='PASS_SOFTWARE_PHAT_CANDIDATE_NOT_RTL_OR_ALGORITHM_ACCEPTANCE',
        epsilon_cross_codes=str(EPSILON_CODES),epsilon_cross_codes_float=float(EPSILON_CODES),
        seed_offset=args.seed_offset,normalization_seed=2026091301+args.seed_offset,
        magnitude_fraction_bits=MAG_FRAC,paired_mag16_max_error_codes=max_old_error,
        rounding_checks=tested,normalization_vectors=len(zs),max_error_vs_decimal_rounded_codes=max_error,
        worst_normalization=worst,max_recip_error_vs_direct_division_codes=max_recip_difference,
        mask_mismatch_bins=mask_mismatch,pair_validity_mismatches=pair_mismatch,
        max_pair_component_error_codes=maximum_code_error,trials=trials,
        prequantization_counterexample=dict(float_valid_bins=79,quantized_valid_bins=0,recoverable_by_epsilon=False),
        environment=dict(python=platform.python_version(),numpy=np.__version__,platform=platform.platform()),
        source_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'phat_model.py',Path(__file__)]})
    (args.out/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('trials','source_hashes','environment')},indent=2))

if __name__=='__main__':main()
