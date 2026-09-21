"""Conservative integer interval proof for fixed geometry/custom nodes.

Intervals include dependencies independently: valid over-approximations, not
minimal hardware widths. No substitution of sampled maxima for domain bounds.
"""
import argparse
from itertools import combinations
from math import isqrt
import json
from pathlib import Path

TABLE={}


def add(a,b):return a[0]+b[0],a[1]+b[1]
def neg(a):return -a[1],-a[0]
def sub(a,b):return add(a,neg(b))
def mul(a,b):
    v=[x*y for x in a for y in b];return min(v),max(v)
def const(v):return v,v
def scale(a,b):return mul(a,const(b))
def rne(n,d):
    q,r=divmod(n,d);return q+int(2*r>d or (2*r==d and q%2))
def divide(a,d):return rne(a[0],d),rne(a[1],d)
def square(a):return (0 if a[0]<=0<=a[1] else min(a[0]**2,a[1]**2)),max(a[0]**2,a[1]**2)
def record(name,a):
    current=a
    if name in TABLE:a=min(TABLE[name][0],a[0]),max(TABLE[name][1],a[1])
    TABLE[name]=a;return current
def signed(w):return -(1<<(w-1)),(1<<(w-1))-1


def derive():
    pcm=signed(24);window=(0,1<<17)
    record('window.doa_product',mul(pcm,window))
    record('gate.sum',scale(pcm,1024))
    center=record('gate.center',sub(pcm,pcm))
    record('gate.window_product',mul(center,window))
    for bits in (25,29):
        x=signed(bits);tw=(-(1<<30),1<<30)
        product=record(f'fft{bits}.scalar_product',mul(x,tw))
        complex_product=record(f'fft{bits}.complex_product_sum',add(product,product))
        v=record(f'fft{bits}.rotated',divide(complex_product,1<<30))
        butterfly=record(f'fft{bits}.butterfly_pre_shift',add(x,v))
        record(f'fft{bits}.pre_saturate',divide(butterfly,2))
    fft=signed(25)
    sum_power=record('gate.sum_power',scale(square(fft),132))
    record('gate.power_numerator',scale(sum_power,1<<45))
    record('gate.on_threshold',scale((0,2**64-1),4))
    # PHAT retains original conservative S51 cross container domain.
    cross=signed(51)
    sq=record('phat.square',scale(square(cross),2))
    record('phat.mask_product',scale(sq,2500))
    radicand=record('phat.sqrt_input',scale(sq,1<<48))
    record('phat.sqrt_compare_4n',scale(radicand,4))
    maximum_root=isqrt(radicand[1])+1
    record('phat.sqrt_compare_odd_square',(1,(2*maximum_root+1)**2))
    record('phat.magnitude',(1<<24,maximum_root))
    reciprocal_ranges=[]
    for k in range(256):
        m=(2**30+k*2**22,2**30+(k+1)*2**22-(0 if k==255 else 1))
        r=const(rne(2**30*512,513+2*k))
        for stage in range(2):
            mr_prod=record(f'phat.newton{stage}.mr_product',mul(m,r))
            mr=record(f'phat.newton{stage}.mr',divide(mr_prod,2**30))
            factor=record(f'phat.newton{stage}.factor',sub(const(2**31),mr))
            assert factor[0]>0
            prod=record(f'phat.newton{stage}.update_product',mul(r,factor))
            r=record(f'phat.newton{stage}.reciprocal',divide(prod,2**30))
        reciprocal_ranges.append(r)
    reciprocal=(min(x[0] for x in reciprocal_ranges),max(x[1] for x in reciprocal_ranges))
    record('phat.normalize_product',mul(cross,reciprocal))
    # Correlation container domain; delta is explicitly clamped after division.
    corr=signed(25)
    record('lag.denominator',sub(add(corr,corr),scale(corr,2)))
    numerator=record('lag.numerator',scale(sub(corr,corr),2**11))
    record('lag.unclamped_delta',numerator) # smallest nonzero positive denominator 1
    record('lag.tau_before_physical_guard',(-8*4096-2048,8*4096+2048))
    record('lag.margin_numerator',scale(sub(corr,corr),2**15))
    record('lag.margin_output',(0,(2**25-1)*2**15))
    geometry=((1,0),(1,1),(0,1),(0,1),(-1,1),(-1,0))
    subsets=0
    for count in range(3,7):
        for ids in combinations(range(6),count):
            subsets+=1;g=[geometry[i] for i in ids]
            limits=[isqrt((1920**2*(dx*dx+dy*dy)*4096**2)//343**2) for dx,dy in g]
            taus=[(-v,v) for v in limits]
            sxx=sum(dx*dx for dx,dy in g);syy=sum(dy*dy for dx,dy in g);sxy=sum(dx*dy for dx,dy in g)
            for name,val in [('sxx',sxx),('syy',syy),('sxy',sxy)]:record('doa.'+name,const(val))
            det=sxx*syy-sxy*sxy;assert det>0
            record('doa.det_products',(0,max(sxx*syy,sxy*sxy)));record('doa.det',const(det))
            bx=(0,0);by=(0,0)
            for (dx,dy),tau in zip(g,taus):bx=add(bx,scale(tau,dx));by=add(by,scale(tau,dy))
            record('doa.bx_by',bx);record('doa.bx_by',by)
            # Symbolically combine coefficients before intervals for exact linear LS ranges.
            nx=(0,0);ny=(0,0)
            for (dx,dy),tau in zip(g,taus):
                nx=add(nx,scale(tau,syy*dx-sxy*dy));ny=add(ny,scale(tau,sxx*dy-sxy*dx))
            for v in (scale(bx,syy),scale(by,sxy),scale(by,sxx),scale(bx,sxy)):record('doa.ls_term_product',v)
            for v in (nx,ny):record('doa.ls_difference',v)
            ux=divide(record('doa.ls_scaled_numerator',scale(nx,343*256)),det*1920)
            uy=divide(record('doa.ls_scaled_numerator',scale(ny,343*256)),det*1920)
            record('doa.denominator',const(det*1920));record('doa.xy_pre_guard',ux);record('doa.xy_pre_guard',uy)
            residual=(0,0)
            for (dx,dy),tau in zip(g,taus):
                dot=record('doa.predicted_dot',add(scale(ux,dx),scale(uy,dy)))
                num=record('doa.predicted_numerator',scale(dot,1920*4096))
                predicted=record('doa.predicted',divide(num,343*2**20))
                difference=record('doa.residual_difference',sub(predicted,tau))
                residual=add(residual,square(difference))
            record('doa.residual_sum_square',residual)
            record('doa.norm_square',add(square(ux),square(uy)))
    xy=max(abs(x) for x in TABLE['doa.xy_pre_guard'])
    # Both updates bounded by M + ceil(M/2**i); includes arithmetic shift error.
    bound=xy
    cordic=[]
    for i in range(24):
        bound+= (bound+(1<<i)-1)//(1<<i)
        cordic.append(bound)
    record('cordic.xy_all_iterations',(-bound,bound))
    # i=0 is 45 degrees; for i>=1, atan(z)<=z and 180/pi<60.
    # Sum 2^-i < 1; 24 units conservatively cover all table rounding errors.
    angle_bound=(45+60+180)*65536+24
    record('cordic.angle_plus_offset',(-angle_bound,angle_bound))
    record('cordic.angle_output',divide((-angle_bound,angle_bound),256))
    # Convex weights allow tighter accumulator than unrelated product bounds.
    record('das.channel_weighted_sum',scale(pcm,4096))
    record('das.four_channel_sum',scale(pcm,4*4096))
    record('das.fade_sum',scale(pcm,4096))
    record('das.fade_alpha_numerator',(0,480*4096))
    assert TABLE['doa.xy_pre_guard']==(-2531477,2531477)
    return subsets,cordic


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    subsets,cordic=derive();rows=[]
    for name,(lo,hi) in TABLE.items():
        width=1
        while lo<-(1<<(width-1)) or hi>=(1<<(width-1)):width+=1
        unsigned=None if lo<0 else max(1,hi.bit_length())
        rows.append(dict(node=name,minimum=lo,maximum=hi,signed_bits=width,unsigned_bits=unsigned))
    (a.out/'widths.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    (a.out/'widths.md').write_text('| Node | Min | Max | Signed bits | Unsigned bits |\n|---|---:|---:|---:|---:|\n'+''.join(f"| {r['node']} | {r['minimum']} | {r['maximum']} | {r['signed_bits']} | {r['unsigned_bits']} |\n" for r in rows),encoding='utf-8')
    result=dict(status='CONSERVATIVE_DOMAIN_BOUNDS',nodes=len(rows),geometry_subsets=subsets,cordic_iteration_abs_bounds=cordic,proof='integer interval inclusion and linear symbolic LS coefficients; not sampled maxima',limits='fixed square geometry, legal Q12 tau, declared PCM/spectrum domains; no IP internals, divider implementation, counters or hardware cost proof')
    (a.out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(result)


if __name__=='__main__':main()
