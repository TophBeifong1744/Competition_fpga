"""B1/B3 exact node verification; extracts unchanged AST nodes, never calls FFT."""
import argparse
import ast
from fractions import Fraction
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import numpy as np
from strict_activity import StrictActivity,checked_power

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def oracle(n,d):return round(Fraction(int(n),int(d)))

def nodes(gate):
    tree=ast.parse(Path(gate.__file__).read_text(encoding='utf-8'));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='stage')
    def target(n):return n.targets[0].id if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) else None
    cut=next(i for i,n in enumerate(fn.body) if target(n)=='spectra')
    front=ast.FunctionDef(name='front',args=fn.args,body=fn.body[:cut]+ast.parse('return x, means, centered, window, weighted').body,decorator_list=[])
    start=next(i for i,n in enumerate(fn.body) if target(n)=='denominator')
    power=ast.FunctionDef(name='power',args=ast.parse('def power(half, window): pass').body[0].args,
        body=fn.body[start:-1]+ast.parse('return sums, numerators, denominator, powers').body,decorator_list=[])
    code=ast.fix_missing_locations(ast.Module(body=[front,power],type_ignores=[]));env=dict(np=np,fixed=gate.fixed)
    exec(compile(code,'<unchanged-stage-node-extraction>','exec'),env)
    return env['front'],env['power'],ast.unparse(code)

