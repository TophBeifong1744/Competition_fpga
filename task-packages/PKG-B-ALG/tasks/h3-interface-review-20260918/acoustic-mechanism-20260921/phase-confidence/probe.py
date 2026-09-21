"""Single-frame phase closure is tautological; delay-model fit is diagnostic."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
PAIRS=((0,1),(0,2),(0,3),(1,2),(1,3),(2,3))

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def fit_score(unit,bins,tau,weights):
    matched=np.real(unit*np.exp(2j*np.pi*np.asarray(tau)[:,None]*bins[None,:]/1024))
    return dict(unweighted=float(matched.mean()),weighted=float(np.sum(matched*weights)/(len(tau)*weights.sum())))

def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    root=a.repo/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918';cp=root/'checkpoint-20260923';seal=load(cp/'SNAPSHOT-SHA256.json')['files'];pins={}
    def frozen(p):
        h=sha(p);assert h==seal[p.relative_to(root).as_posix()];pins[p.relative_to(a.repo).as_posix()]=h;return load(p)
    prior=frozen(root/'acoustic-mechanism-20260921/frequency-diagnostic/run01/frames.json');summary=frozen(cp/'evidence/run01/summary.json')
    protocol=dict(selection='same320 selected target +1122 background',band=[7,85],mask='original per-pair2percent, intersection across all six pairs',minimum_common_bins_for_score=12,weight='min across pairs of amplitude / each pair full-band maximum',scores=['zero_delay','graph_arrival_fit','plane_fit'],threshold_tuning=False,one_frame_closure='algebraic identity, never acceptance evidence',new_audio=False)
    dump(a.out/'protocol.json',protocol)
    g=np.zeros((6,4))
    for k,(i,j) in enumerate(PAIRS):g[k,i]=-1;g[k,j]=1
    xy=np.array([[0,0],[1,0],[1,1],[0,1]])*1920/343;plane=g@xy;output=[];max_closure=0.;transforms=0
    for name in sorted(set(r['capture'] for r in prior)):
        raw=next(p for p in summary['pins'] if p.endswith('/'+name+'/raw.bin'));assert sha(a.repo/raw)==summary['pins'][raw];pins[raw]=sha(a.repo/raw)
        pcm=np.fromfile(a.repo/raw,dtype='<u4').reshape(-1,8)[:,2:6].view('<i4')
        for r in [r for r in prior if r['capture']==name]:
            start=r['start'];sp=np.fft.rfft(pcm[start:start+1024].T/2**23*np.hanning(1024),axis=1);transforms+=4
            z=np.array([sp[i]*sp[j].conj() for i,j in PAIRS]);amp=np.abs(z);maxima=amp[:,7:86].max(axis=1)
            active=np.zeros((6,513),dtype=bool);active[:,7:86]=amp[:,7:86]>=.02*np.maximum(maxima[:,None],1e-15)
            assert active.sum(axis=1).tolist()==r['variants']['full']['retained_bins']
            bins=np.flatnonzero(np.all(active,axis=0));unit=z[:,bins]/np.maximum(amp[:,bins],1e-15)
            # Four oriented graph triangles. Near-zero closure is automatic.
            err=max((float(np.max(np.abs(unit[i]*unit[j]*unit[k].conj()-1))) for i,j,k in ((0,3,1),(0,4,2),(1,5,2),(3,5,4))),default=0.) if len(bins) else 0.
            max_closure=max(max_closure,err);assert err<1e-10
            full=r['variants']['full'];valid=np.array([reason=='VALID' for reason in full['pair_reasons']]);record=dict(capture=name,start=start,background=r['background'],marker_excluded=r['marker_excluded'],gate=r['gate'],original_valid=full['valid'],original_cycle=full['cycle'],original_norm=full['norm'],common_bins=len(bins),scores=None)
            if len(bins)>=12 and valid.sum()>=3 and np.linalg.matrix_rank(plane[valid])==2:
                tau=np.array([t for t,keep in zip(full['taus'],valid) if keep]);arrival=np.linalg.lstsq(g[valid,1:],tau,rcond=None)[0];u=np.linalg.lstsq(plane[valid],tau,rcond=None)[0]
                assert np.isclose(np.linalg.norm(u),full['norm'],atol=1e-10,rtol=1e-12)
                weights=np.min(amp[:,bins]/np.maximum(maxima[:,None],1e-15),axis=0);assert np.all(weights>0)
                models=dict(zero_delay=np.zeros(6),graph_arrival_fit=g[:,1:]@arrival,plane_fit=plane@u)
                record['scores']={key:fit_score(unit,bins,delay,weights) for key,delay in models.items()}
                record['effective_weight_bins']=float(weights.sum()**2/np.sum(weights**2))
                record['graph_minus_zero']=record['scores']['graph_arrival_fit']['unweighted']-record['scores']['zero_delay']['unweighted']
            output.append(record)
    groups={}
    for label,select in [('background',lambda r:r['background']),('target_nonmarker_valid',lambda r:not r['background'] and not r['marker_excluded'] and r['original_valid']),('target_nonmarker_cycle_fail',lambda r:not r['background'] and not r['marker_excluded'] and r['original_cycle'] is not None and r['original_cycle']>.5)]:
        allrows=[r for r in output if select(r)];rows=[r for r in allrows if r['scores'] is not None];stats={}
        for model in protocol['scores']:
            for metric in ('unweighted','weighted'):
                vals=[r['scores'][model][metric] for r in rows];stats[model+'_'+metric]=None if not vals else dict(zip(('p05','p50','p95'),map(float,np.percentile(vals,[5,50,95]))))
        vals=[r['graph_minus_zero'] for r in rows];groups[label]=dict(total=len(allrows),scored=len(rows),insufficient=len(allrows)-len(rows),scores=stats,graph_minus_zero_median=None if not vals else float(np.median(vals)))
    dump(a.out/'frames.json',output);dump(a.out/'result.json',dict(protocol=protocol,pins=pins,source_sha256=sha(Path(__file__)),fft_calls=transforms,ifft_calls=0,max_triangle_identity_error=max_closure,groups=groups,no_candidate_adopted=True));print(json.dumps(groups,indent=2))
if __name__=='__main__':main()
