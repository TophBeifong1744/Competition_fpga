"""A-only independent rational-delay and git-identity audit. No renderer imports."""
import argparse, csv, hashlib, json, math, subprocess, wave
from pathlib import Path
import numpy as np

BASE='058aa3095fd4df7392645004b164adb4eec52041'
INPUT='f9768b80e5718dcf29baf48015305780f4b9b8e8'
AUTHOR='6c70cbcac0b24c993a49a0e69efc969dccde5a2a'
REL=Path('task-packages/PKG-B-ALG/tasks/real-audio-compare-01/center-target-01')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def blob(root,rev,name):
    return subprocess.check_output(['git','-c',f'safe.directory={root.as_posix()}','-C',str(root),'show',f'{rev}:{name}'])
def decoded(p):
    with wave.open(str(p),'rb') as w:
        assert (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes())==(1,3,48000,31994)
        b=w.readframes(w.getnframes())
    return np.array([int.from_bytes(b[i:i+3],'little',signed=True) for i in range(0,len(b),3)],dtype=np.int64)
def cmp(a,b,path,diffs):
    assert type(a)==type(b),path
    if isinstance(a,dict):
        assert a.keys()==b.keys(),path
        for k in a: cmp(a[k],b[k],path+'/'+k,diffs)
    elif isinstance(a,list):
        assert len(a)==len(b),path
        for i,(x,y) in enumerate(zip(a,b)): cmp(x,y,path+'/'+str(i),diffs)
    elif isinstance(a,float):
        assert math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12),path
        if a!=b: diffs.append(dict(path=path,error=abs(a-b)))
    else: assert a==b,path
def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('run',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args()
    root=a.root.resolve();pkg=root/REL;ref=pkg/'evidence/audio-run01';cfg=read(pkg/'config.json');pins=read(pkg/'pins.json')
    for name,want in pins.items():
        assert hashlib.sha256(blob(root,BASE,name)).hexdigest()==want
        assert sha(root/name)==want
    batch=root/cfg['batch'];source=batch/'delivery-01'/cfg['recording'];manifest=read(batch/'delivery-01/SHA256.json')
    for n in ['samples.csv','metadata.json']:
        path=(source/n).relative_to(root).as_posix()
        assert sha(source/n)==hashlib.sha256(blob(root,INPUT,path)).hexdigest()==manifest[cfg['recording']+'/'+n]
    for name in read(pkg/'MANIFEST.json'):
        assert (pkg/name).read_bytes()==blob(root,AUTHOR,(REL/name).as_posix())
    with (source/'samples.csv').open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    ids=[int(r['sample_id']) for r in rows]
    assert len(ids)==32000 and ids==list(range(17413,49413))
    assert all(r['stream_error']=='0' and not r['error_flags'] for r in rows)
    pcm=np.array([[int(r['mic'+str(k)]) for k in range(4)] for r in rows],dtype=np.int64)
    t=np.arange(6,32000);den=4*343
    # 0.04*48000/343 = 1920/343 = 5 + 205/343.
    # Delayed lanes interpolate at n-6 + 138/343, with weights 205 and 138.
    num=343*(pcm[t,0]+pcm[t,3])+205*(pcm[t-6,1]+pcm[t-6,2])+138*(pcm[t-5,1]+pcm[t-5,2])
    raw_manual=num/den/2**23;raw_single=pcm[t,0]/2**23
    peak=max(float(np.max(np.abs(pcm)))/2**23,float(np.max(np.abs(raw_manual))),float(np.max(np.abs(raw_single))))
    gain=1 if peak==0 else 128
    while peak*gain>.5:gain/=2
    assert gain==32 and peak==.007843017578125
    actual=read(a.run/'audio/result.json');differences=[]
    cmp(read(ref/'result.json'),actual,'result',differences)
    cmp(read(pkg/'evidence/input-check-01.json'),read(a.run/'input-check.json'),'input',differences)
    cmp(read(pkg/'evidence/audit-01.json'),read(a.run/'audit.json'),'author_audit',differences)
    np.testing.assert_allclose(actual['compensation_delays_samples'],[0,1920/343,1920/343,0],rtol=0,atol=1e-12)
    assert actual['preview_common_gain']==gain and actual['preview_peak_basis']==peak
    r=actual['records'][0];assert len(actual['records'])==1
    assert (r['output_reference_row_start'],r['output_reference_row_stop'])==(6,32000)
    assert (r['first_reference_sample_id'],r['last_reference_sample_id'])==('17419','49412')
    records=[]
    for item in r['files']:
        g=1 if item['mode']=='raw' else 32;assert item['gain']==g
        n=(pcm[t,0]*den if item['branch']=='single' else num)*g
        q,rem=np.divmod(n,den);golden=q+((2*rem>den)|((2*rem==den)&(q%2==1)))
        p=a.run/'audio'/item['file'];code=decoded(p)
        np.testing.assert_array_equal(code,decoded(ref/item['file']))
        assert sha(p)==item['sha256']
        diff=int(np.max(np.abs(code-golden)))
        error=float(np.max(np.abs(code*den-n)))/den/2**23
        assert diff<=1 and error<=.5/2**23+1e-12
        assert item['saturation_samples']==0 and np.all((golden>=-2**23)&(golden<2**23))
        signal=n/den/2**23
        assert math.isclose(item['peak_abs'],float(np.max(np.abs(signal))),abs_tol=1e-12,rel_tol=1e-12)
        assert math.isclose(item['rms'],float(np.sqrt(np.mean(signal**2))),abs_tol=1e-12,rel_tol=1e-12)
        assert math.isclose(item['max_quantization_error'],error,abs_tol=1e-12,rel_tol=1e-12)
        records.append(dict(file=item['file'],sha256=sha(p),bytes_equal=sha(p)==sha(ref/item['file']),decoded_equal=True,rational_golden_max_code_difference=diff,rational_max_error=error))
    assert len(records)==4
    result=dict(status='A_INDEPENDENT_PASS',reviewed_sha=AUTHOR,pins_git_baseline_checked=len(pins),input_git_commit=INPUT,all_author_files_unchanged=True,crop=[6,32000],reference_ids=[17419,49412],frames=31994,preview_gain=gain,peak_basis=peak,wavs=records,float_differences=differences,json_bytes_equal={n:sha(a.run/new)==sha(pkg/old) for n,new,old in [('result','audio/result.json','evidence/audio-run01/result.json'),('input','input-check.json','evidence/input-check-01.json'),('audit','audit.json','evidence/audit-01.json')]},note='Exact rational code oracle; no borrowed acoustic truth and no independent listening claim.')
    with a.out.open('x',encoding='utf-8') as f: json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
