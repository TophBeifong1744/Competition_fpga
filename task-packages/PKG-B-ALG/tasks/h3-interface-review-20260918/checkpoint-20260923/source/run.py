"""New candidate study only. Reuse accepted input/marker facts, no re-review."""
import argparse
from collections import Counter
import math
import platform
import sys
import traceback
import numpy as np
from common import ROOT,HERE,TASKS,BATCH,load,dump,sha,module,config,new_output
from candidates import features,BandActivity,decisions,direction_summary
from audio_candidate import render,measurements,das

diag = module('checkpoint_direction', TASKS/'c-board-algorithm-01/run.py')
tracker = module('checkpoint_tracker', ROOT/'task-packages/PKG-B-ALG/payload/model/python/sector_tracker.py')
POSITIONS = np.array([[0,0,0],[.04,0,0],[.04,.04,0],[0,.04,0]])
BOUNDS = [np.linalg.norm(POSITIONS[j]-POSITIONS[i])*48000/343 for i,j in diag.PAIRS]

def inside(row, interval):
    return row['start'] >= interval[0] and row['stop'] <= interval[1]

def intervals(marker,cfg):
    core = marker['common_source_mapped_interval_samples']
    exclusion = []
    for c in marker['channels']:
        scale = (c['end']-c['start'])/204000
        for begin in (c['start'],c['end']):
            exclusion.append([begin-cfg['marker_guard_ms']*48, begin+7200*scale+cfg['marker_guard_ms']*48])
    return {str(ms):[math.ceil(core[0]+ms*48), math.floor(core[1]-ms*48)] for ms in cfg['inner_guards_ms']}, exclusion

