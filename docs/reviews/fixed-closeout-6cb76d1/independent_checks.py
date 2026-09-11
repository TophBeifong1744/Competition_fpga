"""Independent archive/array/strata audit; does not import B analysis or chain."""
import argparse
from collections import Counter
import csv
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path
import subprocess
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('--repo', type=Path, required=True)
ap.add_argument('--analysis', type=Path, required=True)
ap.add_argument('--out', type=Path, required=True)
a = ap.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
task = a.repo/'task-packages/PKG-B-ALG/tasks/phat-fixed-03'
package = task/'closeout-01'
archive = task/'dynamic-range/evidence/run01'
sha = lambda b: hashlib.sha256(b).hexdigest()
packing = json.loads((archive/'packing.json').read_text())
compressed = (archive/'frames.json.gz').read_bytes()
raw = gzip.decompress(compressed)
assert (len(compressed), sha(compressed)) == (packing['compressed_bytes'], packing['compressed_sha256'])
assert (len(raw), sha(raw)) == (packing['original_bytes'], packing['original_sha256'])
frames = json.loads(raw)
del raw
assert len(frames) == 196 and [f['case'] for f in frames] == list(range(196))
protocol = json.loads((task/'dynamic-range/protocol.json').read_text())
assert set((f['seed'],f['az'],f['el'],f['scenario'],f['peak_exponent']) for f in frames[:192]) == set(
    (s,az,el,sc,e) for s in protocol['seeds'] for az,el in protocol['directions']
    for sc in protocol['scenarios'] for e in range(1,25))

pos = np.array([[-.02,-.02,0],[.02,-.02,0],[.02,.02,0],[-.02,.02,0],
                [0,0,np.sqrt(2)*.02],[0,0,-np.sqrt(2)*.02]])
pairs = list(itertools.combinations(range(6), 2))
bounds = [float(np.linalg.norm(pos[i]-pos[j])*48000/343) for i,j in pairs]
band = np.zeros(513, dtype=bool)
band[7:86] = True
coeff = np.rint(np.hanning(1024)*2**17).astype(np.int64)

def rne(n, d):
    sign = -1 if n < 0 else 1
    q, r = divmod(abs(int(n)), int(d))
    return sign*(q + (2*r>d or (2*r==d and q%2==1)))

def estimate(corr, bound, integer=False):
    lags = list(range(-math.ceil(bound), math.ceil(bound)+1))
    lag = lags[int(np.argmax([corr[k%1024] for k in lags]))]
    lo, mid, hi = [int(corr[k%1024]) if integer else float(corr[k%1024]) for k in (lag-1,lag,lag+1)]
    curvature = lo-2*mid+hi
    if integer:
        frac = rne((hi-lo)*2048, -curvature) if curvature < 0 else 0
        tau = lag + max(-2048,min(2048,frac))/4096
    else:
        frac = .5*(lo-hi)/curvature if curvature < -1e-15 else 0
        tau = lag + max(-.5,min(.5,frac))
    return dict(peak=lag, tau_samples=tau, valid=abs(tau)<=bound+.05)

def floating(windowed):
    spec = np.fft.rfft(windowed, axis=1)
    result = []
    for k,(i,j) in enumerate(pairs):
        cross = spec[i]*spec[j].conj()
        mag = np.abs(cross)
        mask = band & (mag >= .02*max(float(mag[band].max()),1e-15))
        p = dict(valid=False,mask=mask.tolist())
        if mask.sum()>=12:
            corr = np.fft.irfft(np.where(mask,cross/np.maximum(mag,1e-15),0),n=1024)
            p.update(estimate(corr,bounds[k]))
        result.append(p)
    return result

def verify_float(actual, old):
    for x,y in zip(actual,old,strict=True):
        assert x['mask']==y['mask'] and x['valid']==y['valid']
        if 'peak' in x:
            assert x['peak']==y['peak']
            assert abs(x['tau_samples']-y['tau_samples'])<=1e-12

