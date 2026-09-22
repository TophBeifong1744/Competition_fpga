import argparse,hashlib,importlib.util,json,math,pathlib,sys,zipfile
import numpy as np

def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',type=pathlib.Path,required=True);ap.add_argument('--zip',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path,required=True);a=ap.parse_args();root=a.repo.resolve();pkg=root/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918';here=pathlib.Path(__file__).resolve().parent
 receipt=json.loads((here/'run01/result.json').read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(a.zip)==receipt['zip_sha256']
 cp=pkg/'checkpoint-20260923';cfg=json.loads((cp/'config.json').read_text());oldnoise=json.loads((cp/'evidence/run01/calibration.json').read_text())['noise_power_codes_squared'];diag=module('new_diag',root/'task-packages/PKG-B-ALG/tasks/c-board-algorithm-01/run.py');act=module('new_act',cp/'source/candidates.py');trk=module('new_trk',root/'task-packages/PKG-B-ALG/payload/model/python/sector_tracker.py')
 pos=np.array([[0,0,0],[.04,0,0],[.04,.04,0],[0,.04,0]]);bounds=[np.linalg.norm(pos[j]-pos[i])*48000/343 for i,j in diag.PAIRS];pcm={};features={}
 with zipfile.ZipFile(a.zip) as z:
  for path in receipt['input_sha256']:
   if not path.endswith('.bin'):continue
   raw=z.read(path);assert hashlib.sha256(raw).hexdigest()==receipt['input_sha256'][path];name=pathlib.PurePosixPath(path).stem;pcm[name]=np.frombuffer(raw,'<u4').reshape(-1,8)[:,2:6].view('<i4');features[name]=[act.features(pcm[name][s:s+1024]) for s in range(0,len(pcm[name])-1023,512)]
 noise=np.percentile([f['band_power'] for f in features['back_od']],95,axis=0);rows=[];summaries=[]
 for name,x in sorted(pcm.items()):
  trackers={m:trk.Tracker(trk.Config(cone_half_angle_deg=60)) for m in ('no_gate','old_background','new_pre_background')};gates={m:act.BandActivity(n,cfg) for m,n in [('old_background',oldnoise),('new_pre_background',noise)]};out=[]
  for index,start in enumerate(range(0,len(x)-1023,512)):
   pairs,_=diag.floating(x[start:start+1024],bounds);p=diag.projection(pairs,pos,48000,343);valid=p.get('advisory_consistent',False);angle=p.get('advisory_azimuth_deg') if valid else None;f=features[name][index];activity={'no_gate':True,**{m:g.update(f['band_power'],f['endpoint']) for m,g in gates.items()}};states={}
   for m,t in trackers.items():
    if not activity[m]:t.reset()
    v=None if angle is None else [math.cos(math.radians(angle)),math.sin(math.radians(angle)),0];states[m]=t.update((start+1024)/48,v,valid and activity[m])
   out.append(dict(capture=name,start=start,stop=start+1024,valid=valid,angle=angle,projection=p,pair_reasons=[p['reason'] for p in pairs],taus=[p.get('tau_samples') for p in pairs],activity=activity,trackers=states))
  modes={m:dict(gate_frames=sum(r['activity'][m] for r in out),eligible=sum(r['activity'][m] and r['valid'] and abs(r['angle'])<=60+1e-10 for r in out),fresh=sum(r['trackers'][m]['fresh_valid'] for r in out),hold=sum(r['trackers'][m]['state']=='HOLD' for r in out),max_acquire=max(r['trackers'][m]['acquire_count'] for r in out)) for m in trackers};s=dict(capture=name,frames=len(out),numeric_valid=sum(r['valid'] for r in out),modes=modes);summaries.append(s);rows.extend(out);print(json.dumps(s),flush=True)
 deps=[cp/'config.json',cp/'evidence/run01/calibration.json',cp/'source/candidates.py',root/'task-packages/PKG-B-ALG/tasks/c-board-algorithm-01/run.py',root/'task-packages/PKG-B-ALG/payload/model/python/sector_tracker.py',root/'task-packages/PKG-B-ALG/tasks/phat-fixed-03/integration/chain.py']
 result=dict(status='CONDITIONAL_DEVELOPMENT_DIAGNOSTIC_NOT_ACCEPTANCE',zip_sha256=receipt['zip_sha256'],dependencies={p.relative_to(root).as_posix():sha(p) for p in deps},source_sha256=sha(pathlib.Path(__file__)),assumptions=dict(positions_m=pos.tolist(),fs=48000,sound_speed=343,configuration_confirmation='pending operator confirmation',scene_mapping={'back_od':'pre_background','az045':'azp045'},mapping_source='user confirmation',activity_truth='unavailable; full recordings include markers and pauses'),new_pre_background_power=noise.tolist(),calibration_note='activity background normalization only, not channel calibration; pre background in calibration sample',captures=summaries,frames=len(rows))
 a.out.mkdir(parents=True,exist_ok=False)
 for n,v in [('result',result),('frames',rows)]: (a.out/(n+'.json')).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
if __name__=='__main__':main()