def execute(out):
    cfg=config()
    manifest=load(BATCH/'evidence/background-confirmation-20260920-01/CURRENT-DATA-SHA256.json')
    marker_list=load(ROOT/'docs/reviews/eight-94b5fe7/markers/results.json')['captures']
    markers={m['capture']:m for m in marker_list}
    baseline=load(ROOT/'docs/reviews/eight-94b5fe7/gate-frames.json')
    recordings={}
    pins={}
    for rel in manifest:
        if not rel.endswith('/metadata.json'):continue
        path=(BATCH/rel).parent
        for name in ['metadata.json','raw.bin']:
            p=path/name
            assert sha(p)==manifest[p.relative_to(BATCH).as_posix()]
            pins[p.relative_to(ROOT).as_posix()]=sha(p)
        meta=load(path/'metadata.json')
        assert meta['sample_rate_hz']==48000 and meta['channel_order']==['mic0','mic1','mic2','mic3']
        assert meta['coordinates_m']==POSITIONS.tolist()
        words=np.fromfile(path/'raw.bin',dtype='<u4').reshape(-1,8)
        assert len(words)==288250 and not words[:,6:].any()
        ids=words[:,0].astype(np.uint64)+(words[:,1].astype(np.uint64)<<32)
        assert np.all(np.diff(ids)==1)
        pcm=words[:,2:6].view('<i4').astype(np.int64)
        name=path.name
        frames=[]
        for k,start in enumerate(range(0,len(pcm)-1023,512)):
            f=features(pcm[start:start+1024],*cfg['band_bins_inclusive'])
            prior=baseline[name][k]
            assert (prior['start'],prior['stop'])==(start,start+1024)
            frames.append(dict(start=start,stop=start+1024,features=f,baseline_present=prior['present']))
        recordings[name]=dict(pcm=pcm,ids=ids,frames=frames)
    assert set(recordings)==set(cfg['design_runs']+cfg['development_probe_runs'])
    # Calibration ONLY from the pre-design background Run; never probe or target.
    calibration=recordings[cfg['calibration_run']]['frames']
    noise=np.percentile([r['features']['band_power'] for r in calibration],cfg['background_percentile'],axis=0)
    dump(out/'calibration.json',dict(run=cfg['calibration_run'],method='numpy linear percentile95 of per-channel band power',
        frames=len(calibration),noise_power_codes_squared=noise.tolist(),
        effective_on_power=(cfg['on_power_ratio']*np.maximum(noise,cfg['band_rms_floor_codes']**2)).tolist(),
        effective_off_power=(cfg['off_power_ratio']*np.maximum(noise,cfg['band_rms_floor_codes']**2)).tolist(),
        config_sha256=sha(HERE/'config.json'),probe_used=False))
    reports=[]
    audio_dir=out/'audio';audio_dir.mkdir()
    for name,item in recordings.items():
        frames=item['frames']; pcm=item['pcm']
        background=name not in markers
        nominal=None if background else -45 if '_m045_' in name else 45 if '_p045_' in name else 0
        masks,exclusion=({},[]) if background else intervals(markers[name],cfg)
        gate=BandActivity(noise,cfg)
        tracks={key:tracker.Tracker(tracker.Config(cone_half_angle_deg=cone)) for key,cone in
                [('baseline30',30),('ungated60',60),('candidate60',cfg['tracker_cone_half_angle_deg'])]}
        events=[]
        for row in frames:
            row['candidates']=decisions(row['features'],gate,cfg)
            pair_rows,_=diag.floating(pcm[row['start']:row['stop']],BOUNDS)
            projection=diag.projection(pair_rows,POSITIONS,48000,343)
            row['projection']=projection
            row['pair_reasons']=[p['reason'] for p in pair_rows]
            valid=projection.get('advisory_consistent',False)
            angle=projection.get('advisory_azimuth_deg') if valid else None
            row['numeric_angle']=angle
            vector=None if angle is None else [math.cos(math.radians(angle)),math.sin(math.radians(angle)),0]
            ready=row['stop']
            row['trackers']={}
            for key,t in tracks.items():
                enabled=True if key=='ungated60' else row['baseline_present'] if key=='baseline30' else row['candidates']['band_calibrated_duration']
                # Candidate no-activity is an explicit release, not a new DOA.
                if key=='candidate60' and not enabled:t.reset()
                state=t.update(ready/48,vector,valid and enabled)
                row['trackers'][key]=state
                d=state['direction']
                row[key+'_angle']=None if d is None else math.degrees(math.atan2(d[1],d[0]))
            state=row['trackers']['candidate60']
            d=state['display_direction']
            event_angle=None if d is None else cfg['audio_angle_step_deg']*round(math.degrees(math.atan2(d[1],d[0]))/cfg['audio_angle_step_deg'])
            events.append(dict(ready=ready,angle=event_angle,fresh=state['fresh_valid'],
                valid_through=None if d is None else round(state['display_expires_at_ms']*48)))
            row['marker_excluded']=any(row['start']<b and row['stop']>a for a,b in exclusion)
            row['first_id']=str(int(item['ids'][row['start']]))
        summary=dict(capture=name,split='design' if name in cfg['design_runs'] else 'development_probe_not_independent',
                     nominal_deg=nominal,frames=len(frames),background_operator_label=background,
                     sensitivity={},formal_metrics=None)
        selected_groups={'reported_background':frames} if background else {
            g:[r for r in frames if inside(r,v) and not r['marker_excluded']] for g,v in masks.items()}
        for group,selected in selected_groups.items():
            gate_counts={'frozen_baseline':sum(r['baseline_present'] for r in selected)}
            gate_counts.update({key:sum(r['candidates'][key] for r in selected) for key in
                ['dc_only','band_absolute','band_calibrated_duration']})
            summary['sensitivity'][group]=dict(frames=len(selected),gate_pass=gate_counts,
                direction={key:direction_summary(selected,nominal,key+'_angle',cfg['wrong_direction_threshold_deg'])
                    for key in ['baseline30','ungated60','candidate60']},
                numeric=direction_summary(selected,nominal,'numeric_angle',cfg['wrong_direction_threshold_deg']))
        # Scoring intervals are not used by the gate, estimator, tracker or renderer.
        output,detail=render(pcm,0 if nominal is None else nominal,events,cfg)
        files=[]
        for branch,signal in output.items():
            for mode,gain in [('raw',1),('preview',cfg['audio_preview_gain'])]:
                p=audio_dir/f'{name}-{branch}-{mode}.wav'
                info=das.write_wav(p,signal*gain,48000)
                assert info['saturation_samples']==0
                info.update(file=p.name,branch=branch,mode=mode,gain=gain)
                files.append(info)
        np.testing.assert_array_equal(np.rint(output['single']*2**23).astype(np.int64),pcm[8:-8,0])
        region=[8,len(pcm)-8] if background else masks['200']
        selection=np.arange(max(8,region[0]),min(len(pcm)-8,region[1]))-8
        detail.update(files=files,manual_deg=0 if nominal is None else nominal,manual_is_ground_truth=False,
            evaluation_reference_rows=region,descriptive_audio=measurements(output,selection),
            listening_status='NOT_LISTENED',objective_benefit='NOT_MEASURABLE_NO_SYNCHRONOUS_COMPONENT_REFERENCE')
        dump(out/(name+'-frames.json'),frames)
        dump(out/(name+'-audio.json'),dict(events=events,**detail))
        summary['audio']=detail
        summary['failure_examples']=[dict(start=r['start'],nominal_deg=nominal,numeric_angle=r['numeric_angle'],
            gate=r['candidates']['band_calibrated_duration'],tracker=r['trackers']['candidate60'])
            for r in (selected_groups.get('200',frames))
            if r['candidate60_angle'] is None or (nominal is not None and abs((r['candidate60_angle']-nominal+180)%360-180)>15)][:8]
        reports.append(summary)
        print(name,summary['sensitivity'].get('200',summary['sensitivity'].get('reported_background'))['gate_pass'],flush=True)
    assert all(sha(ROOT/p)==v for p,v in pins.items())
    dump(out/'summary.json',dict(status='AUTHOR_DEVELOPMENT_ONLY_NOT_ACCEPTANCE',config=cfg,pins=pins,
        environment=dict(python=platform.python_version(),numpy=np.__version__),reports=reports,
        baseline_reused='94b5fe7 B archived gate frames; no old review rerun',
        hardware='NOT_RUN',independent_validation=False))
    dump(out/'OUTPUT-SHA256.json',{p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob('*')) if p.is_file()})

if __name__=='__main__':
    parser=argparse.ArgumentParser(__doc__);parser.add_argument('--out',required=True)
    out=new_output(parser.parse_args().out)
    try:execute(out)
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
