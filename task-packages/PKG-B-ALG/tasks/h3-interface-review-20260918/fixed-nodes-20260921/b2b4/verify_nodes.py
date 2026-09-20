"""B2/B4 node-level checks: no full FFT/IFFT or old acoustic research."""
import argparse
import ast
from decimal import Decimal,localcontext,ROUND_HALF_EVEN
from fractions import Fraction
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import numpy as np
from guards import checked_adapter,checked_conjugate,FrameGuard

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def rne(n,d):return round(Fraction(int(n),int(d)))
def module(name,p):
    sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m

def execute(repo,out):
    out.mkdir(parents=True,exist_ok=False)
    tasks=repo/'task-packages/PKG-B-ALG/tasks';cp=tasks/'h3-interface-review-20260918/checkpoint-20260923'
    fp=tasks/'h3-complete-20260918/source/fixed_golden.py';pp=tasks/'phat-fixed-03/phat_model.py';gp=cp/'source/golden.py'
    deps=load(cp/'dependencies.json');seal=load(cp/'SNAPSHOT-SHA256.json')['files']
    for p in [fp,pp,gp]:
        wanted=seal[p.relative_to(cp.parent).as_posix()] if cp in p.parents else deps[p.relative_to(repo).as_posix()]
        assert sha(p)==wanted,p
    fixed=module('b2_fixed',fp);phat=module('b4_phat',pp)
    fixed.fixed_fft=lambda *a,**k:(_ for _ in ()).throw(AssertionError('Full FFT forbidden'))
    # Threshold fixed before normalization cases: ideal PHAT deviation <=2 output codes.
    error_limit=2;checks={};details={};inputs=sorted(set([-2**28,-2**28+1,2**28-1,2**28-8,2**28-9,0]+[16*q+r for q in [-100,-3,-2,-1,0,1,2,3,100] for r in [7,8,9]]))
    a=np.zeros((4,513,2),dtype=np.int64);a.flat[:len(inputs)]=inputs
    result,ov=checked_adapter(a,fixed.adapt_fft29_to_s25)
    exp=np.array([max(-2**24,min(2**24-1,rne(v,16))) for v in a.flat],dtype=np.int64).reshape(a.shape)
    expected_ov=sum(not -2**24<=rne(v,16)<2**24 for v in a.flat)
    assert np.array_equal(result,exp) and ov==expected_ov and ov>0
    checks['adapter_boundary_values']=len(inputs);details['adapter']=dict(values=inputs,codes=list(map(int,result.flat[:len(inputs)])),overflow=ov)
    bad=[]
    for name,x in [('float',a.astype(float)),('shape',a[:3]),('outside29',np.full_like(a,2**28))]:
        try:checked_adapter(x,fixed.adapt_fft29_to_s25)
        except ValueError:bad.append(name)
        else:raise AssertionError(name)
    # Single butterfly arithmetic as used in fixed_fft; AST extraction, no transform.
    tree=ast.parse(fp.read_text(encoding='utf-8'));fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='fixed_fft')
    statements=[]
    for x in ast.walk(fn):
        if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name) and x.targets[0].id in ['tr','ti','candidates']:statements.append(x)
    node=ast.fix_missing_locations(ast.Module(body=statements,type_ignores=[]));code=compile(node,'<butterfly-nodes>','exec')
    (out/'butterfly-extracted.py').write_text(ast.unparse(node)+'\n',encoding='utf-8')
    butterfly=0;butterfly_overflows=0
    for width in [25,29]:
        for ar,ai,br,bi in [(0,0,1,-1),(1,-1,3,-3),(2**(width-1)-1,)*4,(-2**(width-1),)*4]:
            for wr,wi in [(2**30,0),(0,2**30),(759250125,759250125),(2**29,-2**29)]:
                env=dict(ar=ar,ai=ai,br=br,bi=bi,wr=wr,wi=wi,TWIDDLE_FRAC=30,rne_shift=fixed.rne_shift)
                exec(code,env)
                tr=rne(wr*br-wi*bi,2**30);ti=rne(wr*bi+wi*br,2**30)
                assert env['candidates']==((ar+tr,ai+ti),(ar-tr,ai-ti))
                for pair in env['candidates']:
                    for v in pair:
                        q,overflow=fixed.saturate(fixed.rne_shift(v,1),width);wanted=rne(v,2)
                        assert q==max(-2**(width-1),min(2**(width-1)-1,wanted)) and overflow==(q!=wanted)
                        butterfly_overflows+=int(overflow)
                butterfly+=1
    checks['butterfly_cases']=butterfly;checks['butterfly_component_overflows']=butterfly_overflows
    # Exact midpoint/large square cases, Decimal oracle has >150bit precision margin.
    sqrtcases=0
    with localcontext() as ctx:
        ctx.prec=100
        for k in [0,1,2,7,2**24,2**50,2**74]:
            for n in sorted(set([k*k,k*k+k,k*k+k+1,(k+1)*(k+1)])):
                assert phat.sqrt_rne(n)==int(Decimal(n).sqrt().to_integral_value(rounding=ROUND_HALF_EVEN));sqrtcases+=1
        norm=[]
        zcases=[(0,0),(1,0),(-1,0),(0,1),(0,-1),(3,4),(-3,4),(3,-4),(-3,-4),(1,1)]
        for values in itertools.product([-2**24,-1,0,1,2**24-1],repeat=4):zcases.append(phat.cross(values[:2],values[2:]))
        for re,im in sorted(set(zcases)):
            actual,meta=phat.normalize((re,im));square=re*re+im*im
            if not square:assert actual==(0,0) and not meta['valid'];continue
            mag=Decimal(square).sqrt();ideal=[int((Decimal(v)*Decimal(2**23)/mag).to_integral_value(rounding=ROUND_HALF_EVEN)) for v in [re,im]]
            err=max(abs(a-b) for a,b in zip(actual,ideal));assert err<=error_limit,(re,im,err)
            norm.append(dict(cross=[re,im],actual=list(actual),ideal=ideal,max_error=err))
    assert tuple(phat.RECIP_LUT)==tuple(rne(2**30*512,513+2*k) for k in range(256))
    assert phat.EPSILON_CODES==Fraction(2**26,10**15) and 0<phat.EPSILON_CODES<1
    checks.update(sqrt_cases=sqrtcases,reciprocal_lut_entries=256,normalization_cases=len(norm),normalization_code_error_limit=error_limit,max_normalization_code_error=max(x['max_error'] for x in norm))
    band=[7<=i<=85 for i in range(513)];maskrecords=[]
    for maximum in [49,50,51]:
        z=[(0,0)]*513;z[7]=(maximum,0);z[8]=(1,0);z[6]=(10**9,0);z[86]=(10**9,0)
        actual=phat.mask_for(z,band)
        expected=[band[i] and (r*r+j*j)>0 and Fraction(r*r+j*j,maximum**2)>=Fraction(1,2500) for i,(r,j) in enumerate(z)]
        assert actual==expected;maskrecords.append(dict(maximum=maximum,one_code_kept=actual[8]))
    for count in [0,11,12]:
        a=[(0,0)]*513;b=[(0,0)]*513
        for i in range(7,7+count):a[i]=(1,0);b[i]=(1,0)
        r=phat.phat_pair(a,b,band);assert r['valid']==(count>=12)
        for channel in range(4):
            flags=[False]*4;flags[channel]=True
            q=phat.phat_pair(a,b,band,ip_overflow=any(flags));assert not q['valid'] and q['reason']=='UPSTREAM_IP_OVERFLOW' and not any(q['mask'])
    checks.update(mask_equal_boundary_cases=3,bin_count_cases=3,upstream_flag_cases=12)
    half=np.zeros((513,2),dtype=np.int64);half[7]=[2**23,-2**23];full=checked_conjugate(half,fixed.conjugate_complete)
    assert all(full[1024-k,0]==half[k,0] and full[1024-k,1]==-half[k,1] for k in range(1,512))
    legacy_gaps=[]
    for name,index,value in [('dc_imag',0,1),('nyquist_imag',512,1),('minimum_imag',7,-2**24)]:
        h=half.copy();h[index,1]=value;raw=fixed.conjugate_complete(h)
        legacy_gaps.append(dict(case=name,legacy_accepted=True,outside_s25=bool(np.any(raw>=2**24))))
        try:checked_conjugate(h,fixed.conjugate_complete)
        except ValueError:pass
        else:raise AssertionError(name)
    # Exercise exact existing checkpoint any-IFFT-overflow aggregation statement.
    tree=ast.parse(gp.read_text(encoding='utf-8'))
    guard=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and 'ifft_flags' in ast.unparse(n.test) and 'overflow_count' in ast.unparse(n.test))
    code=compile(ast.fix_missing_locations(ast.Module(body=[guard],type_ignores=[])),'<checkpoint-ifft-guard>','exec')
    for fault in range(6):
        flags=[dict(overflow_count=int(i==fault)) for i in range(6)];env=dict(ifft_flags=flags,lags=[dict(valid=True)]*6);exec(code,env)
        assert all(not x['valid'] and x['reason']=='IFFT_OVERFLOW' for x in env['lags'])
    units=['fft'+str(i) for i in range(4)]+['ifft'+str(i) for i in range(6)]
    g=FrameGuard('frame1',units);assert not g.commit()
    for u in units[:-1]:g.status('frame1',u)
    assert not g.commit();g.status('frame1',units[-1]);assert not g.commit(stop=True)
    h=FrameGuard('frame2',units)
    for u in units:h.status('frame2',u)
    assert h.commit() and not h.commit();h.status('frame2',units[-1],error=True)
    assert h.invalid and h.committed and h.events[-1]=='LATE_ERROR_AFTER_COMMIT'
    checks.update(conjugate_bins=511,legacy_conjugate_gaps=len(legacy_gaps),actual_ifft_aggregation_cases=6,frame_guard_candidate_scenarios=5)
    dump(out/'result.json',dict(status='B2_B4_NODE_PASS_WITH_UNINTEGRATED_GUARDS',checks=checks,adapter_rejections=bad,
        legacy_gaps=legacy_gaps,source_hashes={p.relative_to(repo).as_posix():sha(p) for p in [fp,pp,gp]},
        fft_calls=0,ifft_calls=0,amd_tested=False,full_dynamic_range_proved=False,late_status_implemented_in_checkpoint=False))
    dump(out/'normalization-cases.json',norm);dump(out/'mask-cases.json',maskrecords);dump(out/'adapter-cases.json',details)
    dump(out/'OUTPUT-SHA256.json',{p.name:sha(p) for p in out.iterdir() if p.is_file()});print(json.dumps(checks,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();execute(a.repo.resolve(),a.out.resolve())
