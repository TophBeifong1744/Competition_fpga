"""Nested graph/geometry least-squares: delay consistency lower bound."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    root=a.repo/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918'
    path=root/'closeout-0918-20260921/acoustic/pairs01/frames.json'
    assert sha(path)==load(root/'checkpoint-20260923/SNAPSHOT-SHA256.json')['files'][path.relative_to(root).as_posix()]
    xy=np.array([[0,0],[1,0],[1,1],[0,1]],dtype=float)*1920/343
    # Pure algebra negative controls, not synthetic acoustic recordings.
    all_graph=np.zeros((6,4))
    for k,(i,j) in enumerate(((0,1),(0,2),(0,3),(1,2),(1,3),(2,3))):all_graph[k,i]=-1;all_graph[k,j]=1
    def residual(matrix,t):return float(np.mean((t-matrix@np.linalg.lstsq(matrix,t,rcond=None)[0])**2))
    realizable=all_graph@xy@np.array([.5,.25])
    assert residual(all_graph[:,1:],realizable)<1e-20 and residual(all_graph@xy,realizable)<1e-20
    nonplanar=all_graph@np.array([1,-1,1,-1])
    assert residual(all_graph[:,1:],nonplanar)<1e-20 and residual(all_graph@xy,nonplanar)>.25
    inconsistent=np.array([1,-1,0,1,0,0.])
    assert np.allclose(all_graph.T@inconsistent,0)
    assert np.isclose(residual(all_graph[:,1:],inconsistent),.5)
    assert residual(all_graph[:3,1:],np.array([1,2,4.]))<1e-20
    reports=[]
    for row in load(path):
        pairs=[p for p in row['pairs'] if p['valid']]
        if len(pairs)<3:continue
        graph=np.zeros((len(pairs),4));tau=[]
        for k,pair in enumerate(pairs):
            i,j=pair['pair'];graph[k,i]=-1;graph[k,j]=1;tau.append(pair['tau_samples'])
        tau=np.array(tau);plane=graph@xy
        arrival,_,rank,_=np.linalg.lstsq(graph[:,1:],tau,rcond=None)
        u,_,plane_rank,_=np.linalg.lstsq(plane,tau,rcond=None)
        if plane_rank<2:continue
        fitted_graph=graph[:,1:]@arrival;fitted_plane=plane@u
        cycle=float(np.mean((tau-fitted_graph)**2));extra=float(np.mean((fitted_graph-fitted_plane)**2));total=float(np.mean((tau-fitted_plane)**2))
        assert np.isclose(total,cycle+extra,rtol=1e-12,atol=1e-12)
        assert np.isclose(np.sqrt(total),row['projection']['residual_samples'],rtol=1e-12,atol=1e-10)
        offset=np.array([0,.25,-.5,.75]);shifted=tau+graph@offset
        fitted_shift=graph[:,1:]@np.linalg.lstsq(graph[:,1:],shifted,rcond=None)[0]
        assert np.isclose(float(np.mean((shifted-fitted_shift)**2)),cycle,rtol=1e-12,atol=1e-12)
        reports.append(dict(capture=row['capture'],start=row['start'],marker_excluded=row['marker_excluded'],anchor=row['anchor'],valid_pairs=len(pairs),graph_rank=int(rank),cycle_degrees=len(pairs)-int(rank),cycle_rms=float(np.sqrt(cycle)),extra_planar_rms=float(np.sqrt(extra)),original_residual=float(np.sqrt(total)),original_residual_reject=total>.25,any_arrival_model_residual_reject=cycle>.25))
    counts={}
    for group,rows in [('selected_all',reports),('selected_nonmarker',[r for r in reports if not r['marker_excluded']]),('selected_acquisition',[r for r in reports if r['anchor']])]:
        counts[group]=dict(frames=len(rows),original_residual_reject=sum(r['original_residual_reject'] for r in rows),cycle_lower_bound_reject=sum(r['any_arrival_model_residual_reject'] for r in rows),cycle_not_exercised=sum(r['cycle_degrees']==0 for r in rows))
    result=dict(input_sha256=sha(path),algebra_controls=4,selection='previous 137 acquisition anchors +/- one frame, 320 selected; rank>=2 subset only, not whole recordings',counts=counts,scope='graph residual invariant to channel-wise constant offsets and channel relabeling; no physical root cause or new accepted direction',records=reports)
    (a.out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(counts)
if __name__=='__main__':main()
