"""Selected real-frame pair diagnostics; no tuning, waveform rendering or new simulation."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import sys
import numpy as np

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def distribution(values):
    x=list(values)
    return dict(n=len(x),p50=float(np.median(x)) if x else None,p95=float(np.percentile(x,95)) if x else None,max=max(x) if x else None)

def execute(repo,out):
    out.mkdir(parents=True,exist_ok=False)
    cp=repo/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923'
    deps=load(cp/'dependencies.json');sealed=load(cp/'SNAPSHOT-SHA256.json')['files']
    for name,want in deps.items():assert sha(repo/name)==want,name
    summary=load(cp/'evidence/run01/summary.json')
    assert sha(cp/'evidence/run01/summary.json')==sealed['checkpoint-20260923/evidence/run01/summary.json']
    source=repo/'task-packages/PKG-B-ALG/tasks/c-board-algorithm-01/run.py'
    spec=importlib.util.spec_from_file_location('selected_pair_diagnostic',source)
    diag=importlib.util.module_from_spec(spec);sys.modules[spec.name]=diag;spec.loader.exec_module(diag)
    pins=dict(deps);records=[];transitions=[];counts=Counter();all_gate_projection=Counter();groups=[]
    for frame_file in sorted((cp/'evidence/run01').glob('*-frames.json')):
        assert sha(frame_file)==sealed[frame_file.relative_to(cp.parent).as_posix()]
        pins[frame_file.relative_to(repo).as_posix()]=sha(frame_file)
        name=frame_file.name.removesuffix('-frames.json');rows=load(frame_file)
        raw_path=next(p for p in summary['pins'] if p.endswith('/'+name+'/raw.bin'))
        assert sha(repo/raw_path)==summary['pins'][raw_path]
        meta=load((repo/raw_path).with_name('metadata.json'))
        pos=np.asarray(meta['coordinates_m']);fs=meta['sample_rate_hz'];c=343
        assert meta['channel_order']==['mic0','mic1','mic2','mic3'] and fs==48000
        matrix=np.array([(pos[j]-pos[i])[:2]*fs/c for i,j in diag.PAIRS])
        bounds=[float(np.linalg.norm(pos[j]-pos[i])*fs/c) for i,j in diag.PAIRS]
        pcm=np.fromfile(repo/raw_path,dtype='<u4').reshape(-1,8)[:,2:6].view('<i4').astype(np.int64)
        anchors={i for i,r in enumerate(rows) if r['trackers']['candidate60']['state']=='ACQUIRE'}
        selected={j for i in anchors for j in (i-1,i,i+1) if 0<=j<len(rows)}
        for r in rows:
            if not r['candidates']['band_calibrated_duration']:continue
            pr=r['projection']
            if pr.get('advisory_consistent',False):why='consistent'
            elif pr['valid_pairs']<3:why='insufficient_pairs'
            else:
                bad=[]
                if pr.get('residual_samples',0)>.5:bad.append('residual')
                if not .1<=pr.get('projection_norm',0)<=1.3:bad.append('norm')
                why='+'.join(bad) or pr['reason']
            all_gate_projection[why]+=1
        for i in sorted(selected):
            old=rows[i];pair,corr=diag.floating(pcm[old['start']:old['stop']],bounds)
            proj=diag.projection(pair,pos,fs,c)
            assert [p['reason'] for p in pair]==old['pair_reasons'],(name,i)
            assert proj.keys()==old['projection'].keys()
            for k,v in proj.items():
                ov=old['projection'][k]
                if isinstance(v,(float,list)):np.testing.assert_allclose(v,ov,rtol=1e-12,atol=1e-10)
                else:assert type(v)==type(ov) and v==ov,(name,i,k)
            for k,p in enumerate(pair):
                p['pair']=list(diag.PAIRS[k]);lim=int(np.ceil(bounds[k]));lags=np.arange(-lim,lim+1)
                p['legal_search_lags']=lags.tolist();p['correlation']=corr[k,lags%1024].tolist()
                if p.get('valid'):p['fit_residual_samples']=float(matrix[k]@np.array(proj.get('projection_xy',[0,0]))-p['tau_samples']) if 'projection_xy' in proj else None
            tau=[p.get('tau_samples') for p in pair]
            # 01+12=02, 01+13=03, 02+23=03, 12+23=13. Diagnostic only, no new gate.
            closure=[tau[a]+tau[b]-tau[d] if all(tau[k] is not None for k in (a,b,d)) else None
                     for a,b,d in [(0,3,1),(0,4,2),(1,5,2),(3,5,4)]]
            rec=dict(capture=name,index=i,start=old['start'],stop=old['stop'],first_id=old['first_id'],anchor=i in anchors,
                     marker_excluded=old['marker_excluded'],gate=old['candidates']['band_calibrated_duration'],
                     tracker=old['trackers']['candidate60'],projection=proj,pairs=pair,cycle_closure_samples=closure)
            records.append(rec)
        previous=[]
        for i,row in enumerate(rows):
            state=row['trackers']['candidate60'];a=row['numeric_angle']
            if state['state']!='ACQUIRE':previous=[];continue
            if state['acquire_count']==1 and previous:
                delta=[abs((a-rows[j]['numeric_angle']+180)%360-180) for j in previous]
                assert max(delta)>8-1e-10
                transitions.append(dict(capture=name,current_index=i,previous_indices=previous[:],
                                        previous_angles=[rows[j]['numeric_angle'] for j in previous],current_angle=a,
                                        max_angle_change_deg=max(delta)))
            if state['acquire_count']==1:previous=[]
            previous.append(i)
        groups.append(dict(capture=name,anchors=len(anchors),selected=len(selected)))
    bykey={(r['capture'],r['index']):r for r in records}
    for t in transitions:
        a=bykey[(t['capture'],t['current_index'])];b=bykey[(t['capture'],t['current_index']-1)]
        t['pairs_changed_integer_peak']=sum(x.get('peak')!=y.get('peak') for x,y in zip(a['pairs'],b['pairs']))
        t['max_tau_step_samples']=max(abs(x['tau_samples']-y['tau_samples']) for x,y in zip(a['pairs'],b['pairs']) if 'tau_samples' in x and 'tau_samples' in y)
        t['min_projection_norm']=min(a['projection']['projection_norm'],b['projection']['projection_norm'])
    classes={}
    for name,predicate in [('anchors',lambda r:r['anchor']),('neighbor_projection_rejected',lambda r:not r['anchor'] and not r['projection'].get('advisory_consistent',False)),('neighbor_other',lambda r:not r['anchor'] and r['projection'].get('advisory_consistent',False))]:
        selected=[r for r in records if predicate(r)];pair=[p for r in selected for p in r['pairs']]
        classes[name]=dict(frames=len(selected),pair_reasons=dict(Counter(p['reason'] for p in pair)),
                           edge_peaks=sum(p.get('edge_peak',False) for p in pair),
                           valid_pairs=sum(p['valid'] for p in pair),
                           margin=distribution(p['separated_peak_margin'] for p in pair if 'separated_peak_margin' in p),
                           residual=distribution(r['projection']['residual_samples'] for r in selected if 'residual_samples' in r['projection']),
                           norm=distribution(r['projection']['projection_norm'] for r in selected if 'projection_norm' in r['projection']))
    result=dict(status='SELECTED_REAL_INPUT_DIAGNOSTIC_ONLY',source_commit='fe67547635ff254f9f91c7f917e8dedb6daf3363',
                selection='all 137 candidate60 ACQUIRE anchors plus one immediate preceding/following frame, deduplicated',
                groups=groups,frames=len(records),anchors=sum(r['anchor'] for r in records),pair_evaluations=len(records)*6,
                all_787_gate_frames_projection=dict(all_gate_projection),classes=classes,
                spread_restarts=len(transitions),restart_angle_change=distribution(t['max_angle_change_deg'] for t in transitions),
                restarts_with_integer_peak_change=sum(t['pairs_changed_integer_peak']>0 for t in transitions),
                input_pins=pins,script_sha256=sha(Path(__file__)),
                environment=dict(python=platform.python_version(),numpy=np.__version__),
                hardware='NOT_RUN',production_changes=False,independent_validation=False)
    dump(out/'result.json',result);dump(out/'frames.json',records);dump(out/'spread-restarts.json',transitions)
    dump(out/'OUTPUT-SHA256.json',{p.name:sha(p) for p in out.iterdir() if p.is_file()})
    print(json.dumps({k:v for k,v in result.items() if k not in ('input_pins','classes','groups')},ensure_ascii=False,indent=2))
    print(json.dumps(classes,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();execute(a.repo.resolve(),a.out.resolve())
