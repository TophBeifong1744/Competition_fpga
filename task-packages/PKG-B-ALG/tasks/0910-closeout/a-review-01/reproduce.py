"""A's independent receipt audit. Never execute/overwrite B's fixed run01."""
import argparse,csv,hashlib,json,math,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();repo=a.repo.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
prefix='task-packages/PKG-B-ALG/tasks/0910-closeout/'
original='146736bf692d10fcfe0a95e8ffd7e16a0d4b4120'
git=lambda *s:subprocess.check_output(['git',*s],cwd=repo)
assert git('rev-parse','HEAD').decode().strip()==original
paths=git('diff-tree','--no-commit-id','--name-only','-r',original).decode().splitlines()
assert len(paths)==15 and all(v.startswith(prefix) for v in paths)
hashes={}
for name in paths:
    raw=(repo/name).read_bytes()
    assert raw==git('show',original+':'+name),name
    hashes[name]=hashlib.sha256(raw).hexdigest()
commands=[]
def run(label,cmd,cwd):
    r=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True)
    (out/(label+'.txt')).write_text(r.stdout+r.stderr,encoding='utf-8')
    commands.append(dict(command=cmd,cwd=str(cwd),exit_code=r.returncode))
    assert r.returncode==0,(label,r.stderr)
mono=repo/'task-packages/PKG-A-H2-MONO-DIAGNOSTIC'
for label,file in [('manifest','file_manifest.py'),('export','mono_delivery.py'),('tests','test_delivery.py')]:
    run(label,[sys.executable,'-B','source/'+file]+([] if label=='tests' else ['verify']),mono)
run('h3',[sys.executable,'-B',str(repo/'task-packages/PKG-A-H3-INTEGRATION/source/verify.py'),'--out',str(out/'h3')],repo)
read=lambda path:json.loads(path.read_text(encoding='utf-8'))
old=repo/prefix/'evidence/run01'
def equal(x,y):
    if isinstance(x,dict):
        assert x.keys()==y.keys()
        for k in x: equal(x[k],y[k])
    elif isinstance(x,list):
        assert len(x)==len(y)
        for v,w in zip(x,y):equal(v,w)
    elif isinstance(x,float): assert math.isclose(x,y,abs_tol=1e-7,rel_tol=1e-10),(x,y)
    else: assert type(x)==type(y) and x==y,(x,y)
records=[]
for prior in read(old/'result.json')['mono_records']:
    folder=mono/'data'/prior['name'];meta=read(folder/'metadata.json');raw=(folder/meta['raw_file']).resolve().read_bytes()
    assert len(raw)==48000*16
    # Decode with byte slices/int.from_bytes, independently of B's struct unpacker.
    rows=[(int.from_bytes(raw[i:i+8],'little'),int.from_bytes(raw[i+8:i+12],'little',signed=True),
           int.from_bytes(raw[i+12:i+16],'little')) for i in range(0,len(raw),16)]
    with (folder/'samples.csv').open(newline='') as f:
        reader=csv.reader(f);assert next(reader)==['sample_id','pcm','flags']
        assert [tuple(map(int,r)) for r in reader]==rows
    ids,x,flags=zip(*rows);n=len(x);mean=sum(x)/n;square=sum(v*v for v in x)/n
    r=dict(name=prior['name'],samples=n,first_id=ids[0],last_id=ids[-1],
        gaps=sum(v-u!=1 for u,v in zip(ids,ids[1:])),nonzero_flags=sum(v!=0 for v in flags),
        outside_signed24=sum(v<-(1<<23) or v>=(1<<23) for v in x),
        clipped_endpoints=sum(v in (-(1<<23),(1<<23)-1) for v in x),non_multiple_of_32=sum(v%32!=0 for v in x),
        minimum=min(x),maximum=max(x),mean_pcm=mean,rms_pcm=math.sqrt(square),ac_rms_pcm=math.sqrt(square-mean*mean),
        peak_fullscale=max(map(abs,x))/(1<<23),first_4800_mean_pcm=sum(x[:4800])/4800,last_4800_mean_pcm=sum(x[-4800:])/4800,
        raw_sha256=hashlib.sha256(raw).hexdigest(),source_kind=meta['source_kind'],sample_rate_status=meta['sample_rate_status'],
        loaded_identity_verified=meta['loaded_identity_verified'])
    equal(r,prior);records.append(r)
comparisons={}
for rel in ['export.txt','h3/result.json','h3/calculations.json','h3/fft/check.json','h3/fft/vectors/reference.json']:
    equal(read(old/rel),read(out/rel))
    comparisons[rel]=dict(numeric_semantic_equal=True,bytes_equal=(old/rel).read_bytes()==(out/rel).read_bytes())
assert (old/'h3/fft/vectors/inputs.mem').read_bytes()==(out/'h3/fft/vectors/inputs.mem').read_bytes()
for rel,count in [('tests.txt',10),('h3/tests.txt',11)]:
    oldtests=[line for line in (old/rel).read_text().splitlines() if line.startswith('test_')]
    newtests=[line for line in (out/rel).read_text().splitlines() if line.startswith('test_')]
    assert oldtests==newtests and len(newtests)==count and all(line.endswith('ok') for line in newtests)
for rel in ['h3.txt','h3/fft.txt']:
    oldvalue=json.JSONDecoder().raw_decode((old/rel).read_text())[0]
    newvalue=json.JSONDecoder().raw_decode((out/rel).read_text())[0]
    equal(oldvalue,newvalue)
assert (old/'manifest.txt').read_text()==(out/'manifest.txt').read_text()
assert all(hashlib.sha256((repo/name).read_bytes()).hexdigest()==h for name,h in hashes.items())
result=dict(status='PASS_LIMITED_RECEIPT_AND_RECAP_NOT_H2_H3',reviewed_commit=original,
    original_files=hashes,commands=commands,mono_records=records,comparisons=comparisons,
    fft_input_bytes_equal=True,original_evidence_unchanged=True,
    not_verified=['B unpublished research','new XSim','new synthesis','board identity','full H2/H3'])
(out/'review-result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status=result['status'],original_files=len(hashes),mono_samples=96000,comparisons=comparisons),indent=2))
