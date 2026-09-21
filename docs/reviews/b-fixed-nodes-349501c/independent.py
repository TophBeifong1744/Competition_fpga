"""A rational geometry and streaming audit, independent of B node verifier."""
from fractions import Fraction as F
from decimal import Decimal, localcontext
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import subprocess
import sys
import numpy as np

root, repo, out = map(Path, sys.argv[1:4])
pkg=root/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918'
nodes=pkg/'fixed-nodes-20260921'
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=subprocess.check_output(['git','-C',str(repo),'cat-file','blob','b5913e596e28b30f9e04cf2c9ba365430b8914df:task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923/SNAPSHOT-SHA256.json'])
assert old==(nodes/'SNAPSHOT-before-nodes.json').read_bytes()
for name,value in json.loads(old)['files'].items(): assert sha(pkg/name)==value,name
manifest=pkg/'checkpoint-20260923/SNAPSHOT-SHA256.json'
assert {p.relative_to(pkg).as_posix():sha(p) for p in pkg.rglob('*') if p.is_file() and p!=manifest}==load(manifest)['files']
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
fixed=module('audit_fixed',root/'task-packages/PKG-B-ALG/tasks/h3-complete-20260918/source/fixed_golden.py')
stream=module('audit_stream',nodes/'b5b6/stream_das.py')
# Geometry independently constructed from four square vertices, not DUT deltas.
positions=[(0,0),(1,0),(1,1),(0,1)]
deltas=[(positions[j][0]-positions[i][0],positions[j][1]-positions[i][1]) for i,j in itertools.combinations(range(4),2)]
with localcontext() as c:
    c.prec=100
    bounds=[int(Decimal(dx*dx+dy*dy).sqrt()*Decimal(1920*4096)/343) for dx,dy in deltas]
count=outside=0;maximum=0
for mask in itertools.product([False,True],repeat=6):
    ids=[i for i,b in enumerate(mask) if b]
    if len(ids)<3:continue
    xx=sum(deltas[i][0]**2 for i in ids);xy=sum(deltas[i][0]*deltas[i][1] for i in ids);yy=sum(deltas[i][1]**2 for i in ids)
    assert xx*yy-xy*xy>0
    for signs in itertools.product([-1,1],repeat=len(ids)):
        tau={i:s*bounds[i] for i,s in zip(ids,signs)}
        bx=sum(deltas[i][0]*tau[i] for i in ids);by=sum(deltas[i][1]*tau[i] for i in ids)
        y=(F(by)-F(xy*bx,xx))/(F(yy)-F(xy*xy,xx));x=(F(bx)-xy*y)/xx
        want=[round(z*F(343*256,1920)) for z in [x,y]]
        got=fixed.doa_q20([dict(valid=i in tau,tau_q12=tau.get(i,0)) for i in range(6)])
        assert want==[got['ux_q20'],got['uy_q20']]
        if any(not -2**21<=v<2**21 for v in want):
            outside+=1;assert not got['valid']
        maximum=max(maximum,*map(abs,want));count+=1
assert (count,outside,maximum)==(656,8,2531477)
# Independent exact interpolation for each emitted prefix, not only final PCM.
rng=np.random.default_rng(20260921)
pcm=rng.integers(-2**23,2**23,size=(4,67),dtype=np.int64)
cases=0;lookahead=0
for delays in [[0]*4,[32768,-32768,4095,-4095],[-32767,1,8193,-12000]]:
    expected=[]
    for n in range(pcm.shape[1]):
        total=F(0)
        for ch,d in enumerate(delays):
            q=F(n)-F(d,4096);left=q.numerator//q.denominator;frac=q-left
            val=lambda i:int(pcm[ch,i]) if 0<=i<pcm.shape[1] else 0
            total+=(1-frac)*val(left)+frac*val(left+1)
        expected.append(round(total/4))
    for chunk in [1,2,11,67]:
        obj=stream.StreamDAS(delays);actual=[]
        for i in range(0,pcm.shape[1],chunk):
            actual.extend(obj.push(pcm[:,i:i+chunk]).tolist())
            assert actual==expected[:len(actual)]
            assert len(actual)==max(0,obj.received-obj.lookahead)
        actual.extend(obj.push(np.zeros((4,0),dtype=np.int64),final=True).tolist())
        assert actual==expected;lookahead=max(lookahead,obj.lookahead);cases+=1
        try:obj.push(pcm[:,:1])
        except ValueError:pass
        else:raise AssertionError('accepted after final')
rejected=0
for delays in [[0]*3,[True,0,0,0],[0.,0,0,0],[32769,0,0,0]]:
    try:stream.StreamDAS(delays)
    except ValueError:rejected+=1
    else:raise AssertionError('invalid delays')
for bad in [pcm.astype(float),np.zeros((4,2),dtype=bool),pcm[:3],np.full((4,2),2**23,dtype=np.int64)]:
    try:stream.StreamDAS([0]*4).push(bad)
    except ValueError:rejected+=1
    else:raise AssertionError('invalid PCM')
assert lookahead==9 and rejected==8
result=dict(status='A_INDEPENDENT_PASS',old_files_unchanged=len(json.loads(old)['files']),current_snapshot_files=len(load(manifest)['files']),
    rational_vertices=count,rejected_outside_s22=outside,max_abs_xy=maximum,stream_prefix_and_final_cases=cases,
    max_lookahead=lookahead,invalid_stream_cases=rejected,hardware_or_production_approved=False)
with out.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
print(json.dumps(result))
