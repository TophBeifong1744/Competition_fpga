"""Read-only A diagnostics after the official reproduction comparator fails."""
import argparse
import hashlib
import json
from pathlib import Path
import wave
import numpy as np


def load(p):
    return json.loads(p.read_text(encoding='utf-8'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def differences(a, b, path='', out=None):
    out = [] if out is None else out
    if type(a) is not type(b):
        out.append(dict(path=path, kind='type', a=str(a), b=str(b)))
    elif isinstance(a, dict):
        for k in a.keys() | b.keys():
            if k not in a or k not in b:
                out.append(dict(path=path+'/'+k, kind='key'))
            else:
                differences(a[k], b[k], path+'/'+k, out)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append(dict(path=path, kind='length', a=len(a), b=len(b)))
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                differences(x, y, path+'/'+str(i), out)
    elif a != b:
        out.append(dict(path=path, kind='float' if isinstance(a, float) else 'discrete', a=a, b=b))
    return out


def decode(p):
    with wave.open(str(p),'rb') as w:
        assert (w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()) == (1,3,48000,288234)
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.uint8).reshape(-1,3).astype(np.int64)
    x = a[:,0] + (a[:,1]<<8) + (a[:,2]<<16)
    return np.where(x >= 2**23, x-2**24, x)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True)
    ap.add_argument('--run',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    pkg=args.repo/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923'
    old=pkg/'evidence/run01';new=args.run/'study'
    json_reports=[]
    for p in sorted(old.glob('*.json')):
        if p.name=='OUTPUT-SHA256.json':continue
        a,b=load(p),load(new/p.name)
        if p.name=='summary.json':a.pop('environment');b.pop('environment')
        d=differences(a,b)
        floats=[v for v in d if v['kind']=='float']
        json_reports.append(dict(file=p.name,bytes_equal=sha(p)==sha(new/p.name),
            float_differences=len(floats),other_differences=[v for v in d if v['kind']!='float'],
            max_abs_float_difference=max([abs(v['a']-v['b']) for v in floats]+[0]),
            first_differences=d[:3]))
    wav_reports=[]
    for p in sorted((old/'audio').glob('*.wav')):
        a,b=decode(p),decode(new/'audio'/p.name)
        wav_reports.append(dict(file=p.name,bytes_equal=sha(p)==sha(new/'audio'/p.name),
            mismatch_codes=int(np.count_nonzero(a!=b)),max_code_error=int(np.max(np.abs(a-b)))))
    arrays=0;unequal=[]
    for p in sorted((pkg/'evidence/golden02').glob('*.npz')):
        with np.load(p,allow_pickle=False) as a,np.load(args.run/'golden'/p.name,allow_pickle=False) as b:
            assert a.files==b.files
            for k in a.files:
                arrays+=1
                if a[k].dtype!=b[k].dtype or not np.array_equal(a[k],b[k]):unequal.append([p.name,k])
    golden_diffs=differences(load(pkg/'evidence/golden02/summary.json'),load(args.run/'golden/summary.json'))
    # Separate original-PCM computation. This data's automatic branch never locks.
    summary=load(new/'summary.json');independent=[]
    for r in summary['reports']:
        name=r['capture'];path=next(k for k in summary['pins'] if k.endswith('/'+name+'/raw.bin'))
        raw=np.fromfile(args.repo/path,dtype='<u4').reshape(-1,8)
        assert not raw[:,6:].any()
        codes=raw[:,2:6].view('<i4').astype(np.int64);n=np.arange(8,len(codes)-8)
        angle=r['audio']['manual_deg']*np.pi/180
        d=np.array([[0,0],[.04,0],[.04,.04],[0,.04]])@np.array([np.cos(angle),np.sin(angle)])*48000/343
        manual=sum(np.interp(n-d[i],np.arange(len(codes)),codes[:,i]) for i in range(4))/4
        assert r['audio']['beam_contribution_samples']==0
        expected=dict(single=codes[n,0],automatic=codes[n,0],manual=manual)
        errors=[]
        for branch,value in expected.items():
            for mode,gain in [('raw',1),('preview',12)]:
                actual=decode(new/'audio'/f'{name}-{branch}-{mode}.wav')
                wanted=np.rint(value*gain).astype(np.int64)
                assert np.all((wanted >= -2**23)&(wanted < 2**23))
                errors.append(dict(branch=branch,mode=mode,mismatches=int(np.count_nonzero(actual!=wanted)),
                                   max_code_error=int(np.max(np.abs(actual-wanted)))))
        independent.append(dict(capture=name,comparisons=errors))
    report=dict(official_reproduce_status='FAIL_JSON_EXACT_COMPARISON_NOT_OVERRIDDEN',
                json=json_reports,wavs=wav_reports,integer_arrays=arrays,unequal_integer_arrays=unequal,
                golden_summary_differences=golden_diffs,independent_pcm=independent,
                no_author_files_or_thresholds_modified=True)
    (args.out/'diagnostic.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(json_files=len(json_reports),float_differences=sum(r['float_differences'] for r in json_reports),
        nonfloat_differences=sum(len(r['other_differences']) for r in json_reports),
        max_abs_difference=max(r['max_abs_float_difference'] for r in json_reports),
        wavs_equal=sum(r['bytes_equal'] for r in wav_reports),pcm_errors=sum(r['mismatch_codes'] for r in wav_reports),
        integer_arrays=arrays,unequal_integer_arrays=unequal,golden_summary_differences=len(golden_diffs),
        independent_pcm_errors=sum(c['mismatches'] for r in independent for c in r['comparisons'])),indent=2))


if __name__=='__main__':main()
