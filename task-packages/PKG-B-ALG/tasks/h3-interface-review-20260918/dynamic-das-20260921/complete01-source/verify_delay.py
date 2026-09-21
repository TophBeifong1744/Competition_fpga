"""All Q8 angles: independent Decimal Taylor reference, frozen integer ROM."""
import argparse
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np

PI='3.141592653589793238462643383279502884197169399375105820974944592307816406286208998628034825342117067982148086513282306647'


def quarter(precision):
    with localcontext() as ctx:
        ctx.prec=precision
        values=[]
        for k in range(90*256+1):
            x=Decimal(k)*Decimal(PI)/Decimal(180*256)
            term=x;s=x;n=1
            while abs(term)>Decimal(10)**(-precision+6):
                term *= -x*x/Decimal((2*n)*(2*n+1))
                s+=term;n+=1
            values.append(+s)
        values[0]=Decimal(0);values[-1]=Decimal(1)
        return values


def generate(precision):
    with localcontext() as ctx:
        ctx.prec=precision
        table=quarter(precision);q=90*256
        def sine(k):
            quadrant,r=divmod(k%(4*q),q)
            return (table[r],table[q-r],-table[r],-table[q-r])[quadrant]
        scale=Decimal(1920*4096)/Decimal(343)
        codes=[];min_half=Decimal(1)
        for angle in range(-180*256,180*256):
            sx,sy=sine(angle+q),sine(angle)
            row=[]
            for v in (sx,sx+sy,sy):
                value=v*scale
                rounded=value.to_integral_value(rounding=ROUND_HALF_EVEN)
                min_half=min(min_half,Decimal('0.5')-abs(value-rounded))
                row.append(int(rounded))
            codes.append(row)
        return np.array(codes,dtype='<i2'),str(min_half)


def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    path=a.repo/'task-packages/PKG-B-ALG/tasks/h3-complete-20260918/source/fixed_golden.py'
    spec=importlib.util.spec_from_file_location('fg_delay',path);fg=importlib.util.module_from_spec(spec);sys.modules[spec.name]=fg;spec.loader.exec_module(fg)
    low,margin60=generate(60);high,margin90=generate(90)
    assert np.array_equal(low,high),'precision instability'
    original=np.array([fg.delay_q12_from_angle(k)[1:] for k in range(-46080,46080)],dtype=np.int64)
    delta=original-high.astype(np.int64)
    mismatches=np.argwhere(delta!=0)
    # Preserve discrepancies, do not rewrite old goldens.
    rows=[dict(angle_q8=int(i)-46080,channel=int(j)+1,original=int(original[i,j]),reference=int(high[i,j])) for i,j in mismatches]
    np.save(a.out/'delay-rom-s16.npy',high,allow_pickle=False)
    result=dict(status='AUTHOR_ENUMERATION_COMPLETE',angle_count=92160,delay_codes=276480,precision_checks=[60,90],minimum_half_code_margin_60=margin60,minimum_half_code_margin_90=margin90,old_float_mismatch_count=len(rows),max_abs_difference=int(np.abs(delta).max()),maximum_delay_code=int(np.abs(high.astype(np.int64)).max()),rom_payload_bytes=int(high.nbytes),rom_sha256=hashlib.sha256((a.out/'delay-rom-s16.npy').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),runtime='integer lookup, angle_q8 in [-46080,46079], implicit mic0 delay 0',scope='fixed 40mm square, 48kHz, 343m/s; offline ROM candidate, not hardware layout')
    (a.out/'mismatches.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    (a.out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(result)


if __name__=='__main__':main()
