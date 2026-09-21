"""Fixed quarter-sample graph grid over frozen six-pair correlation caches."""
import argparse,hashlib,json,pathlib
import numpy as np
PAIRS=[(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]
POS=np.array([[0,0],[.04,0],[.04,.04],[0,.04]])*48000/343
G=np.zeros((6,4))
for k,(i,j) in enumerate(PAIRS):G[k,i]=-1;G[k,j]=1
BOUNDS=np.array([np.linalg.norm(POS[j]-POS[i])+.05 for i,j in PAIRS])

def grid():
    axes=[np.arange(-int(np.floor(BOUNDS[k]*4)),int(np.floor(BOUNDS[k]*4))+1)/4 for k in (0,1,2)]
    arrivals=np.array(np.meshgrid(*axes,indexing='ij')).reshape(3,-1).T
    tau=arrivals@G[:,1:].T
    return tau[np.all(np.abs(tau)<=BOUNDS+1e-12,axis=1)]

def choose(pairs,tau):
    scores=np.zeros(len(tau));ratios=[]
    for k,p in enumerate(pairs):
        y=np.array(p['correlation']);height=p['peak_height']
        if not np.isfinite(y).all() or not np.isfinite(height) or height<=0:raise ValueError('NONPOSITIVE_OR_NONFINITE_PEAK')
        v=np.interp(tau[:,k],p['legal_search_lags'],y)/height;ratios.append(v);scores+=v/6
    best=int(np.argmax(scores));return tau[best],float(scores[best]),[float(v[best]) for v in ratios]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path,required=True);a=ap.parse_args()
    root=a.repo/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918';seal=json.loads((root/'checkpoint-20260923/SNAPSHOT-SHA256.json').read_text())['files'];pins={}
    def read(rel):
        f=root/rel;h=hashlib.sha256(f.read_bytes()).hexdigest();assert h==seal[rel],rel;pins[rel]=h;return json.loads(f.read_text())
    data=read('closeout-0918-20260921/acoustic/pairs01/frames.json');cs=read('acoustic-mechanism-20260921/cycle01/result.json');lookup={(r['capture'],r['start']):r for r in cs['records']}
    tau_grid=grid();rows=[];plane=G@POS
    for r in data:
        if r['marker_excluded'] or not all(p['valid'] for p in r['pairs']):continue
        assert [tuple(p['pair']) for p in r['pairs']]==PAIRS
        old=lookup[(r['capture'],r['start'])];tau,score,ratios=choose(r['pairs'],tau_grid)
        u=np.linalg.lstsq(plane,tau,rcond=None)[0];res=float(np.sqrt(np.mean((tau-plane@u)**2)));norm=float(np.linalg.norm(u));valid=res<=.5 and .1<=norm<=1.3
        graph_res=float(np.max(np.abs(tau-G[:,1:]@np.linalg.lstsq(G[:,1:],tau,rcond=None)[0])));assert graph_res<1e-10 and score<=1+1e-12
        rows.append(dict(capture=r['capture'],start=r['start'],old_cycle_fail=old['any_arrival_model_residual_reject'],old_valid=r['projection'].get('advisory_consistent',False),support_ratio=score,min_pair_ratio=min(ratios),ratios=ratios,tau=tau.tolist(),plane_residual=res,norm=norm,new_valid=valid,angle=float(np.degrees(np.arctan2(u[1],u[0]))) if valid else None,graph_residual_constructed=graph_res))
    assert len(rows)==191
    groups={}
    for fail in (False,True):
        rs=[r for r in rows if r['old_cycle_fail']==fail];groups[str(fail)]=dict(frames=len(rs),support_ratio_quartiles=np.percentile([r['support_ratio'] for r in rs],[25,50,75]).tolist(),min_pair_ratio_quartiles=np.percentile([r['min_pair_ratio'] for r in rs],[25,50,75]).tolist(),old_valid=sum(r['old_valid'] for r in rs),new_valid=sum(r['new_valid'] for r in rs),newly_valid=sum(r['new_valid'] and not r['old_valid'] for r in rs),lost=sum(r['old_valid'] and not r['new_valid'] for r in rs))
    a.out.mkdir(parents=True,exist_ok=False);result=dict(status='AUTHOR_DIAGNOSTIC_NOT_ADOPTED',pins=pins,grid_step_samples=.25,grid_candidates=len(tau_grid),groups=groups,rows=rows,fft_calls=0,ifft_calls=0)
    (a.out/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({'grid_candidates':len(tau_grid),'groups':groups},indent=2))
if __name__=='__main__':main()
