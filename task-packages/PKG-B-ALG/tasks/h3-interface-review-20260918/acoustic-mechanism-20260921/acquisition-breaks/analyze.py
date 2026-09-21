import argparse,collections,hashlib,json,pathlib

def cause(row,state,valid):
 if not row['gate']:return 'activity_gate_closed'
 if not valid:return 'geometry_rejected'
 if state['reason']=='outside_cone':return 'outside_cone'
 if state['reason']=='invalid_direction':return 'invalid_direction'
 return 'eligible'

def analyze(rows,branch):
 statekey='baseline_tracker' if branch=='baseline' else 'tracker';validkey='baseline_valid' if branch=='baseline' else 'new_valid';counts=collections.Counter();events=[];prev=None;eligible_run=longest=0
 for r in rows:
  state=r[statekey];assert not state['fresh_valid'] and state['state']!='HOLD'
  c=cause(r,state,r[validkey]);counts[c]+=1
  eligible_run=eligible_run+1 if c=='eligible' else 0;longest=max(longest,eligible_run)
  if prev is not None and prev[statekey]['acquire_count']>0:
   old=prev[statekey]['acquire_count'];new=state['acquire_count']
   if c!='eligible' or new==1:
    reason=c if c!='eligible' else 'spread_restart'
    assert new==(1 if reason=='spread_restart' else 0)
    events.append(dict(capture=r['capture'],previous_start=prev['start'],break_start=r['start'],previous_acquire_count=old,reason=reason))
   else:assert new==old+1
  prev=r
 if prev is not None and prev[statekey]['acquire_count']>0:events.append(dict(capture=prev['capture'],previous_start=prev['start'],break_start=None,previous_acquire_count=prev[statekey]['acquire_count'],reason='recording_end_censored'))
 return dict(frames=len(rows),frame_causes=dict(counts),longest_eligible_run=longest,max_acquire=max(r[statekey]['acquire_count'] for r in rows),break_counts=dict(collections.Counter(e['reason'] for e in events)),events=events)

def main():
 p=argparse.ArgumentParser();p.add_argument('--repo',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();root=a.repo/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918';seal=json.loads((root/'checkpoint-20260923/SNAPSHOT-SHA256.json').read_text())['files'];rel='acoustic-mechanism-20260921/joint-full-replay/run01/frames.json';f=root/rel;h=hashlib.sha256(f.read_bytes()).hexdigest();assert h==seal[rel];rows=json.loads(f.read_text());captures=[]
 for name in sorted({r['capture'] for r in rows}):
  rs=[r for r in rows if r['capture']==name];assert len(rs)==561 and all(y['start']-x['start']==512 for x,y in zip(rs,rs[1:]));captures.append(dict(capture=name,**{b:analyze(rs,b) for b in ('baseline','joint')}))
 totals={}
 for b in ('baseline','joint'):
  fc=collections.Counter();bc=collections.Counter()
  for c in captures:fc.update(c[b]['frame_causes']);bc.update(c[b]['break_counts'])
  totals[b]=dict(frame_causes=dict(fc),break_counts=dict(bc),longest_eligible_run=max(c[b]['longest_eligible_run'] for c in captures),max_acquire=max(c[b]['max_acquire'] for c in captures))
 a.out.mkdir(parents=True,exist_ok=False);result=dict(status='AUTHOR_ATTRIBUTION_NOT_NEW_ALGORITHM',input_sha256=h,totals=totals,captures=captures)
 (a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(totals,indent=2))
if __name__=='__main__':main()
