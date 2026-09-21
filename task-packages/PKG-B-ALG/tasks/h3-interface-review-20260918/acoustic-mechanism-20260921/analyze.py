"""Frozen-feature attribution and one preregistered causal smoothing probe.
No waveform generation, FFT rerun, threshold tuning or independent-test claim.
"""
import argparse
from collections import deque
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import numpy as np

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def longest(values):
    best=n=0
    for v in values:n=n+1 if v else 0;best=max(best,n)
    return best
def quant(v):return None if not len(v) else dict(zip(('p05','p50','p95'),map(float,np.percentile(v,[5,50,95]))))

def simulate(rows,mod,mode):
    t=mod.Tracker(mod.Config(cone_half_angle_deg=60));history=deque(maxlen=5);outputs=[]
    for r in rows:
        active=r['candidates']['band_calibrated_duration'];valid=r['projection'].get('advisory_consistent',False)
        angle=r['numeric_angle'];vec=None;ready=False
        if not active:t.reset()
        if mode=='raw':
            ready=active and valid
            if ready:vec=[math.cos(math.radians(angle)),math.sin(math.radians(angle)),0]
        elif mode=='causal5':
            if not(active and valid):history.clear()
            else:history.append([math.cos(math.radians(angle)),math.sin(math.radians(angle)),0])
            if len(history)==5:
                vec=np.mean(history,axis=0);ready=float(np.linalg.norm(vec))>=1e-12
        else:
            # Deliberately impossible diagnostic intervention: perfect in-cone
            # directions. Never a deployable candidate or accuracy estimate.
            ready=active and (valid if mode=='oracle_valid' else True);vec=[1,0,0]
        state=t.update(r['stop']/48,vec,ready)
        if mode=='raw':assert state==r['trackers']['candidate60']
        d=state['direction']
        outputs.append(dict(start=r['start'],fresh=state['fresh_valid'],state=state['state'],reason=state['reason'],acquire=state['acquire_count'],angle=None if d is None else math.degrees(math.atan2(d[1],d[0]))))
    return outputs

