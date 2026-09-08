"""Develop capture variants on frozen seeds, then evaluate one frozen choice on new seeds."""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import platform
import numpy as np
import batch_presence as batch
import six_mic_localize as entry
from six_mic_track import load_config
from quorum_tracker import CaptureConfig,QuorumSession
from sector_tracker import angle,vector

ROOT=Path(__file__).resolve().parents[3]
PROTOCOL=ROOT/'payload/config/capture-research-protocol.json'
REFERENCE=ROOT/'reference/batch-presence-fixed/frozen-files.json'


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def verify_reference():
    for name,h in read(REFERENCE)['files'].items():
        if entry.sha256(ROOT/name)!=h:raise ValueError('fixed reference changed: '+name)


def sources():
    directory=Path(__file__).resolve().parent
    return {p.name:entry.sha256(p) for p in [directory/name for name in
        ['capture_research.py','quorum_tracker.py','batch_presence.py','sector_tracker.py','six_mic_track.py',
         'six_mic_localize.py','six_mic_baseline_core.py','audio_frames.py','h1_reader.py']]}


def load_development():
    groups=defaultdict(list)
    with (ROOT/'evidence/batch-presence-run-01/frames.csv').open(encoding='utf-8',newline='') as f:
        for raw in csv.DictReader(f):
            r=dict(raw)
            for key in ['seed','frame_index','row_start','row_stop']:r[key]=int(r[key])
            r['episode']=int(r['episode']) if r['episode'] else None
            for key in ['timestamp_ms','error_deg','estimate_x','estimate_y','estimate_z','residual_samples','display_expires_at_ms']:
                r[key]=float(r[key]) if r[key] else None
            for key in ['fresh_valid','stale','baseline_valid']:r[key]=r[key]=='True'
            groups[r['scenario'],r['seed']].append(r)
    return groups


def replay(base_rows,plan,config,candidate):
    capture=CaptureConfig(**{k:candidate[k] for k in ['required','window_frames','max_span_ms']})
    session=QuorumSession(config,capture);result=[]
    for row in base_rows:
        estimate=[row['estimate_'+axis] for axis in 'xyz'] if row['fresh_valid'] else None
        output=session.update(dict(end_seconds_exclusive=row['timestamp_ms']/1000,
                                   reset_before=row['frame_index']==0,valid=row['fresh_valid'],unit_vector=estimate))
        direction=output['direction'];error=None
        if output['fresh_valid'] and row['scope']=='target_active':
            episode=plan['episodes'][row['episode']]
            truth=batch.b.unit(episode['azimuth_deg'],episode['elevation_deg'])
            error=angle(truth,np.asarray(direction))
        result.append(row|dict(method=candidate['name'],fresh_valid=output['fresh_valid'],state=output['state'],
            reason=output['reason'],stale=output['stale'],error_deg=error,
            estimate_x=direction[0] if direction is not None else None,
            estimate_y=direction[1] if direction is not None else None,
            estimate_z=direction[2] if direction is not None else None,
            display_expires_at_ms=output['display_expires_at_ms']))
    return result


def gate(pooled,candidate,protocol):
    index={(r['scenario'],r['method']):r for r in pooled}
    old=index['band_noise0','tracker'];new=index['band_noise0',candidate]
    limits=protocol['gates'];scenarios=batch.SCENARIOS
    checks=dict(noise_correct_gain=new['active_correct_within10_rate']-old['active_correct_within10_rate']>=limits['noise_correct_within10_gain_min'],
        noise_p95=new['p95_error_deg'] is not None and new['p95_error_deg']<=limits['noise_p95_max_deg'],
        absent_false_outputs=all(index[s,candidate]['absent_false_output_rate']-index[s,'tracker']['absent_false_output_rate']<=limits['each_scenario_absent_false_increase_max']+1e-12 for s in scenarios),
        normal_correct=index['drop_return',candidate]['active_correct_within10_rate']>=index['drop_return','tracker']['active_correct_within10_rate']-limits['normal_correct_within10_drop_max'],
        noise_wrong=new['active_wrong_rate_all']-old['active_wrong_rate_all']<=limits['noise_wrong_over30_rate_all_increase_max']+1e-12)
    return dict(passed=all(checks.values()),checks=checks)


def diagnose(groups,config):
    results=[];center=vector(config.cone_center)
    for (scenario,seed),rows in groups.items():
        if scenario!='band_noise0':continue
        base=[r for r in rows if r['method']=='baseline']
        consecutive=[];maximum=0;windows=0;stable=0
        for r in base:
            u=np.array([r['estimate_'+a] for a in 'xyz']) if r['fresh_valid'] else None
            if u is None or angle(center,u)>config.cone_half_angle_deg+1e-10:consecutive=[];continue
            consecutive.append(u);maximum=max(maximum,len(consecutive))
            if len(consecutive)>=5:
                windows+=1;last=consecutive[-5:]
                stable+=all(angle(a,b)<=config.acquire_spread_deg+1e-10 for i,a in enumerate(last) for b in last[i+1:])
        active=[r for r in base if r['scope']=='target_active']
        results.append(dict(seed=seed,active_frames=len(active),baseline_active_valid=sum(r['fresh_valid'] for r in active),
                            longest_consecutive_candidates=maximum,consecutive_five_windows=windows,
                            pairwise_stable_five_windows=stable))
    return results


