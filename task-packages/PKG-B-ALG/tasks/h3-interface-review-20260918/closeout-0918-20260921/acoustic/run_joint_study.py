"""One fixed exploratory joint-grid candidate, using existing eight recordings."""
import argparse
from collections import Counter
import importlib.util
import json
import math
from pathlib import Path
import sys
import platform
import numpy as np
from analyze_pairs import load,sha,dump,distribution
from joint_candidate import JointCandidate

def module(name,path):
    sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m

def execute(repo,out):
    out.mkdir(parents=True,exist_ok=False)
    cp=repo/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923'
    deps=load(cp/'dependencies.json')
    for p,h in deps.items():assert sha(repo/p)==h,p
    old=load(cp/'evidence/run01/summary.json');seal=load(cp/'SNAPSHOT-SHA256.json')['files']
    diag=module('joint_diag',repo/'task-packages/PKG-B-ALG/tasks/c-board-algorithm-01/run.py')
    tracker=module('joint_tracker',repo/'task-packages/PKG-B-ALG/payload/model/python/sector_tracker.py')
    reports=[];pins=dict(deps)
    for report in old['reports']:
        name=report['capture'];f=cp/'evidence/run01'/f'{name}-frames.json'
        assert sha(f)==seal[f.relative_to(cp.parent).as_posix()];pins[f.relative_to(repo).as_posix()]=sha(f)
        frames=load(f);raw=next(p for p in old['pins'] if p.endswith('/'+name+'/raw.bin'))
        assert sha(repo/raw)==old['pins'][raw]
        meta=load((repo/raw).with_name('metadata.json'));pos=np.array(meta['coordinates_m'])
        model=JointCandidate(pos,diag.PAIRS);bounds=[float(np.linalg.norm(pos[j]-pos[i])*48000/343) for i,j in diag.PAIRS]
        pcm=np.fromfile(repo/raw,dtype='<u4').reshape(-1,8)[:,2:6].view('<i4').astype(np.int64)
        tracks={k:tracker.Tracker(tracker.Config(cone_half_angle_deg=60)) for k in ['joint_gated','joint_ungated']}
        data=[];counts=Counter()
        for i,row in enumerate(frames):
            pair,corr=diag.floating(pcm[row['start']:row['stop']],bounds)
            assert [x['reason'] for x in pair]==row['pair_reasons'],(name,i)
            candidate=model.estimate(pair,corr);counts[candidate['reason']]+=1
            states={}
            for key,t in tracks.items():
                gate=key=='joint_ungated' or row['candidates']['band_calibrated_duration']
                if not gate:t.reset()
                a=candidate['angle'];v=None if a is None else [math.cos(math.radians(a)),math.sin(math.radians(a)),0]
                states[key]=t.update(row['stop']/48,v,candidate['valid'] and gate)
            data.append(dict(index=i,start=row['start'],stop=row['stop'],marker_excluded=row['marker_excluded'],
                             gate=row['candidates']['band_calibrated_duration'],candidate=candidate,trackers=states))
        bg=report['background_operator_label'];region=report['audio']['evaluation_reference_rows']
        selected=list(range(len(data))) if bg else [i for i,r in enumerate(data) if r['start']>=region[0] and r['stop']<=region[1] and not r['marker_excluded']]
        metrics={}
        for key in tracks:
            chosen=[data[i] for i in selected];fresh=[r for r in chosen if r['trackers'][key]['fresh_valid']]
            nominal=report['nominal_deg'];dev=[]
            for r in fresh:
                d=r['trackers'][key]['direction'];angle=math.degrees(math.atan2(d[1],d[0]))
                if nominal is not None:dev.append(abs((angle-nominal+180)%360-180))
            metrics[key]=dict(eligible=len(chosen),fresh=len(fresh),whole_recording_fresh=sum(r['trackers'][key]['fresh_valid'] for r in data),
                              states=dict(Counter(r['trackers'][key]['state'] for r in chosen)),
                              reasons=dict(Counter(r['trackers'][key]['reason'] for r in chosen)),
                              nominal_deviation_not_accuracy=distribution(dev),nominal_over15_count=sum(x>15 for x in dev),
                              max_acquire=max(r['trackers'][key]['acquire_count'] for r in data))
        baseline=report['sensitivity']['reported_background' if bg else '200']['direction']
        r=dict(capture=name,background=bg,split=report['split'],frames=len(data),candidate_reasons=dict(counts),
               metrics=metrics,frozen_baseline=baseline,formal_accuracy=None,objective_audio_benefit=None)
        reports.append(r);dump(out/(name+'-frames.json'),data);print(name,{k:v['fresh'] for k,v in metrics.items()},flush=True)
    result=dict(status='AUTHOR_EXPLORATORY_NOT_ACCEPTANCE',reports=reports,input_pins=pins,
                source_commit='fe67547635ff254f9f91c7f917e8dedb6daf3363',
                script_hashes={p.name:sha(p) for p in [Path(__file__),Path(__file__).with_name('joint_candidate.py'),Path(__file__).with_name('joint-study-config.json')]},
                config=load(Path(__file__).with_name('joint-study-config.json')),environment=dict(python=platform.python_version(),numpy=np.__version__),
                independent_validation=False,audio_rendered=False,production_changed=False)
    dump(out/'result.json',result);dump(out/'OUTPUT-SHA256.json',{p.name:sha(p) for p in out.iterdir() if p.is_file()})

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();execute(a.repo.resolve(),a.out.resolve())