def main(repo,out):
    out.mkdir(parents=True,exist_ok=False)
    cp=repo/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923'
    paths=[cp/'source/integer_gate.py',cp/'source/common.py',repo/'task-packages/PKG-B-ALG/tasks/h3-complete-20260918/source/fixed_golden.py']
    sealed=load(cp/'SNAPSHOT-SHA256.json')['files'];deps=load(cp/'dependencies.json')
    for p in paths:
        expected=sealed[p.relative_to(cp.parent).as_posix()] if cp in p.parents else deps[p.relative_to(repo).as_posix()]
        assert sha(p)==expected,p
    sys.path.insert(0,str(cp/'source'));import integer_gate as gate
    def forbidden(*a,**k):raise AssertionError('FFT call forbidden in B1/B3')
    gate.fixed.fixed_fft=forbidden
    front,power,extracted=nodes(gate);(out/'extracted-nodes.py').write_text(extracted+'\n',encoding='utf-8')
    cfg=load(cp/'config.json');records=[];lo=-2**23;hi=2**23-1
    cases={}
    for val in [0,lo,hi]:cases['constant_'+str(val)]=np.full((1024,4),val,dtype=np.int64)
    for val,other in [(lo,hi),(hi,lo)]:
        for idx in [0,511,1023]:
            x=np.full((1024,4),val,dtype=np.int64);x[idx,:]=other;cases[f'outlier_{val}_{idx}']=x
    for total in [512,1536,-512,-1536]:
        x=np.zeros((1024,4),dtype=np.int64);x[511,:]=total;cases['mean_tie_'+str(total)]=x
    beyond=0;goldens={};rom=None
    for name,x in cases.items():
        xx,means,centered,w,weighted=front(x)
        expected_mean=np.array([oracle(sum(map(int,x[:,ch])),1024) for ch in range(4)],dtype=np.int64)
        expected_center=x-expected_mean
        expected_window=np.array([[oracle(int(expected_center[i,ch])*int(w[i]),2**17) for i in range(1024)] for ch in range(4)],dtype=np.int64)
        assert np.array_equal(means,expected_mean) and np.array_equal(centered,expected_center) and np.array_equal(weighted,expected_window)
        assert np.all(centered>=-2**24) and np.all(centered<2**24) and np.all(weighted>=-2**24) and np.all(weighted<2**24)
        assert np.array_equal(w,w[::-1]) and w[0]==w[-1]==0 and np.all((w>=0)&(w<=2**17))
        beyond+=int(np.count_nonzero((weighted<lo)|(weighted>hi)));rom=w
        goldens[name+'_input']=x;goldens[name+'_mean']=expected_mean;goldens[name+'_centered']=expected_center;goldens[name+'_windowed']=expected_window
        records.append(dict(case=name,mean=means.tolist(),centered_min=int(centered.min()),centered_max=int(centered.max()),weighted_min=int(weighted.min()),weighted_max=int(weighted.max())))
    assert beyond>0,'must exercise S25 samples outside S24'
    frozen_hann=[]
    for f in (cp/'evidence/golden02').glob('*.npz'):
        with np.load(f,allow_pickle=False) as z:assert np.array_equal(z['hann'],rom)
        frozen_hann.append(dict(file=f.name,sha256=sha(f)))
    (out/'hann-u18f17.u32le').write_bytes(np.asarray(rom,dtype='<u4').tobytes())
    np.savez_compressed(out/'frontend-oracle.npz',**goldens)
    powercases={}
    for bin in [6,7,72,73]:
        a=np.zeros((4,513,2),dtype=np.int64);a[:,bin,:]=2**24-1;powercases['bin_'+str(bin)]=a
    powercases['zero']=np.zeros((4,513,2),dtype=np.int64)
    powercases['signed25_min']=np.full((4,513,2),-2**24,dtype=np.int64)
    powercases['signed25_max']=np.full((4,513,2),2**24-1,dtype=np.int64)
    powerrecords=[]
    for name,a in powercases.items():
        sums,nums,den,powers=checked_power(a,rom,power)
        expected=[oracle(sum(int(v)**2 for v in a[ch,7:73].ravel())*2**45,sum(int(v)**2 for v in rom)) for ch in range(4)]
        assert powers==expected
        if name in ['zero','bin_6','bin_73']:assert not any(powers)
        powerrecords.append(dict(case=name,sum_power=sums,numerators=nums,denominator=den,powers=powers))
    def reference(state,p,n,invalid):
        active,attack,release=state
        if invalid:return (False,0,0)
        active_channels=sum(Fraction(v,max(k,512**2))>=4 for v,k in zip(p,n))
        holding_channels=sum(Fraction(v,max(k,512**2))>=2 for v,k in zip(p,n))
        attack=min(attack+1,3) if active_channels>=3 else 0
        release=min(release+1,3) if holding_channels<3 else 0
        if not active and attack==3:return (True,attack,0)
        if active and release==3:return (False,0,release)
        return (active,attack,release)
    transitions=0;state_cases=0;noise=[0]*4;floor=512**2
    symbols=[([4*floor]*4,False),([2*floor]*4,False),([2*floor-1]*4,False),([4*floor]*4,True)]
    for sequence in itertools.product(range(4),repeat=6):
        obj=StrictActivity(gate.IntegerActivity,noise,cfg);state=(False,0,0)
        for symbol in sequence:
            p,invalid=symbols[symbol];state=reference(state,p,noise,invalid)
            obj.update(p,invalid);assert obj.state==state,(sequence,state,obj.state);transitions+=1
        state_cases+=1
    boundary_records=[]
    for n in [0,floor,2**62-1,2**62,2**64-1]:
        for channels in [2,3,4]:
            for ratio in [2,4]:
                for offset in [-1,0,1]:
                    value=ratio*max(n,floor)+offset
                    if not 0<=value<2**64:continue
                    noise=[n]*4;p=[value]*channels+[0]*(4-channels)
                    obj=StrictActivity(gate.IntegerActivity,noise,cfg);state=(False,0,0)
                    # Warm active state only where onset is representable, then probe off boundary.
                    if ratio==2 and 4*max(n,floor)<2**64:
                        for _ in range(3):
                            warm=[4*max(n,floor)]*4;obj.update(warm);state=reference(state,warm,noise,False)
                    states=[]
                    for _ in range(4):
                        state=reference(state,p,noise,False);obj.update(p);assert obj.state==state;states.append(list(state));transitions+=1
                    boundary_records.append(dict(noise=n,channels=channels,ratio=ratio,offset=offset,power=p,states=states))
    for n in [2**62,2**64-1]:
        obj=StrictActivity(gate.IntegerActivity,[n]*4,cfg)
        for _ in range(4):assert not obj.update([2**64-1]*4)
        assert obj.state==(False,0,0) if n==2**62 else obj.state==(False,0,3)
    node_rejections=0
    for badhalf in [np.zeros((4,512,2),dtype=np.int64),np.zeros((4,513,2),dtype=float),np.full((4,513,2),2**24,dtype=np.int64)]:
        try:checked_power(badhalf,rom,power)
        except ValueError:node_rejections+=1
        else:raise AssertionError('malformed half accepted')
    for badwindow in [np.zeros(1024,dtype=np.int64),np.full(1024,-1,dtype=np.int64),rom.astype(float)]:
        try:checked_power(powercases['zero'],badwindow,power)
        except ValueError:node_rejections+=1
        else:raise AssertionError('malformed window accepted')
    for n in [65536,196608,-65536,-196608]:
        assert gate.fixed.rne_shift(n,17)==oracle(n,2**17)
    invalid_records=[]
    bad=[('integral_float_noise',lambda cls:cls([1.0]*4,cfg)),('bool_noise',lambda cls:cls([True]*4,cfg)),
         ('negative_floor',lambda cls:cls([0]*4,dict(cfg,band_rms_floor_codes=-512))),
         ('fractional_floor',lambda cls:cls([0]*4,dict(cfg,band_rms_floor_codes=512.5))),
         ('integral_float_power',lambda cls:cls([0]*4,cfg).update([1.0]*4)),
         ('bool_power',lambda cls:cls([0]*4,cfg).update([True]*4)),
         ('missing_channel',lambda cls:cls([0]*4,cfg).update([0]*3)),
         ('power_overflow',lambda cls:cls([0]*4,cfg).update([2**64]*4)),
         ('bad_ratio',lambda cls:cls([0]*4,dict(cfg,on_power_ratio=5))),
         ('nan_power',lambda cls:cls([0]*4,cfg).update([float('nan')]*4)),
         ('inf_power',lambda cls:cls([0]*4,cfg).update([float('inf')]*4)),
         ('nonbool_invalid',lambda cls:cls([0]*4,cfg).update([0]*4,invalid='yes'))]
    for name,call in bad:
        results={}
        for label,cls in [('legacy',gate.IntegerActivity),('strict_candidate',lambda n,c:StrictActivity(gate.IntegerActivity,n,c))]:
            try:call(cls);results[label]='ACCEPTED'
            except (ValueError,TypeError,OverflowError) as e:results[label]=type(e).__name__
        assert results['strict_candidate']!='ACCEPTED',name
        invalid_records.append(dict(case=name,**results))
    for badpcm in [np.zeros((1023,4),dtype=np.int64),np.zeros((1024,4),dtype=float),np.full((1024,4),2**23,dtype=np.int64)]:
        try:front(badpcm)
        except ValueError:pass
        else:raise AssertionError('bad PCM accepted')
    result=dict(status='B1_B3_NODE_CHECK_PASS_WITH_LEGACY_INPUT_GAPS',frontend_cases=len(records),
        s25_window_codes_outside_s24=beyond,power_cases=len(powerrecords),state_sequences=state_cases,state_steps=transitions,
        threshold_cases=len(boundary_records),invalid_cases=len(invalid_records),direct_power_rejections=node_rejections,
        u64_unreachable_onset_cases=2,additional_rne_half_cases=4,
        legacy_invalid_accepted=[r['case'] for r in invalid_records if r['legacy']=='ACCEPTED'],
        frozen_hann_matches=len(frozen_hann),rom_sha256=sha(out/'hann-u18f17.u32le'),source_hashes={str(p.relative_to(repo)):sha(p) for p in paths},
        fft_calls=0,amd_or_rtl_tested=False,full_gate_pipeline_tested=False,default_modified=False)
    dump(out/'result.json',result);dump(out/'frontend-cases.json',records);dump(out/'power-cases.json',powerrecords);dump(out/'threshold-cases.json',boundary_records);dump(out/'invalid-cases.json',invalid_records);dump(out/'frozen-hann.json',frozen_hann)
    dump(out/'OUTPUT-SHA256.json',{p.name:sha(p) for p in out.iterdir() if p.is_file()});print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();main(a.repo.resolve(),a.out.resolve())
