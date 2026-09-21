import argparse,hashlib,importlib.util,json,math,pathlib,sys
import numpy as np

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m

def replay(tracker,row,angle,valid):
 gate=row['candidates']['band_calibrated_duration']
 if not gate:tracker.reset()
 vec=None if angle is None else [math.cos(math.radians(angle)),math.sin(math.radians(angle)),0]
 return tracker.update(row['stop']/48,vec,valid and gate)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
 repo=a.repo.resolve();root=repo/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918';cp=root/'checkpoint-20260923';seal=load(cp/'SNAPSHOT-SHA256.json')['files'];pins={}
 def frozen(rel):
  p=root/rel;assert sha(p)==seal[rel],rel;pins[rel]=sha(p);return p
 summary=load(frozen('checkpoint-20260923/evidence/run01/summary.json'));deps=load(frozen('checkpoint-20260923/dependencies.json'))
 for p,h in deps.items():assert sha(repo/p)==h,p
 joint=module('full_joint',frozen('acoustic-mechanism-20260921/joint-arrival/analyze.py'));diag=module('full_diag',repo/'task-packages/PKG-B-ALG/tasks/c-board-algorithm-01/run.py');track=module('full_track',repo/'task-packages/PKG-B-ALG/payload/model/python/sector_tracker.py')
 cache={(r['capture'],r['start']):r for r in load(frozen('closeout-0918-20260921/acoustic/pairs01/frames.json'))};prior={(r['capture'],r['start']):r for r in load(frozen('acoustic-mechanism-20260921/joint-arrival/run01/result.json'))['rows']}
 markers={r['capture']:r for r in load(repo/'docs/reviews/eight-94b5fe7/markers/results.json')['captures']}
 protocol=dict(candidate='unchanged quarter-sample graph grid, normalized six-pair score',fallback='fewer than six original VALID pairs: preserve original projection, including original rejection',bad_score='reject candidate if nonpositive/nonfinite peaks',gate='frozen band_calibrated_duration',tracker='unchanged candidate60',selection='all eight recordings; development only',no_confidence_threshold=True)
 (a.out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
 grid=joint.grid();plane=joint.G@joint.POS;pos=np.column_stack((joint.POS*343/48000,np.zeros(4)));bounds=[np.linalg.norm(pos[j]-pos[i])*48000/343 for i,j in diag.PAIRS];output=[];captures=[];forward=inverse=used_cache=prior_checks=0
 for name in sorted(r['capture'] for r in summary['reports']):
  raw=next(p for p in summary['pins'] if p.endswith('/'+name+'/raw.bin'))
  for rel in (raw,str(pathlib.PurePosixPath(raw).with_name('metadata.json'))):assert sha(repo/rel)==summary['pins'][rel],rel;pins[rel]=summary['pins'][rel]
  meta=load((repo/raw).with_name('metadata.json'));assert np.allclose(meta['coordinates_m'],pos,atol=1e-15,rtol=0) and meta['sample_rate_hz']==48000
  pcm=np.fromfile(repo/raw,dtype='<u4').reshape(-1,8)[:,2:6].view('<i4');rows=load(frozen('checkpoint-20260923/evidence/run01/'+name+'-frames.json'));tr=track.Tracker(track.Config(cone_half_angle_deg=60));control=track.Tracker(track.Config(cone_half_angle_deg=60));out=[]
  for row in rows:
   cached=cache.get((name,row['start']))
   if cached is not None:pairs=cached['pairs'];used_cache+=1
   else:
    pairs,corr=diag.floating(pcm[row['start']:row['stop']],bounds);forward+=4;inverse+=sum(p['bins']>=12 for p in pairs)
    for k,p in enumerate(pairs):
     if 'peak' in p:
      lim=int(np.ceil(bounds[k]));lags=np.arange(-lim,lim+1);p.update(legal_search_lags=lags.tolist(),correlation=corr[k,lags%1024].tolist())
   full=diag.projection(pairs,pos,48000,343);old=row['projection'];assert [p['reason'] for p in pairs]==row['pair_reasons'];assert full.get('advisory_consistent',False)==old.get('advisory_consistent',False)
   for k in ('projection_norm','residual_samples','advisory_azimuth_deg'):
    if k in old:assert np.isclose(full[k],old[k],rtol=1e-12,atol=1e-10)
   oldvalid=old.get('advisory_consistent',False);oldangle=old.get('advisory_azimuth_deg') if oldvalid else None;state0=replay(control,row,oldangle,oldvalid)
   assert state0==row['trackers']['candidate60'],(name,row['start'],'TRACKER_MISMATCH')
   valid=oldvalid;angle=oldangle;score=None;mode='original_fallback';norm=res=None
   if all(p['valid'] for p in pairs):
    if any(p['peak_height']<=0 or not np.isfinite(p['peak_height']) for p in pairs):valid=False;angle=None;mode='invalid_score'
    else:
     tau,score,_=joint.choose(pairs,grid);u=np.linalg.lstsq(plane,tau,rcond=None)[0];res=float(np.sqrt(np.mean((tau-plane@u)**2)));norm=float(np.linalg.norm(u));valid=res<=.5 and .1<=norm<=1.3;angle=float(np.degrees(np.arctan2(u[1],u[0]))) if valid else None;mode='joint'
     prev=prior.get((name,row['start']))
     if prev is not None:assert np.array_equal(tau,prev['tau']) and valid==prev['new_valid'] and np.isclose(score,prev['support_ratio'],rtol=1e-12,atol=1e-12);prior_checks+=1
   state=replay(tr,row,angle,valid);r=dict(capture=name,start=row['start'],stop=row['stop'],marker_excluded=row['marker_excluded'],gate=row['candidates']['band_calibrated_duration'],mode=mode,baseline_valid=oldvalid,new_valid=bool(valid),angle=angle,score=score,norm=norm,residual=res,tracker=state,baseline_tracker=state0);out.append(r);output.append(r)
  groups={'whole':out}
  if name in markers:
   core=markers[name]['common_source_mapped_interval_samples'];groups['target200']=[r for r in out if r['start']>=math.ceil(core[0]+9600) and r['stop']<=math.floor(core[1]-9600) and not r['marker_excluded']]
  counts={}
  for group,rs in groups.items():
   counts[group]=dict(frames=len(rs),joint=sum(r['mode']=='joint' for r in rs),fallback=sum(r['mode']=='original_fallback' for r in rs),gate=sum(r['gate'] for r in rs),old_valid=sum(r['baseline_valid'] for r in rs),new_valid=sum(r['new_valid'] for r in rs),gained=sum(r['new_valid'] and not r['baseline_valid'] for r in rs),lost=sum(r['baseline_valid'] and not r['new_valid'] for r in rs),old_fresh=sum(r['baseline_tracker']['fresh_valid'] for r in rs),fresh=sum(r['tracker']['fresh_valid'] for r in rs),hold=sum(r['tracker']['state']=='HOLD' for r in rs),max_acquire=max((r['tracker']['acquire_count'] for r in rs),default=0))
  captures.append(dict(capture=name,groups=counts));print(name,json.dumps(counts),flush=True)
 assert len(output)==4488 and prior_checks==191 and used_cache==320
 result=dict(protocol=protocol,pins=pins,dependencies=deps,captures=captures,matched_baseline_frames=len(output),matched_prior_joint_frames=prior_checks,cached_frames=used_cache,forward_fft_channels=forward,inverse_fft_pairs=inverse,formal_acceptance=False)
 for n,v in [('result',result),('frames',output)]: (a.out/(n+'.json')).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
if __name__=='__main__':main()