def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    repo=a.repo.resolve();cp=repo/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923'
    seal=load(cp/'SNAPSHOT-SHA256.json')['files'];pins={}
    def frozen(p):
        h=sha(p);assert h==seal[p.relative_to(cp.parent).as_posix()],p;pins[p.relative_to(repo).as_posix()]=h;return load(p)
    cfg=frozen(cp/'config.json');summary=frozen(cp/'evidence/run01/summary.json');cal=frozen(cp/'evidence/run01/calibration.json')
    source=repo/'task-packages/PKG-B-ALG/payload/model/python/sector_tracker.py'
    assert sha(source)==load(cp/'dependencies.json')[source.relative_to(repo).as_posix()];pins[source.relative_to(repo).as_posix()]=sha(source)
    spec=importlib.util.spec_from_file_location('acoustic_tracker',source);mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
    markers_path=repo/'docs/reviews/eight-94b5fe7/markers/results.json';pins[markers_path.relative_to(repo).as_posix()]=sha(markers_path)
    assert sha(markers_path)==load(cp/'dependencies.json')[markers_path.relative_to(repo).as_posix()]
    markers={r['capture']:r for r in load(markers_path)['captures']}
    # Written before running any capture. No sweep or per-capture parameter fit.
    protocol=dict(window=5,warmup='five consecutive gate+projection valid inputs',clear_on='gate or projection invalid',tracker='unchanged 5-frame/8-degree, cone60',calibration='frozen pre-background only',groups=['whole_recording','100','200','300'],all_eight_previously_inspected=True,oracle_modes='diagnostic hypothetical constant +X, not an implementation',fft_calls=0)
    dump(a.out/'protocol.json',protocol)
    reports=[];traces={};checks=0
    originals={r['capture']:r for r in summary['reports']}
    for path in sorted((cp/'evidence/run01').glob('*-frames.json')):
        rows=frozen(path);name=path.name[:-12];background=name not in markers;nominal=originals[name]['nominal_deg']
        states={k:simulate(rows,mod,k) for k in ('raw','causal5','oracle_valid','oracle_gate')}
        # Prefix invariance against removal of future frames, exact states/codes.
        for stop in (137,333):assert simulate(rows[:stop],mod,'causal5')==states['causal5'][:stop];checks+=1
        groups={'whole_recording':list(range(len(rows)))}
        if not background:
            core=markers[name]['common_source_mapped_interval_samples']
            for ms in cfg['inner_guards_ms']:
                lo=math.ceil(core[0]+ms*48);hi=math.floor(core[1]-ms*48)
                groups[str(ms)]=[i for i,r in enumerate(rows) if r['start']>=lo and r['stop']<=hi and not r['marker_excluded']]
        power=np.array([r['features']['band_power'] for r in rows]);raw=np.array([r['features']['raw_rms'] for r in rows]);center=np.array([r['features']['centered_rms'] for r in rows])
        noise=np.maximum(np.array(cal['noise_power_codes_squared']),cfg['band_rms_floor_codes']**2)
        section={}
        for group,ids in groups.items():
            selected=[rows[i] for i in ids]
            if not ids:continue
            gates=dict(baseline=sum(r['baseline_present'] for r in selected),**{k:sum(r['candidates'][k] for r in selected) for k in ('dc_only','band_absolute','band_calibrated_duration')})
            source_group='reported_background' if background else group
            if source_group in originals[name]['sensitivity']:
                prior=originals[name]['sensitivity'][source_group];assert len(ids)==prior['frames'];assert gates['baseline']==prior['gate_pass']['frozen_baseline'];assert gates['band_calibrated_duration']==prior['gate_pass']['band_calibrated_duration']
            metrics={}
            for mode,values in states.items():
                out=[values[i] for i in ids];angles=[v['angle'] for v in out if v['fresh']]
                errors=[] if nominal is None or mode.startswith('oracle') else [abs((v-nominal+180)%360-180) for v in angles]
                metrics[mode]=dict(fresh=len(angles),hold=sum(v['state']=='HOLD' for v in out),max_acquire=max((v['acquire'] for v in out),default=0),nominal_deviation=quant(errors),nominal_gt15=sum(v>15 for v in errors) if errors else None)
            active=[r for r in selected if r['candidates']['band_calibrated_duration']]
            valid=[r for r in active if r['projection'].get('advisory_consistent',False)]
            in_cone=[r for r in valid if abs(r['numeric_angle'])<=60+1e-10]
            section[group]=dict(frames=len(ids),gates=gates,gate_then_projection=len(valid),gate_then_projection_then_cone=len(in_cone),trackers=metrics,raw_rms=quant(raw[ids].ravel()),centered_rms=quant(center[ids].ravel()),dc_power_fraction=quant(np.maximum(0,1-center[ids]**2/np.maximum(raw[ids]**2,1)).ravel()),band_to_centered_power_fraction=quant((power[ids]/np.maximum(center[ids]**2,1)).ravel()),third_largest_band_to_noise_ratio=quant(np.sort(power[ids]/noise,axis=1)[:,1]))
        continuous={}
        for label,predicate in [('gate',lambda r:r['candidates']['band_calibrated_duration']),('gate_projection',lambda r:r['candidates']['band_calibrated_duration'] and r['projection'].get('advisory_consistent',False)),('gate_projection_cone',lambda r:r['candidates']['band_calibrated_duration'] and r['projection'].get('advisory_consistent',False) and abs(r['numeric_angle'])<=60+1e-10)]:continuous[label]=longest([predicate(r) for r in rows])
        reports.append(dict(capture=name,split=originals[name]['split'],background_operator_label=background,groups=section,longest_whole_recording_runs=continuous))
        traces[name]=states
    dump(a.out/'report.json',dict(protocol=protocol,pins=pins,captures=reports,prefix_checks=checks,formal_acceptance=False))
    dump(a.out/'traces.json',traces)
    for r in reports:
        s=r['groups'].get('200',r['groups']['whole_recording']);print(r['capture'],s['frames'],s['gates'],{k:v['fresh'] for k,v in s['trackers'].items()},r['longest_whole_recording_runs'])
    dump(a.out/'OUTPUT-SHA256.json',{p.name:sha(p) for p in a.out.iterdir() if p.is_file()})

if __name__=='__main__':main()
