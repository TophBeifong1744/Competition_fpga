import argparse,hashlib,json,pathlib
import numpy as np

def shape(lags,values,peak):
    y=np.asarray(values,dtype=float);i=list(lags).index(peak);height=float(y[i])
    if not np.isfinite(y).all():raise ValueError('NONFINITE_CORRELATION')
    if height<=0:return dict(curvature=None,width=None,censored=None)
    curvature=None if i==0 or i==len(y)-1 else float((2*y[i]-y[i-1]-y[i+1])/height)
    left=right=i
    while left>0 and y[left-1]>=height*.5:left-=1
    while right<len(y)-1 and y[right+1]>=height*.5:right+=1
    return dict(curvature=curvature,width=right-left+1,censored=left==0 or right==len(y)-1)

def stats(rows):
    def dist(k):
        x=[r[k] for r in rows if r[k] is not None]
        return dict(n=len(x),quartiles=None if not x else np.percentile(x,[25,50,75]).tolist())
    return dict(frames=len(rows),curvature=dist('curvature'),width=dist('width'),censored_pairs=sum(r['censored_pairs'] for r in rows),scored_pairs=sum(r['scored_pairs'] for r in rows))

def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
    root=a.repo/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918';seal=json.loads((root/'checkpoint-20260923/SNAPSHOT-SHA256.json').read_text())['files'];pins={}
    def read(rel):
        f=root/rel;h=hashlib.sha256(f.read_bytes()).hexdigest();assert h==seal[rel],rel;pins[rel]=h;return json.loads(f.read_text())
    data=read('closeout-0918-20260921/acoustic/pairs01/frames.json');cycle=read('acoustic-mechanism-20260921/cycle01/result.json');lookup={(r['capture'],r['start']):r for r in cycle['records']};rows=[]
    for r in data:
        c=lookup.get((r['capture'],r['start']))
        if r['marker_excluded'] or c is None:continue
        ps=[p for p in r['pairs'] if p['valid']];features=[shape(p['legal_search_lags'],p['correlation'],p['peak']) for p in ps]
        def median(k):
            v=[f[k] for f in features if f[k] is not None];return None if not v else float(np.median(v))
        rows.append(dict(capture=r['capture'],start=r['start'],cycle_fail=c['any_arrival_model_residual_reject'],cycle_degrees=c['cycle_degrees'],support=[p['pair'] for p in ps],valid_pairs=len(ps),curvature=median('curvature'),width=median('width'),scored_pairs=sum(f['width'] is not None for f in features),censored_pairs=sum(f['censored'] is True for f in features)))
    # Same six valid pairs ensures identical support and three independent cycle constraints.
    groups={}
    for scope,selected in [('all_nonmarker',rows),('six_pairs',[r for r in rows if r['valid_pairs']==6])]:
        groups[scope]={str(fail):stats([r for r in selected if r['cycle_fail']==fail]) for fail in (False,True)}
    by_capture={name:{str(f):stats([r for r in rows if r['capture']==name and r['valid_pairs']==6 and r['cycle_fail']==f]) for f in (False,True)} for name in sorted({r['capture'] for r in rows})}
    a.out.mkdir(parents=True,exist_ok=False);result=dict(pins=pins,groups=groups,by_capture=by_capture,rows=rows,fft_calls=0,ifft_calls=0,status='AUTHOR_DIAGNOSTIC_NOT_ACCEPTANCE')
    (a.out/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(groups,indent=2))
if __name__=='__main__':main()
