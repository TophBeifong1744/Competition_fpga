"""A independent CSV/WAV oracle; no use of B renderer for expected audio."""
import argparse, csv, hashlib, json, math, wave
from pathlib import Path
import numpy as np

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def decode(p):
    with wave.open(str(p),'rb') as w:
        assert (w.getnchannels(),w.getsampwidth(),w.getframerate())==(1,3,48000)
        data=w.readframes(w.getnframes())
    return np.array([int.from_bytes(data[i:i+3],'little',signed=True) for i in range(0,len(data),3)],dtype=np.int64)

def compare(a,b,path,changes):
    assert type(a)==type(b),path
    if isinstance(a,dict):
        assert a.keys()==b.keys(),path
        for k in a: compare(a[k],b[k],path+'/'+k,changes)
    elif isinstance(a,list):
        assert len(a)==len(b),path
        for i,(x,y) in enumerate(zip(a,b)): compare(x,y,path+'/'+str(i),changes)
    elif isinstance(a,float):
        assert math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12),path
        if a!=b: changes.append(dict(path=path,absolute_difference=abs(a-b)))
    else: assert a==b,path

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('run',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args()
    pkg=args.root/'task-packages/PKG-B-ALG/tasks/real-audio-compare-01'
    old=pkg/'evidence/audio-run01';new=args.run/'audio'
    reference=json.loads((old/'result.json').read_text(encoding='utf-8'))
    result=json.loads((new/'result.json').read_text(encoding='utf-8'))
    changes=[];compare(reference,result,'result',changes)
    compare(json.loads((pkg/'evidence/input-check-01.json').read_text(encoding='utf-8')),json.loads((args.run/'input-check.json').read_text(encoding='utf-8')),'input-check',changes)
    cfg=result['input_config'];pos=np.array(cfg['positions_m']);u=np.array([math.sqrt(.5),-math.sqrt(.5),0.])
    delays=(pos-pos[0])@u*48000/343
    np.testing.assert_allclose(delays,result['compensation_delays_samples'],rtol=0,atol=1e-12)
    rows=[]
    for r in result['records']:
        csvpath=args.root/cfg['batch']/'delivery-01'/r['recording']/'samples.csv'
        with csvpath.open(encoding='utf-8',newline='') as f: source=list(csv.DictReader(f))
        ids=[int(row['sample_id']) for row in source]
        assert all(ids[i+1]==ids[i]+1 for i in range(len(ids)-1))
        assert all(int(row['stream_error'])==0 and not row['error_flags'] for row in source)
        pcm=np.array([[int(row[f'mic{k}']) for k in range(4)] for row in source],dtype=np.int64)
        x=pcm/8388608.;n=np.arange(len(x));keep=np.ones(len(x),dtype=bool)
        for d in delays: keep&=(n-d>=0)&(n-d<=len(x)-1)
        valid=n[keep];assert (int(valid[0]),int(valid[-1])+1)==(4,31996)
        assert (r['source_row_start'],r['source_row_stop'])==(4,31996)
        assert (r['first_reference_sample_id'],r['last_reference_sample_id'])==(str(ids[4]),str(ids[31995]))
        manual=sum(np.interp(valid-delays[k],n,x[:,k]) for k in range(4))/4
        for f in r['files']:
            p=new/f['file'];decoded=decode(p);original=decode(old/f['file'])
            np.testing.assert_array_equal(decoded,original)
            assert sha(p)==f['sha256'] and len(decoded)==31992
            signal=x[valid,0] if f['branch']=='single' else manual
            gain=1 if f['mode']=='raw' else 64;assert f['gain']==gain
            signal=signal*gain
            err=float(np.max(np.abs(decoded/8388608.-signal)))
            assert err<=.5/8388608.+1e-12
            assert f['saturation_samples']==0 and np.max(np.abs(signal))<1
            assert math.isclose(float(np.max(np.abs(signal))),f['peak_abs'],abs_tol=1e-12,rel_tol=1e-12)
            assert math.isclose(float(np.sqrt(np.mean(signal**2))),f['rms'],abs_tol=1e-12,rel_tol=1e-12)
            assert math.isclose(err,f['max_quantization_error'],abs_tol=1e-12,rel_tol=1e-12)
            if f['branch']=='single' and f['mode']=='raw': np.testing.assert_array_equal(decoded,pcm[valid,0])
            rows.append(dict(file=f['file'],sha256=sha(p),bytes_equal=sha(p)==sha(old/f['file']),decoded_exact=True,frames=len(decoded),oracle_max_error=err,saturation=0))
    assert len(rows)==8
    report=dict(status='PASS',float_differences=changes,wavs=rows,result_bytes_equal=sha(old/'result.json')==sha(new/'result.json'),input_check_bytes_equal=sha(pkg/'evidence/input-check-01.json')==sha(args.run/'input-check.json'),note='Independent CSV + numpy.interp oracle; same prerecorded input is not acoustic ground truth. Listening record not independently reenacted.')
    with args.output.open('x',encoding='utf-8') as f: json.dump(report,f,indent=2,ensure_ascii=False);f.write('\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