records=[]
stress=[]
windows={}
integer_counts=Counter()
for f in frames:
    path=archive/f['npz']
    assert sha(path.read_bytes()) == f['npz_sha256']
    with np.load(path,allow_pickle=False) as z:
        assert len(z.files)==19
        pcm=z['pcm']; win=z['windowed']; inp=z['input_float']
        assert pcm.shape==win.shape==inp.shape==(6,1024)
        assert np.array_equal(pcm,np.clip(np.rint(inp*2**23),-2**23,2**23-1))
        expected=np.array([rne(int(v)*int(c),2**17) for row in pcm for v,c in zip(row,coeff)],dtype=np.int64).reshape(6,1024)
        assert np.array_equal(win,expected)
        integer_counts['PCM_window_components']+=pcm.size+win.size
        verify_float(floating(inp*np.hanning(1024)),f['float_pairs'])
        verify_float(floating(pcm/2**23*np.hanning(1024)),f['pcm_float_pairs'])
        wp=floating(win/2**23)
        assert [p['mask'] for p in wp]==f['integer_window_float_masks']
        if f['peak_exponent'] in (21,22,23,24):
            windows.setdefault(f['peak_exponent'],[]).extend(wp)
        for name,c in f['candidates'].items():
            rawfft=z[name+'_raw_fft']; packed=z[name+'_packed_fft']
            assert rawfft.shape==packed.shape==(6,1024,2)
            shift=c['common_right_shift']
            expected=np.array([rne(v,2**shift) for v in rawfft.flat],dtype=np.int64).reshape(rawfft.shape)
            assert np.array_equal(packed,expected)
            assert packed.min()>=-2**24 and packed.max()<2**24
            if shift:
                prev=np.array([rne(v,2**(shift-1)) for v in rawfft.flat])
                assert prev.min()<-2**24 or prev.max()>=2**24
            integer_counts['packing_components']+=packed.size
            overflow=any(c['flags']['fft_overflow'])
            for k,(i,j) in enumerate(pairs):
                p=c['pairs'][k]; ref=f['float_pairs'][k]
                aa=packed[i,:513].astype(object); bb=packed[j,:513].astype(object)
                re=aa[:,0]*bb[:,0]+aa[:,1]*bb[:,1]
                im=aa[:,1]*bb[:,0]-aa[:,0]*bb[:,1]
                power=re*re+im*im
                mask=band & (power>0) & (power*2500>=max(power[7:86]))
                if overflow: mask[:]=False
                assert mask.tolist()==p['mask']
                if mask.sum()<12 or any(c['flags']['ifft_overflow']):
                    assert not p['valid']
                else:
                    e=estimate(z[name+'_ifft'][k,:,0],bounds[k],True)
                    assert e['valid']==p['valid'] and e['peak']==p['peak'] and e['tau_samples']==p['tau_samples']
                    assert e['tau_samples']*4096==p['tau_q12']
                assert not np.any(z[name+'_phat'][k][~mask])
                both=ref['valid'] and p['valid']
                records.append(dict(candidate=name,case=f['case'],seed=f['seed'],scenario=f['scenario'],az=f['az'],el=f['el'],
                    peak_exponent=f['peak_exponent'], pair=k, fv=ref['valid'],cv=p['valid'],
                    delta=p['tau_samples']-ref['tau_samples'] if both else None,
                    peak_changed=ref['peak']!=p['peak'] if both else None,
                    mask_changed=sum(x!=y for x,y in zip(ref['mask'],p['mask']))))
            if f['peak_exponent'] is None:
                stress.append(dict(case=f['case'],scenario=f['scenario'],candidate=name,
                    float_valid=sum(p['valid'] for p in f['float_pairs']),fixed_valid=sum(p['valid'] for p in c['pairs']),
                    overflow_channels=sum(c['flags']['fft_overflow'])))
    if f['case']%32==0: print('independently checked case',f['case'],flush=True)
