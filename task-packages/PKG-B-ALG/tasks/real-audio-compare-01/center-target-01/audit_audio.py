"""Author cross-check using independent CSV/np.interp/PCM decoding.

Does not call the production renderer to construct expected audio.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import wave
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--audio',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    if args.out.exists(): raise FileExistsError(args.out)
    report=json.loads((args.audio/'result.json').read_text(encoding='utf-8'))
    cfg=report['config']
    for name,want in {**report['pins'],**report['source_sha256']}.items():
        if sha(ROOT/name)!=want: raise ValueError('source/input hash mismatch')
    csvpath=ROOT/cfg['batch']/'delivery-01'/cfg['recording']/'samples.csv'
    with csvpath.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    pcm=np.array([[int(row[c]) for c in cfg['channel_order']] for row in rows],dtype=np.int64)
    if any(row['stream_error']!='0' or row['error_flags'] for row in rows):
        raise ValueError('this pinned audit expects the accepted single clean interval')
    ids=[int(row['sample_id']) for row in rows]
    if any(b!=a+1 for a,b in zip(ids,ids[1:])): raise ValueError('ID discontinuity')
    # Pinned +X geometry yields delays in samples; independent direct expression.
    d=np.array([0,.04*48000/343,.04*48000/343,0])
    np.testing.assert_allclose(report['compensation_delays_samples'],d,rtol=0,atol=1e-12)
    n=np.arange(len(pcm));keep=np.all((n[:,None]-d>=0)&(n[:,None]-d<=len(pcm)-1),axis=1); t=n[keep]
    x=pcm/2**23
    single=x[t,0]
    manual=sum(np.interp(t-d[i],n,x[:,i]) for i in range(4))/4
    assert len(report['records'])==1
    r=report['records'][0]
    assert (r['output_reference_row_start'],r['output_reference_row_stop'])==(int(t[0]),int(t[-1]+1))
    assert (r['first_reference_sample_id'],r['last_reference_sample_id'])==(str(ids[t[0]]),str(ids[t[-1]]))
    peak=max(float(np.max(np.abs(x))),float(np.max(np.abs(single))),float(np.max(np.abs(manual))))
    gain=128.
    while peak*gain>.5: gain/=2
    assert gain==report['preview_common_gain']
    comparisons=[]
    for item in r['files']:
        file=args.audio/item['file']; assert sha(file)==item['sha256']
        with wave.open(str(file),'rb') as w:
            assert (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes())==(1,3,48000,len(t))
            raw=w.readframes(len(t))
        code=np.array([int.from_bytes(raw[i:i+3],'little',signed=True) for i in range(0,len(raw),3)],dtype=np.int64)
        g=1. if item['mode']=='raw' else gain
        ideal=(single if item['branch']=='single' else manual)*g
        golden=np.clip(np.rint(ideal*2**23),-2**23,2**23-1).astype(np.int64)
        maxcode=int(np.max(np.abs(code-golden)))
        error=float(np.max(np.abs(code/2**23-ideal)))
        assert maxcode<=1 and error<=.5/2**23+1e-12 # Independent float evaluation may round at a half-LSB.
        if item['branch']=='single' and item['mode']=='raw': np.testing.assert_array_equal(code,pcm[t,0])
        saturated=int(np.count_nonzero((np.rint(ideal*2**23)<-2**23)|(np.rint(ideal*2**23)>2**23-1)))
        assert saturated==item['saturation_samples']==0
        comparisons.append(dict(file=item['file'],max_code_difference=maxcode,max_absolute_error=error,saturation=saturated))
    assert len(comparisons)==4
    result=dict(status='AUTHOR_CROSSCHECK_PASS',comparisons=comparisons,common_gain=gain,
        sample_count=len(t),crop=[int(t[0]),int(t[-1]+1)],audit_source_sha256=sha(Path(__file__)),
        note='Separate numerical implementation; still author self-test, not A independent review.')
    with args.out.open('x',encoding='utf-8') as f: json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(result))

if __name__=='__main__': main()
