"""B5/B6 direct integer-node checks; no FFT, waveform study or hardware."""
import argparse
import ast
from decimal import Decimal,localcontext
from fractions import Fraction
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import sys
import numpy as np
from stream_das import StreamDAS

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def rne(n,d):return round(Fraction(int(n),int(d)))

def execute(repo,out):
    out.mkdir(parents=True,exist_ok=False)
    tasks=repo/'task-packages/PKG-B-ALG/tasks';source=tasks/'h3-complete-20260918/source/fixed_golden.py'
    expected=load(tasks/'h3-interface-review-20260918/checkpoint-20260923/dependencies.json')[source.relative_to(repo).as_posix()]
    assert sha(source)==expected
    sp=importlib.util.spec_from_file_location('b5_fixed',source);fixed=importlib.util.module_from_spec(sp);sys.modules[sp.name]=fixed;sp.loader.exec_module(fixed)
    fixed.fixed_fft=lambda *a,**k:(_ for _ in ()).throw(AssertionError('FFT forbidden'))
    limits={};lag_records=[];boundary=[]
    with localcontext() as ctx:
        ctx.prec=100
        for length in [1,2]:
            lim=int(Decimal(length).sqrt()*Decimal(1920*4096)/Decimal(343));limits[length]=lim
            assert lim==fixed.physical_limit_q12(length)
            for sign in [-1,1]:
                for delta in [-1,0,1]:
                    t=sign*(lim+delta);v=fixed.physical_tau_legal_q12(t,length);assert v==(delta<=0)
                    boundary.append(dict(length=length,tau=t,valid=v))
            search=math.ceil(Fraction(lim,4096));cases={}
            for value in [0,-100,100]:cases['flat_'+str(value)]=np.full(1024,value,dtype=np.int64)
            for peak in [-search,-1,0,1,search]:
                for left,right in [(0,0),(0,50),(50,0),(100,0),(0,100)]:
                    a=np.full(1024,-100,dtype=np.int64);a[peak%1024]=100;a[(peak-1)%1024]=left;a[(peak+1)%1024]=right
                    cases[f'peak_{peak}_{left}_{right}']=a
            for name,a in cases.items():
                lags=list(range(-search,search+1));values=[int(a[k%1024]) for k in lags];peak=lags[values.index(max(values))]
                l,c,r=[int(a[k%1024]) for k in [peak-1,peak,peak+1]];den=l-2*c+r
                delta=0 if den==0 else round(Fraction(l-r,2*den)*4096);delta=max(-2048,min(2048,delta));tau=peak*4096+delta
                got=fixed.lag_q12(a,length);assert (got['peak'],got['delta_q12'],got['tau_q12'],got['valid'])==(peak,delta,tau,abs(tau)<=lim)
                lag_records.append(dict(case=name,length=length,**got))
    # Enumerate all 64 validity masks using direct rational direction-delay inputs.
    directions=[(1,0),(-1,0),(0,1),(0,-1),(Fraction(1,2),Fraction(1,2)),(0,0)]
    doa_records=[]
    for ux,uy in directions:
        for bits in itertools.product([False,True],repeat=6):
            taus=[round((dx*ux+dy*uy)*Fraction(1920*4096,343)) for dx,dy in fixed.PAIR_DELTAS]
            rows=[dict(valid=v,tau_q12=t) for v,t in zip(bits,taus)];got=fixed.doa_q20(rows)
            if sum(bits)<3:assert got['reason']=='INSUFFICIENT_PAIRS';continue
            a=[fixed.PAIR_DELTAS[k] for k in range(6) if bits[k]];b=[taus[k] for k in range(6) if bits[k]]
            aa=sum(x*x for x,y in a);bb=sum(x*y for x,y in a);dd=sum(y*y for x,y in a)
            rhs0=sum(x*t for (x,y),t in zip(a,b));rhs1=sum(y*t for (x,y),t in zip(a,b))
            # Fraction Gaussian elimination, not the DUT's determinant/RNE routine.
            y=(Fraction(rhs1)-Fraction(bb*rhs0,aa))/(Fraction(dd)-Fraction(bb*bb,aa));x=(Fraction(rhs0)-bb*y)/aa
            ex=round(x*Fraction(343*256,1920));ey=round(y*Fraction(343*256,1920))
            assert (got['ux_q20'],got['uy_q20'])==(ex,ey)
            residual=sum((rne((dx*ex+dy*ey)*1920*4096,343*2**20)-t)**2 for (dx,dy),t in zip(a,b))
            norm=ex*ex+ey*ey;accepted=residual<=len(a)*2048**2 and round(Fraction(2**20,10))**2<=norm<=round(Fraction(13*2**20,10))**2
            assert got['residual_sum_square_q24']==residual and got['norm_square_q40']==norm and got['valid']==accepted
            doa_records.append(dict(mask=list(bits),xy=[str(ux),str(uy)],result=got))
    assert fixed.doa_q20([dict(valid=True,tau_q12=0)]*3,[(1,0)]*3)['reason']=='RANK_DEFICIENT'
    # Guard arithmetic equalities isolated from original AST, not claimed reachable frames.
    tree=ast.parse(source.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='doa_q20')
    tests=[n for n in fn.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ['residual_ok','norm_ok']]
    code=compile(ast.fix_missing_locations(ast.Module(body=tests,type_ignores=[])),'<doa-thresholds>','exec')
    guard_cases=0
    lower=round(Fraction(2**20,10))**2;upper=round(Fraction(13*2**20,10))**2
    for count in [3,6]:
        for residual in [count*2048**2-1,count*2048**2,count*2048**2+1]:
            for norm in [lower-1,lower,lower+1,upper-1,upper,upper+1]:
                env=dict(valid=[None]*count,residual_sq=residual,norm_sq=norm,FRAC_LAG=12,FRAC_DIR=20);exec(code,env)
                assert env['residual_ok']==(residual<=count*2048**2) and env['norm_ok']==(lower<=norm<=upper);guard_cases+=1
    corners=[]
    for bits in itertools.product([False,True],repeat=6):
        valid_indices=[k for k,v in enumerate(bits) if v]
        if len(valid_indices)<3:continue
        for signs in itertools.product([-1,1],repeat=len(valid_indices)):
            rows=[dict(valid=False) for _ in range(6)]
            for k,sign in zip(valid_indices,signs):rows[k]=dict(valid=True,tau_q12=sign*limits[fixed.PAIR_LENGTH_SQ[k]])
            got=fixed.doa_q20(rows)
            corners.append(dict(mask=list(bits),signs=list(signs),ux=got['ux_q20'],uy=got['uy_q20'],valid=got['valid']))
    extremes={axis:dict(min=min(r[axis] for r in corners),max=max(r[axis] for r in corners)) for axis in ['ux','uy']}
    outside_s22=[r for r in corners if any(not -2**21<=r[k]<2**21 for k in ['ux','uy'])]
    dump(out/'doa-corner-ranges.json',dict(corners=len(corners),extremes=extremes,outside_s22=outside_s22,
        note='Per-component LS is linear and RNE monotonic: corner extrema bound all individually legal pair-delay boxes for each subset. Not full intermediate-product proof.'))
    angles=[];small=[]
    for scale in [1,2**17,2**20]:
        for x,y in [(scale,0),(-scale,0),(0,scale),(0,-scale),(scale,scale),(-scale,scale),(-scale,-scale),(scale,-scale),(scale,scale//2)]:
            actual=fixed.atan2_q8(y,x);ideal=round(math.degrees(math.atan2(y,x))*256);error=abs((actual-ideal+180*256)%(360*256)-180*256)
            record=dict(x=x,y=y,actual=actual,ideal=ideal,error_codes=error)
            if scale==1:small.append(record)
            else:assert error<=1;angles.append(record)
    n=97;pcm=np.array([[(i*317+ch*1703)%20001-10000 for i in range(n)] for ch in range(4)],dtype=np.int64)
    streams=[];naive_mismatches=0;das_cases=0
    for delays in [[0]*4,[0,2048,-2048,4096],[32768,-32768,4095,-4095],fixed.delay_q12_from_angle(45*256)]:
        actual,info=fixed.das_block(pcm,delays);oracle=[]
        for i in range(n):
            value=Fraction(0)
            for ch,d in enumerate(delays):
                position=Fraction(i)-Fraction(d,4096);left=position.numerator//position.denominator;frac=position-left
                aa=int(pcm[ch,left]) if 0<=left<n else 0;bb=int(pcm[ch,left+1]) if 0<=left+1<n else 0
                value+=aa*(1-frac)+bb*frac
            oracle.append(round(value/4))
        assert np.array_equal(actual,oracle) and info['saturation_count']==0;das_cases+=1
        naive=np.concatenate([fixed.das_block(pcm[:,i:i+13],delays)[0] for i in range(0,n,13)])
        naive_mismatches+=int(np.count_nonzero(naive!=actual))
        for chunk in [1,7,13,64]:
            stream=StreamDAS(delays);parts=[]
            for i in range(0,n,chunk):parts.append(stream.push(pcm[:,i:i+chunk]))
            parts.append(stream.push(np.zeros((4,0),dtype=np.int64),final=True));joined=np.concatenate(parts)
            assert np.array_equal(joined,actual)
            streams.append(dict(delays=delays,chunk=chunk,samples=len(joined),lookahead=stream.lookahead,history=stream.history))
    for val in [-2**23,2**23-1]:
        a=np.full((4,17),val,dtype=np.int64);y,info=fixed.das_block(a,[0]*4);assert np.all(y==val) and info['saturation_count']==0;das_cases+=1
    illegal=np.full((4,17),2**23,dtype=np.int64);_,inf=fixed.das_block(illegal,[0]*4);assert inf['saturation_count']==17
    try:StreamDAS([0]*4).push(illegal)
    except ValueError:pass
    else:raise AssertionError('invalid PCM accepted')
    assert naive_mismatches>0
    rom={str(a):fixed.delay_q12_from_angle(a*256) for a in [-180,-90,-45,0,45,90,180]};dump(out/'delay-samples.json',rom)
    for a,want in [(0,[0,rne(1920*4096,343),rne(1920*4096,343),0]),(90,[0,0,rne(1920*4096,343),rne(1920*4096,343)])]:assert rom[str(a)]==want
    result=dict(status='B5_B6_NODE_PASS_WITH_UNINTEGRATED_STREAM_CANDIDATE',lag_cases=len(lag_records),physical_boundary_cases=len(boundary),doa_validity_masks=64,direction_inputs=6,doa_numerical_cases=len(doa_records),guard_cases=guard_cases,doa_corner_cases=len(corners),doa_xy_extremes=extremes,doa_corners_outside_s22=len(outside_s22),cordic_valid_scale_cases=len(angles),cordic_small_input_gaps=[r for r in small if r['error_codes']>1],das_cases=das_cases,stream_cases=len(streams),naive_split_mismatches=naive_mismatches,illegal_pcm_legacy_saturated=17,source_sha256=sha(source),fft_calls=0,hardware_tested=False,variable_direction_stream_tested=False)
    for name,value in [('result',result),('lag-cases',lag_records),('physical-boundaries',boundary),('doa-cases',doa_records),('cordic-cases',angles+small),('stream-cases',streams)]:dump(out/(name+'.json'),value)
    dump(out/'OUTPUT-SHA256.json',{p.name:sha(p) for p in out.iterdir() if p.is_file()});print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();execute(a.repo.resolve(),a.out.resolve())
