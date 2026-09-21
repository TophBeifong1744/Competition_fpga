import argparse,hashlib,importlib.util,json,pathlib
import numpy as np

def separation(a,b):return np.abs((a-b+180)%360-180)
def competitor(scores,angles,valid,best):
    mask=valid&(separation(angles,angles[best])>=15.)
    ids=np.flatnonzero(mask)
    if not len(ids):return None
    return int(ids[np.argmax(scores[ids])])

def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
    root=a.repo/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918';seal=json.loads((root/'checkpoint-20260923/SNAPSHOT-SHA256.json').read_text())['files'];pins={}
    def frozen(rel):
        f=root/rel;h=hashlib.sha256(f.read_bytes()).hexdigest()
        if h!=seal[rel]:raise ValueError('HASH_MISMATCH '+rel)
        pins[rel]=h;return f
    rel='acoustic-mechanism-20260921/joint-arrival/analyze.py';f=frozen(rel);spec=importlib.util.spec_from_file_location('joint_reference',f);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    data=json.loads(frozen('closeout-0918-20260921/acoustic/pairs01/frames.json').read_text());prior=json.loads(frozen('acoustic-mechanism-20260921/joint-arrival/run01/result.json').read_text());lookup={(r['capture'],r['start']):r for r in prior['rows']}
    config=json.loads(frozen('checkpoint-20260923/evidence/run01/summary.json').read_text())['config'];assert config['wrong_direction_threshold_deg']==15
    tau=m.grid();plane=m.G@m.POS;u=np.linalg.lstsq(plane,tau.T,rcond=None)[0].T;norm=np.linalg.norm(u,axis=1);res=np.sqrt(np.mean((tau-u@plane.T)**2,axis=1));valid=(res<=.5)&(norm>=.1)&(norm<=1.3);angles=np.degrees(np.arctan2(u[:,1],u[:,0]));rows=[]
    for r in data:
        old=lookup.get((r['capture'],r['start']))
        if old is None:continue
        scores=np.zeros(len(tau))
        for k,pair in enumerate(r['pairs']):scores+=np.interp(tau[:,k],pair['legal_search_lags'],pair['correlation'])/pair['peak_height']/6
        best=int(np.argmax(scores));assert np.array_equal(tau[best],old['tau']);assert np.isclose(scores[best],old['support_ratio'],atol=1e-12,rtol=1e-12);assert bool(valid[best])==old['new_valid']
        rec=dict(capture=r['capture'],start=r['start'],old_cycle_fail=old['old_cycle_fail'],best_valid=bool(valid[best]),best_score=float(scores[best]),best_norm=float(norm[best]),best_residual=float(res[best]),best_angle=float(angles[best]) if valid[best] else None,competitor=None)
        if valid[best]:
            assert separation(angles[best],old['angle'])<1e-9
            j=competitor(scores,angles,valid,best)
            if j is not None:rec['competitor']=dict(angle=float(angles[j]),separation_deg=float(separation(angles[j],angles[best])),score=float(scores[j]),absolute_gap=float(scores[best]-scores[j]),relative_loss=float((scores[best]-scores[j])/scores[best]),tau=tau[j].tolist(),norm=float(norm[j]),plane_residual=float(res[j]))
        rows.append(rec)
    groups={}
    for fail in (False,True):
        rs=[r for r in rows if r['old_cycle_fail']==fail];cs=[r['competitor'] for r in rs if r['competitor'] is not None]
        groups[str(fail)]=dict(frames=len(rs),best_valid=sum(r['best_valid'] for r in rs),best_invalid=len(rs)-sum(r['best_valid'] for r in rs),competitors=len(cs),absolute_gap_quartiles=np.percentile([c['absolute_gap'] for c in cs],[25,50,75]).tolist(),relative_loss_quartiles=np.percentile([c['relative_loss'] for c in cs],[25,50,75]).tolist(),separation_quartiles=np.percentile([c['separation_deg'] for c in cs],[25,50,75]).tolist())
    a.out.mkdir(parents=True,exist_ok=False);result=dict(status='AUTHOR_DIAGNOSTIC_NOT_CONFIDENCE_CALIBRATION',pins=pins,matched_prior_frames=len(rows),angle_separation_deg=15,grid_candidates=len(tau),geometrically_valid_grid_candidates=int(valid.sum()),groups=groups,rows=rows,fft_calls=0,ifft_calls=0)
    (a.out/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(groups,indent=2))
if __name__=='__main__':main()
