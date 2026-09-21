"""Top-three local peaks, graph consistency before unchanged plane rejection."""
import argparse
import hashlib
from itertools import product
import json
from pathlib import Path
import numpy as np

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def options(pair):
    if not pair['valid']:return []
    lags=pair['legal_search_lags'];curve=pair['correlation']
    candidates=[dict(lag=pair['peak'],tau=pair['tau_samples'],score=pair['peak_height'],original=True)]
    for k in range(1,len(lags)-1):
        if lags[k]==pair['peak']:continue
        a,b,c=curve[k-1:k+2]
        if not (b>a and b>=c):continue
        denominator=a-2*b+c
        delta=0 if denominator==0 else float(np.clip(.5*(a-c)/denominator,-.5,.5))
        tau=lags[k]+delta
        if abs(tau)>pair['bound_samples']:continue
        candidates.append(dict(lag=lags[k],tau=tau,score=b,original=False))
    return sorted(candidates,key=lambda r:(-r['score'],r['lag']))[:3]

def probe(row):
    good=[p for p in row['pairs'] if p['valid']]
    if len(good)<3:return dict(status='INSUFFICIENT_PAIRS',valid=False,changed=False)
    g=np.zeros((len(good),4));xy=np.array([[0,0],[1,0],[1,1],[0,1]])*1920/343
    for k,p in enumerate(good):i,j=p['pair'];g[k,i]=-1;g[k,j]=1
    matrix=g@xy
    if np.linalg.matrix_rank(matrix)<2:return dict(status='RANK',valid=False,changed=False)
    choices=[options(p) for p in good];combinations=list(product(*choices))
    tau=np.array([[p['tau'] for p in c] for c in combinations])
    graph_fit=tau@np.linalg.pinv(g[:,1:]).T@g[:,1:].T
    rms=np.sqrt(np.mean((tau-graph_fit)**2,axis=1));allowed=np.flatnonzero(rms<=.5)
    common=dict(combinations=len(combinations),alternatives=sum(len(c)-1 for c in choices),original_cycle_rms=float(np.sqrt(np.mean((np.array([p['tau_samples'] for p in good])@(np.eye(len(good))-g[:,1:]@np.linalg.pinv(g[:,1:])).T)**2))))
    if not len(allowed):return dict(**common,status='NO_GRAPH_CONSISTENT_COMBINATION',valid=False,changed=False)
    scores=np.array([sum(p['score'] for p in c)/len(c) for c in combinations]);best=allowed[np.argmax(scores[allowed])]
    if sum(scores[i]==scores[best] for i in allowed)>1:return dict(**common,status='EXACT_SCORE_TIE',valid=False,changed=False)
    selected=tau[best];u=np.linalg.lstsq(matrix,selected,rcond=None)[0]
    residual=float(np.sqrt(np.mean((matrix@u-selected)**2)));norm=float(np.linalg.norm(u));valid=residual<=.5 and .1<=norm<=1.3
    return dict(**common,status='VALID' if valid else 'PLANE_REJECT',valid=valid,changed=any(not p['original'] for p in combinations[best]),changed_pairs=sum(not p['original'] for p in combinations[best]),selected=selected.tolist(),cycle_rms=float(rms[best]),residual=residual,norm=norm,angle=float(np.degrees(np.arctan2(u[1],u[0]))) if valid else None)

def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    root=a.repo/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918';path=root/'closeout-0918-20260921/acoustic/pairs01/frames.json'
    assert sha(path)==load(root/'checkpoint-20260923/SNAPSHOT-SHA256.json')['files'][path.relative_to(root).as_posix()]
    protocol=dict(top_k=3,secondary_peaks='interior local maxima only; preserve original peak/subsample code',graph_rms_max=.5,geometry='fixed 40mm square',score='mean original peak heights, before plane/norm/cone decisions',unchanged_plane_rms=.5,unchanged_norm=[.1,1.3],selection='frozen 320 selected frames, no background coverage, no independent validation',no_acoustic_acceptance=True)
    dump(a.out/'protocol.json',protocol)
    rows=[]
    for row in load(path):
        result=probe(row);old=row['projection'].get('advisory_consistent',False)
        if result.get('valid') and not result.get('changed'):
            assert old
            assert np.isclose(result['angle'],row['projection']['advisory_azimuth_deg'],atol=1e-10,rtol=1e-12)
        rows.append(dict(capture=row['capture'],start=row['start'],marker_excluded=row['marker_excluded'],anchor=row['anchor'],old_valid=old,result=result))
    from collections import Counter
    summary=dict(frames=len(rows),statuses=dict(Counter(r['result']['status'] for r in rows)),changed_frames=sum(r['result']['changed'] for r in rows),old_valid=sum(r['old_valid'] for r in rows),new_valid=sum(r['result']['valid'] for r in rows),newly_accepted=sum(not r['old_valid'] and r['result']['valid'] for r in rows),lost=sum(r['old_valid'] and not r['result']['valid'] for r in rows),zero_secondary_frames=sum(r['result'].get('alternatives')==0 for r in rows),input_sha256=sha(path),source_sha256=sha(Path(__file__)),fft_calls=0,scope=protocol['selection'])
    dump(a.out/'frames.json',rows);dump(a.out/'result.json',summary);print(summary)

if __name__=='__main__':main()
