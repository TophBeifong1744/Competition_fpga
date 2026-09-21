"""Descriptive nominal-direction residuals; never calibration coefficients."""
import argparse,hashlib,json,pathlib
import numpy as np
PAIRS=[(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]
POS=np.array([[0,0],[.04,0],[.04,.04],[0,.04]])
M=np.array([(POS[j]-POS[i])*48000/343 for i,j in PAIRS])
def expected(degrees):return M@np.array([np.cos(np.deg2rad(degrees)),np.sin(np.deg2rad(degrees))])
def main():
 p=argparse.ArgumentParser();p.add_argument('--repo',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();root=a.repo/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918';seal=json.loads((root/'checkpoint-20260923/SNAPSHOT-SHA256.json').read_text())['files'];pins={}
 def read(rel):
  f=root/rel;h=hashlib.sha256(f.read_bytes()).hexdigest();assert h==seal[rel],rel;pins[rel]=h;return json.loads(f.read_text())
 data=read('closeout-0918-20260921/acoustic/pairs01/frames.json');summary=read('checkpoint-20260923/evidence/run01/summary.json');nominal={r['capture']:r['nominal_deg'] for r in summary['reports']};records=[];captures=[]
 # All six original VALID pairs: no support change across compared frames.
 for name in sorted({r['capture'] for r in data}):
  chosen=[r for r in data if r['capture']==name and not r['marker_excluded'] and all(p['valid'] for p in r['pairs'])];angle=nominal[name];ref=expected(angle)
  x=np.array([[p['tau_samples'] for p in r['pairs']] for r in chosen]);res=x-ref
  for r,v in zip(chosen,res):records.append(dict(capture=name,start=r['start'],nominal_residual_samples=v.tolist()))
  captures.append(dict(capture=name,nominal_deg=angle,frames=len(chosen),median_residual=np.median(res,axis=0).tolist(),residual_q25=np.percentile(res,25,axis=0).tolist(),residual_q75=np.percentile(res,75,axis=0).tolist(),expected_nominal_tau=ref.tolist()))
 repeated=[]
 for angle in (-45,0,45):
  cs=[c for c in captures if c['nominal_deg']==angle];assert len(cs)==2
  delta=np.array(cs[1]['median_residual'])-np.array(cs[0]['median_residual']);repeated.append(dict(nominal_deg=angle,captures=[c['capture'] for c in cs],frames=[c['frames'] for c in cs],second_minus_first_samples=delta.tolist(),max_abs_delta=float(np.max(np.abs(delta)))))
 med=np.array([c['median_residual'] for c in captures]);span=np.ptp(med,axis=0)
 a.out.mkdir(parents=True,exist_ok=False);out=dict(status='NOMINAL_RESIDUAL_DESCRIPTION_NOT_CALIBRATION',pins=pins,pairs=PAIRS,captures=captures,repeated=repeated,cross_capture_median_span_samples=span.tolist(),records=records,frames=len(records),fft_calls=0,not_independent=True)
 (a.out/'result.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n');print(json.dumps({'frames':len(records),'repeated':repeated,'median_span':span.tolist()},indent=2))
if __name__=='__main__':main()
