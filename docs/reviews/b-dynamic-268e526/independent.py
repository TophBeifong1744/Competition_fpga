"""A incremental audit: frozen bytes, strict generated outputs, causal PCM."""
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import numpy as np

root,repo,run,out=map(Path,sys.argv[1:5])
pkg=root/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918'
p=pkg/'dynamic-das-20260921'
load=lambda f:json.loads(f.read_text(encoding='utf-8'))
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
snapshot=pkg/'checkpoint-20260923/SNAPSHOT-SHA256.json'
raw=subprocess.check_output(['git','-C',str(repo),'cat-file','blob','fd1b99c966de1f572bcd080f2b2d6860c0ac5ccd:task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923/SNAPSHOT-SHA256.json'])
assert raw==(p/'SNAPSHOT-before-dynamic.json').read_bytes()
for name,h in json.loads(raw)['files'].items():assert sha(pkg/name)==h
assert load(snapshot)['files']=={f.relative_to(pkg).as_posix():sha(f) for f in pkg.rglob('*') if f.is_file() and f!=snapshot}
compared=0
for group in ['dynamic','delay','widths','width-trace','integration']:
    for original in (p/'validation/portable01'/group).iterdir():
        actual=run/group/original.name
        if original.suffix=='.json':assert load(original)==load(actual),original.name
        elif original.suffix=='.npz':
            with np.load(original,allow_pickle=False) as a,np.load(actual,allow_pickle=False) as b:
                assert a.files==b.files
                for key in a.files:assert a[key].dtype==b[key].dtype and np.array_equal(a[key],b[key])
        else:assert original.read_bytes()==actual.read_bytes(),original.name
        compared+=1
spec=importlib.util.spec_from_file_location('audit_dynamic',p/'dynamic_das.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
pcm=np.random.default_rng(8128).integers(-2**23,2**23,size=(4,1600),dtype=np.int64)
def value(target,n):
    if n<0:return 0
    def sample(ch,k):return int(pcm[ch,k]) if 0<=k<pcm.shape[1] else 0
    if target is None:return sample(0,n)
    total=F(0)
    for ch,d in enumerate(target):
        pos=F(n)-F(d,4096);left=pos.numerator//pos.denominator;frac=pos-left
        total+=sample(ch,left)*(1-frac)+sample(ch,left+1)*frac
    return round(total/4)
count=0;waits=[]
for stop in [1,479,480,481,959]:
    e=m.DynamicDAS();e.control(state='LOCKED',delays=(-32768,32768,-32767,32767),valid_through=1500)
    for t in range(pcm.shape[1]):
        if t==stop:e.control(state='STOP')
        y,trace=e.push(pcm[:,t:t+1],final=t==pcm.shape[1]-1)
        for actual,r in zip(y,trace,strict=True):
            targets=r['endpoints'];n=r['emit']-8
            expected=value(targets[0],n) if len(targets)==1 else round(F(value(targets[0],n)*(4096-r['alpha'])+value(targets[1],n)*r['alpha'],4096))
            assert int(actual)==expected
            # Every nonzero-weight source access is available by the emit time.
            for target in targets:
                if target is None or n<0:continue
                for d in target:
                    q=F(n)-F(d,4096);left=q.numerator//q.denominator
                    assert left+(q.denominator!=1)<=r['emit']
            if r['emit']>=stop and targets==(None,) and len(waits)<=count:waits.append(r['emit']-stop)
        assert e.max_history<=17 and e.max_beams<=2
    count+=1
assert max(waits)<=960
e=m.DynamicDAS();e.control(state='LOCKED',delays=(0,0,0,0),valid_through=1)
e.push(pcm[:,:1]);e.control(state='HOLD');assert e.expiry==1
e.push(pcm[:,1:2]);e.control(state='LOCKED',delays=(0,1,2,3),valid_through=100)
e.push(pcm[:,2:3]);assert not any(r['kind']=='TTL_EXPIRED' for r in e.events)
result=dict(status='A_INCREMENTAL_PASS',old_snapshot_files=len(json.loads(raw)['files']),new_snapshot_files=len(load(snapshot)['files']),
    strict_output_files=compared,independent_extreme_delay_stop_cases=count,fallback_waits=waits,max_history=17,
    fresh_before_expiry=True,rom_bytes_equal=True,production_approval=False)
with out.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
print(json.dumps(result))
