import argparse,hashlib,importlib.util,json,pathlib,sys,zipfile
import numpy as np

def main():
 p=argparse.ArgumentParser();p.add_argument('--repo',type=pathlib.Path,required=True);p.add_argument('--zip',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();root=a.repo.resolve();here=pathlib.Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();receipt=json.loads((here/'run01/result.json').read_text(encoding='utf-8'));assert sha(a.zip)==receipt['zip_sha256'];rows=json.loads((here/'diagnostic01/frames.json').read_text());scripts=root/'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/trusted-direction-input-20260918/scripts';sys.path.insert(0,str(scripts));import process_capture as aligner
 out=[]
 with zipfile.ZipFile(a.zip) as z:
  for name in sorted({r['capture'] for r in rows}):
   if name in ('back_od','bg_post'):continue
   pcm=np.frombuffer(z.read('sound_09_22/'+name+'.bin'),'<u4').reshape(-1,8)[:,2:6].view('<i4');al=aligner.align(pcm);ok=all(c['status']=='CANDIDATE_ALIGNMENT_REVIEW_REQUIRED' and c['source_file_fits_capture'] for c in al['channels']);record=dict(capture=name,alignment=al,all_four_candidate=ok)
   if ok:
    lo=max(c['speech_interval_source_mapped_samples'][0] for c in al['channels']);hi=min(c['speech_interval_source_mapped_samples'][1] for c in al['channels']);rr=[r for r in rows if r['capture']==name];groups={}
    # Exclude both chirps and 200 ms around them from all reported speech cores.
    windows=[(c[label]['index']-9600,c[label]['index']+len(aligner.read_wav(aligner.PLAY/('marker-'+tag+'.wav')))+9600) for c in al['channels'] for label,tag in [('start_marker','start'),('end_marker','end')]]
    def marker(r):return any(r['start']<b and r['stop']>a for a,b in windows)
    for guard in (100,200,300):
     chosen=[r for r in rr if r['start']>=lo+guard*48 and r['stop']<=hi-guard*48 and not marker(r)];reasons={};angles=[];fresh=0
     for r in chosen:
      t=r['trackers']['new_pre_background'];key='gate_closed' if not r['activity']['new_pre_background'] else 'geometry_rejected' if not r['valid'] else 'outside_cone' if t['reason']=='outside_cone' else t['reason'];reasons[key]=reasons.get(key,0)+1
      if t['fresh_valid']:fresh+=1;v=t['direction'];angles.append(float(np.degrees(np.arctan2(v[1],v[0]))))
     groups[str(guard)]=dict(frames=len(chosen),gate=sum(r['activity']['new_pre_background'] for r in chosen),numeric_valid=sum(r['valid'] for r in chosen),fresh=fresh,hold=sum(r['trackers']['new_pre_background']['state']=='HOLD' for r in chosen),reason_counts=reasons,fresh_angle_quartiles=None if not angles else np.percentile(angles,[25,50,75]).tolist())
    record.update(common_mapped_interval=[lo,hi],groups=groups,fresh_whole=sum(r['trackers']['new_pre_background']['fresh_valid'] for r in rr),fresh_marker_neighborhood=sum(r['trackers']['new_pre_background']['fresh_valid'] and marker(r) for r in rr))
   out.append(record);print(name,'aligned',ok,record.get('groups',{}).get('200'),flush=True)
 a.out.mkdir(parents=True,exist_ok=False);result=dict(status='CANDIDATE_SOURCE_ALIGNMENT_NOT_ACTIVITY_TRUTH',zip_sha256=receipt['zip_sha256'],timeline_sha256=sha(here/'diagnostic01/frames.json'),dependencies={p.relative_to(root).as_posix():sha(p) for p in [scripts/'process_capture.py',aligner.PLAY/'timeline.json',aligner.PLAY/'marker-start.wav',aligner.PLAY/'marker-end.wav',aligner.PLAY/'soundsight-target-v1.wav']},captures=out,limits='Marker match does not prove speech content identity or exact onset. Tracker state uses full recording; guarded scores may inherit prior acquisition/HOLD.')
 (a.out/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
if __name__=='__main__':main()