def execute(phase,out,selection_path=None):
    verify_reference();protocol=read(PROTOCOL)
    if set(protocol['development_seeds'])&set(protocol['validation_seeds']):raise ValueError('seed overlap')
    plan=batch.load_plan(ROOT/'payload/config/batch-presence.json')
    config=load_config(ROOT/'payload/config/sector-tracking.json')
    if phase=='develop':
        if plan['seeds']!=protocol['development_seeds']:raise ValueError('development split mismatch')
        candidates=protocol['candidates'];groups=load_development()
    else:
        if selection_path is None:raise ValueError('validation requires a frozen development selection')
        selection=read(selection_path)
        if selection['protocol_sha256']!=entry.sha256(PROTOCOL) or selection['source_sha256']!=sources():
            raise ValueError('selected code/protocol changed before validation')
        if selection['selected'] is None:raise ValueError('no development candidate passed')
        candidates=[selection['selected']];groups={};plan=plan|dict(seeds=protocol['validation_seeds'])
    out=Path(out)
    if out.exists():raise ValueError('output path must be new')
    out.mkdir(parents=True)
    entry.write_json(out/'protocol.json',protocol)
    entry.write_json(out/'plan.json',plan)
    all_rows=[];per_seed=[];latencies=[];input_records=[]
    for scenario in plan['scenarios']:
        for seed in plan['seeds']:
            if phase=='develop':
                rows=groups[scenario,seed]
            else:
                segment,env,directions=batch.generate(plan,scenario,seed)
                raw,annotations=batch.evaluate(segment,env,directions,config)
                rows=[dict(scenario=scenario,seed=seed,**r) for r in raw]
                input_records.append(dict(scenario=scenario,seed=seed,input_sha256=segment.provenance['samples_sha256'],
                                           annotation_sha256=__import__('hashlib').sha256(json.dumps(annotations,sort_keys=True).encode()).hexdigest()))
            base=[r for r in rows if r['method']=='baseline']
            extended=list(rows)
            for candidate in candidates:extended+=replay(base,plan,config,candidate)
            all_rows.extend(extended)
            for method in ['baseline','cone_only','tracker']+[c['name'] for c in candidates]:
                group=[r for r in extended if r['method']==method]
                per_seed.append(dict(scenario=scenario,seed=seed,method=method,**batch.summarize(group)))
                # Reuse exact reference latency definition by mapping this method temporarily.
                mapped=[r|dict(method='baseline') for r in group]
                latencies.extend(dict(scenario=scenario,seed=seed,**(r|dict(method=method))) for r in batch.latencies(mapped,plan) if r['method']=='baseline')
            print(f'{phase}: {scenario} seed={seed}',flush=True)
    methods=['baseline','cone_only','tracker']+[c['name'] for c in candidates]
    pooled=[dict(scenario=s,method=m,**batch.summarize([r for r in all_rows if r['scenario']==s and r['method']==m])) for s in plan['scenarios'] for m in methods]
    paired=[]
    for candidate in candidates:
        for scenario in plan['scenarios']:
            for seed in plan['seeds']:
                index={r['method']:r for r in per_seed if r['scenario']==scenario and r['seed']==seed}
                for metric in ['active_fresh_rate','active_correct_within10_rate','active_wrong_rate_all','absent_false_output_rate']:
                    a,b=index[candidate['name']][metric],index['tracker'][metric]
                    paired.append(dict(scenario=scenario,seed=seed,variant=candidate['name'],metric=metric,
                                       delta=a-b if a is not None and b is not None else None))
    for name,data in [('frames',all_rows),('per-seed',per_seed),('pooled',pooled),('paired',paired),('latencies',latencies)]:
        batch.write_csv(out/(name+'.csv'),data)
    entry.write_json(out/'pooled.json',pooled)
    gates={c['name']:gate(pooled,c['name'],protocol) for c in candidates}
    entry.write_json(out/'gates.json',gates)
    if phase=='develop':
        selected=next((c for c in candidates if gates[c['name']]['passed']),None)
        entry.write_json(out/'diagnosis.json',diagnose(groups,config))
        entry.write_json(out/'selection.json',dict(selected=selected,gates=gates,protocol_sha256=entry.sha256(PROTOCOL),
            source_sha256=sources(),note='Frozen before new-seed validation; prefer declared stricter quorum if both pass.'))
    else:entry.write_json(out/'validation-inputs.json',input_records)
    verify_reference()
    entry.write_json(out/'run.json',dict(status='COMPLETE_RESEARCH',phase=phase,seeds=plan['seeds'],
        selected_from_sha256=entry.sha256(selection_path) if selection_path else None,source_sha256=sources(),
        protocol_sha256=entry.sha256(PROTOCOL),fixed_reference_manifest_sha256=entry.sha256(REFERENCE),
        method_rows=len(all_rows),acoustic_frames=len(plan['scenarios'])*len(plan['seeds'])*467,
        artifact_sha256={p.name:entry.sha256(p) for p in sorted(out.iterdir()) if p.is_file()},
        python=platform.python_version(),numpy=np.__version__,
        scope='Capture-only synthetic research. No automatic replacement of production tracker. Same-cone identity limitation remains.'))
    print(json.dumps(gates));return gates


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--phase',choices=['develop','validate'],required=True)
    parser.add_argument('--selection',type=Path);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    try:execute(args.phase,args.out,args.selection)
    except (ValueError,OSError,TypeError) as error:
        print(json.dumps(dict(status='ERROR',message=str(error))));return 2
    return 0


if __name__=='__main__':raise SystemExit(main())
