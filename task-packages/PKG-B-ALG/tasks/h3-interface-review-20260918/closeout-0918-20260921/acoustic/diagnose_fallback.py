"""Read-only attribution and tracker replay of frozen eight-capture outputs."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def run(repo,out):
    out.mkdir(parents=True,exist_ok=False)
    cp=repo/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923'
    source=repo/'task-packages/PKG-B-ALG/payload/model/python/sector_tracker.py'
    assert sha(source)==load(cp/'dependencies.json')[source.relative_to(repo).as_posix()]
    spec=importlib.util.spec_from_file_location('frozen_tracker',source)
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
    cfg=load(cp/'config.json');manifest=load(cp/'SNAPSHOT-SHA256.json')['files']
    reports=[];pins={source.relative_to(repo).as_posix():sha(source)};trace=[]
    for f in sorted((cp/'evidence/run01').glob('*-frames.json')):
        assert sha(f)==manifest[f.relative_to(cp.parent).as_posix()]
        pins[f.relative_to(repo).as_posix()]=sha(f)
        name=f.name[:-12];rows=load(f);branches={}
        for key,cone in [('baseline30',30),('ungated60',60),('candidate60',cfg['tracker_cone_half_angle_deg'])]:
            t=mod.Tracker(mod.Config(cone_half_angle_deg=cone));counts=Counter();longest=0;consecutive=0;max_acquire=0
            for row in rows:
                enabled=True if key=='ungated60' else row['baseline_present'] if key=='baseline30' else row['candidates']['band_calibrated_duration']
                valid=row['projection'].get('advisory_consistent',False)
                a=row['numeric_angle'];vec=None if a is None else [math.cos(math.radians(a)),math.sin(math.radians(a)),0]
                previous=list(t.candidates)
                if key=='candidate60' and not enabled:t.reset()
                state=t.update(row['stop']/48,vec,valid and enabled)
                # Replay control/identity, not approximate equality of states/counts.
                assert state==row['trackers'][key],(name,key,row['start'],state,row['trackers'][key])
                if not enabled:stage='activity_gate_reject'
                elif not valid:stage='projection_reject'
                elif state['reason']=='outside_cone':stage='outside_cone'
                elif state['fresh_valid']:stage='fresh'
                elif previous and state['acquire_count']==1:stage='acquire_spread_restart'
                else:stage='acquire_wait'
                counts[stage]+=1
                eligible=enabled and valid and state['reason']!='outside_cone'
                consecutive=consecutive+1 if eligible else 0;longest=max(longest,consecutive)
                max_acquire=max(max_acquire,state['acquire_count'])
                trace.append(dict(capture=name,branch=key,start=row['start'],stop=row['stop'],first_id=row['first_id'],
                                  numeric_angle=a,stage=stage,acquire_count=state['acquire_count'],marker_excluded=row['marker_excluded']))
            assert sum(counts.values())==len(rows)
            branches[key]=dict(counts=dict(counts),max_consecutive_eligible=longest,max_acquire_count=max_acquire)
        reports.append(dict(capture=name,frames=len(rows),scope='whole_recording_including_markers_not_formal_voice_metrics',
                            pair_reasons=dict(Counter(x for r in rows for x in r['pair_reasons'])),branches=branches))
    result=dict(status='FROZEN_CONTROL_REPLAY_PASS_NOT_PERFORMANCE_ACCEPTANCE',input_pins=pins,captures=reports,
                replayed_states=sum(r['frames']*3 for r in reports),config=cfg,
                limitation='Whole-recording attribution; includes marker/background frames; no independent truth or parameter tuning.')
    for name,value in [('result.json',result),('trace.json',trace)]:
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    for key in ['baseline30','ungated60','candidate60']:
        total=Counter()
        for r in reports:total.update(r['branches'][key]['counts'])
        print(key,dict(total),'max_acquire',max(r['branches'][key]['max_acquire_count'] for r in reports))
    print('REPLAY_PASS',result['replayed_states'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();run(a.repo.resolve(),a.out.resolve())
