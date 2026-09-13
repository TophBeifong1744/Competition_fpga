"""Compare a fresh run to committed reference; retain byte and numerical differences."""
import argparse
import json
from pathlib import Path
import numpy as np
import run as model

def compare_value(a, b, path, differences):
    if type(a) is not type(b):
        raise AssertionError(f'type mismatch: {path}')
    if isinstance(a, dict):
        assert a.keys() == b.keys(), path
        for key in a: compare_value(a[key], b[key], path+'/'+key, differences)
    elif isinstance(a, list):
        assert len(a) == len(b), path
        for i,(x,y) in enumerate(zip(a,b)): compare_value(x,y,path+'/'+str(i),differences)
    elif isinstance(a, float):
        if a != b: differences.append(dict(path=path, absolute_error=abs(a-b)))
        assert np.isclose(a,b,rtol=1e-10,atol=1e-10), path
    else:
        assert a == b, path  # All discrete peak, validity, reason and Q12 values exact.

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--candidate',type=Path,required=True)
    ap.add_argument('--reference',type=Path,default=model.HERE/'evidence/run02')
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    if args.out.exists(): raise FileExistsError(args.out)
    rows=[]
    for ref in sorted(args.reference.glob('*-frames.json')):
        other=args.candidate/ref.name
        differences=[]
        compare_value(json.loads(ref.read_text()),json.loads(other.read_text()),ref.name,differences)
        rows.append(dict(file=ref.name,bytes_equal=model.sha(ref)==model.sha(other),float_differences=differences,discrete_equal=True))
    assert len(rows)==2, 'both recordings required'
    for ref in sorted(args.reference.glob('*-stages.npz')):
        other=args.candidate/ref.name
        with np.load(ref,allow_pickle=False) as a,np.load(other,allow_pickle=False) as b:
            assert a.files==b.files
            arrays=[]
            for key in a.files:
                assert a[key].shape==b[key].shape and a[key].dtype==b[key].dtype
                error=float(np.max(np.abs(a[key].astype(float)-b[key].astype(float))))
                if a[key].dtype.kind=='f': np.testing.assert_allclose(a[key],b[key],rtol=1e-10,atol=1e-10)
                else: np.testing.assert_array_equal(a[key],b[key])
                arrays.append(dict(key=key,max_absolute_error=error,exact=bool(np.array_equal(a[key],b[key]))))
        rows.append(dict(file=ref.name,bytes_equal=model.sha(ref)==model.sha(other),arrays=arrays))
    assert len(rows)==4
    a=json.loads((args.reference/'summary.json').read_text())
    b=json.loads((args.candidate/'summary.json').read_text())
    differences=[]
    for key in ['status','config','recordings','inputs']:
        compare_value(a[key],b[key],key,differences)
    model.dump(args.out,dict(status='PASS',comparisons=rows,summary_float_differences=differences,
        summary_bytes_equal=model.sha(args.reference/'summary.json')==model.sha(args.candidate/'summary.json'),
        note='Environment and elapsed time retained in each summary; excluded from numerical equality.'))
    print('PASS: input hashes, discrete results, integer stages exact; float stages within 1e-10; byte differences recorded.')

if __name__=='__main__': main()