assert len(records)==11760
groups=json.loads((package/'evidence/run01/strata.json').read_text())
for g in groups:
    dims=g['stratum'].split('/')
    rr=[r for r in records if all(r[d]==g[d] for d in dims)]
    values=sorted(abs(r['delta']) for r in rr if r['delta'] is not None)
    assert len(rr)==g['pairs'] and len({r['case'] for r in rr})==g['frames']
    assert sum(r['fv'] for r in rr)==g['float_valid'] and sum(r['cv'] for r in rr)==g['fixed_valid']
    assert sum(r['fv'] and not r['cv'] for r in rr)==g['lost_valid']
    assert sum(not r['fv'] and r['cv'] for r in rr)==g['newly_valid']
    assert sum(r['peak_changed'] is True for r in rr)==g['peak_changed']
    assert sum(r['mask_changed'] for r in rr)==g['mask_changed']
    assert len(values)==g['n']
    def percentile(p):
        if not values:return None
        index=(len(values)-1)*p; left=math.floor(index); right=math.ceil(index)
        return values[left]+(values[right]-values[left])*(index-left)
    for key,q in [('median',.5),('p95',.95),('p99',.99),('maximum',1)]:
        got=percentile(q)
        assert (got is None and g[key] is None) or (got is not None and abs(got-g[key])<1e-12), (g,key,got)
    for threshold in (.001,.01,.1,.5,1.):
        assert sum(v>threshold for v in values)==g[f'gt_{threshold}']
    assert g['pairs']==g['frames']*15
amps=[g for g in groups if g['stratum']=='candidate/peak_exponent']
assert len(amps)==96 and all(g['pairs']==120 and g['frames']==8 for g in amps)
tails=sorted((r for r in records if r['delta'] is not None and r['peak_exponent'] is not None),key=lambda r:abs(r['delta']),reverse=True)[:30]
oldtails=json.loads((package/'evidence/run01/tail-cases.json').read_text())
for x,y in zip(tails,oldtails,strict=True):
    for k in ('case','candidate','pair','delta'):assert x[k]==y[k]
for g in json.loads((package/'evidence/run01/research-lines.json').read_text()):
    last=0
    for e in range(1,25):
        v=next(v for v in amps if v['candidate']==g['candidate'] and v['peak_exponent']==e)
        if v['n']!=120 or v['maximum']>g['research_line_samples']:break
        last=e
    assert last==g['contiguous_tested_prefix_from_2_minus_1_to_exponent']

# Compare output bytes separately from parsed values. No tolerance is applied to bool/int/string fields.
comparison=[]
for p in sorted((package/'evidence/run01').iterdir()):
    q=a.analysis/p.name
    byte_equal=p.read_bytes()==q.read_bytes()
    if p.name=='verification.json':
        x=json.loads(p.read_text()); y=json.loads(q.read_text())
        ignored=['python','numpy','output_hashes']
        value_equal={k:v for k,v in x.items() if k not in ignored}=={k:v for k,v in y.items() if k not in ignored}
    elif p.suffix=='.json':value_equal=json.loads(p.read_text())==json.loads(q.read_text())
    else:
        with p.open(newline='') as fx,q.open(newline='') as fy:value_equal=list(csv.DictReader(fx))==list(csv.DictReader(fy))
    assert value_equal, p.name
    comparison.append(dict(file=p.name,byte_equal=byte_equal,parsed_equal=value_equal,
                           historical_sha256=sha(p.read_bytes()),rerun_sha256=sha(q.read_bytes())))

budget=dict(external_memory_bytes=sum([49152,4096,4096,49152,24624,8208,8208,513,16,16384,1024,240]),
            window_multiplies=6*1024,transforms=6+15,transform_samples=21*1024,
            full_cross_bins=15*513,full_cross_real_multiplies=4*15*513,
            band_bins=15*79,peak_bins=sum(2*math.ceil(b)+1 for b in bounds),
            peak_comparisons=sum(2*math.ceil(b) for b in bounds))
assert budget['external_memory_bytes']==165713 and budget['peak_bins']==207 and budget['peak_comparisons']==192
summary=dict(status='PASS_INDEPENDENT_ARCHIVE_ARRAY_AND_STATISTICAL_AUDIT_ONLY',frames=196,configuration_results=784,
             pair_results=11760,amplitude_groups=96,joint_strata=len(groups),integer_checks=dict(integer_counts),
             archive=packing,windows={e:dict(total=len(w),enough_bins=sum(sum(p['mask'])>=12 for p in w),
                       valid=sum(p['valid'] for p in w)) for e,w in windows.items()},
             wide29_e20=next(g for g in amps if g['candidate']=='wide29' and g['peak_exponent']==20),
             stress=stress,worst=oldtails[0],budget=budget,rerun_comparison=comparison,
             limits='No vendor model/RTL rerun. Mask and Q12 derived from archived integer arrays; PHAT normalization and IFFT transform not recomputed. Research only.')
(a.out/'independent.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
