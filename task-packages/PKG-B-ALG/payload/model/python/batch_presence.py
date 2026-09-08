"""Paired multi-seed evaluation. Presence truth is used only after localization/tracking."""
from __future__ import annotations
import argparse
from collections import Counter
from dataclasses import asdict
import csv
import json
from pathlib import Path
import platform
import sys
import numpy as np

import six_mic_baseline_core as b
import six_mic_localize as entry
from audio_frames import adapt_six_mic_baseline
from six_mic_track import TrackingSession,load_config
from sector_tracker import angle,vector
from h1_reader import unique_object,bad_constant

SCENARIOS=['drop_return','band_noise0','equal_interferer','interferer_only','same_cone_competitor']
METHODS=['baseline','cone_only','tracker']


def load_plan(path):
    plan=json.loads(Path(path).read_text(encoding='utf-8'),object_pairs_hook=unique_object,parse_constant=bad_constant)
    if not isinstance(plan,dict) or set(plan)!={'seeds','scenarios','duration_samples','margin_samples','edge_samples','episodes'}:
        raise ValueError('unsupported experiment plan fields')
    seeds=plan['seeds']
    if not isinstance(seeds,list) or not seeds or any(type(s) is not int or not 0<=s<2**32 for s in seeds) or len(set(seeds))!=len(seeds):
        raise ValueError('seeds must be unique uint32 integers')
    scenarios=plan['scenarios']
    if not isinstance(scenarios,list) or not scenarios or any(s not in SCENARIOS for s in scenarios) or len(set(scenarios))!=len(scenarios):
        raise ValueError('scenarios must be unique supported names')
    for key in ['duration_samples','margin_samples','edge_samples']:
        if type(plan[key]) is not int or plan[key]<=0:raise ValueError(key)
    if plan['duration_samples']<1024 or plan['margin_samples']<1536:raise ValueError('duration or rendering margin too short')
    episodes=plan['episodes'];last=0
    if not isinstance(episodes,list) or not episodes:raise ValueError('episodes required')
    for episode in episodes:
        if not isinstance(episode,dict) or set(episode)!={'start','stop','azimuth_deg','elevation_deg'}:raise ValueError('episode fields')
        start,stop=episode['start'],episode['stop']
        if type(start) is not int or type(stop) is not int or not last<=start<stop<=plan['duration_samples'] or stop-start<=2*plan['edge_samples']:
            raise ValueError('episodes must not overlap and need a full-amplitude interior')
        for key,low,high in [('azimuth_deg',-180,360),('elevation_deg',-90,90)]:
            value=episode[key]
            if type(value) not in (int,float) or not np.isfinite(value) or not low<=value<=high:raise ValueError(key)
        last=stop
    return plan


def envelope(indices,start,stop,edge):
    value=np.zeros(len(indices),dtype=float)
    value[(indices>=start+edge)&(indices<=stop-edge)]=1
    up=(indices>=start)&(indices<start+edge)
    down=(indices>stop-edge)&(indices<stop)
    value[up]=.5-.5*np.cos(np.pi*(indices[up]-start)/edge)
    value[down]=.5-.5*np.cos(np.pi*(stop-indices[down])/edge)
    return value


def target_envelopes(plan,scenario):
    index=np.arange(plan['duration_samples']+2*plan['margin_samples'])-plan['margin_samples']
    env=np.array([envelope(index,e['start'],e['stop'],plan['edge_samples']) for e in plan['episodes']])
    if scenario=='interferer_only':env[:]=0
    return env


def label_frame(envelopes,start,stop,directions):
    part=envelopes[:,start:stop]
    if part.shape[1]!=stop-start or stop<=start:raise ValueError('invalid annotation window')
    active=[i for i,e in enumerate(part) if np.all(e>=1-1e-12)]
    absent=bool(np.all(part==0))
    episode=active[0] if len(active)==1 else None
    scope='target_absent' if absent else 'target_active' if episode is not None else 'transition'
    return dict(scope=scope,episode=episode,
                target_unit_vector=directions[episode].tolist() if episode is not None else None,
                active_sample_count=int(np.count_nonzero(np.any(part>0,axis=0))),
                full_amplitude_sample_count=int(np.count_nonzero(np.any(part>=1-1e-12,axis=0))))


def probe(rng,count):
    freq=np.fft.rfftfreq(count,1/b.FS)
    weight=np.clip((freq-200)/200,0,1)*np.clip((4400-freq)/600,0,1)
    signal=np.fft.irfft(np.fft.rfft(rng.normal(size=count))*weight,n=count)
    return signal/np.std(signal)


def generate(plan,scenario,seed):
    env=target_envelopes(plan,scenario);count=env.shape[1]
    # Independent streams make target/noise/competitor reproducible across scenarios.
    streams=[np.random.default_rng(np.random.SeedSequence([seed,i])) for i in range(4)]
    x,z=probe(streams[0],count),probe(streams[1],count)
    directions=[b.unit(e['azimuth_deg'],e['elevation_deg']) for e in plan['episodes']]
    target=sum(b.render(x,u)*e for u,e in zip(directions,env))
    mixture=target+streams[2].normal(size=target.shape)*.1
    if scenario=='band_noise0':mixture=target+np.array([probe(streams[3],count) for _ in range(6)])
    if scenario in ['equal_interferer','interferer_only','same_cone_competitor']:
        mixture+=b.render(z,b.unit(20 if scenario=='same_cone_competitor' else 90,0))
    margin=plan['margin_samples'];stop=margin+plan['duration_samples']
    samples=mixture[:,margin:stop]
    segment=adapt_six_mic_baseline(samples,sample_rate_hz=48000,positions_m=b.POS,
        source_id=f'batch-presence:{scenario}:seed={seed}',source_sha256=entry.sha256(__file__),first_sample_id=margin)
    return segment,env[:,margin:stop],directions


def evaluate(segment,envelopes,directions,config):
    # Do not pass truth, episode, source presence or scene labels to either estimator.
    baseline_rows,_=entry.run_segment(segment,truth=None)
    tracker=TrackingSession(config);center=vector(config.cone_center)
    rows=[];annotations=[]
    for base in baseline_rows:
        tracked=tracker.update(base)
        sector=bool(base['valid'] and angle(center,np.asarray(base['unit_vector']))<=config.cone_half_angle_deg+1e-10)
        label=label_frame(envelopes,base['row_start'],base['row_stop'],directions)
        annotations.append(dict(frame_index=base['index'],row_start=base['row_start'],row_stop=base['row_stop'],
                                first_sample_id=base['first_sample_id'],last_sample_id=base['last_sample_id'],**label))
        candidates=[('baseline',base['valid'],base['unit_vector'],'FRAME','accepted' if base['valid'] else 'baseline_rejected',False),
                    ('cone_only',sector,base['unit_vector'] if sector else None,'FRAME',
                     'accepted' if sector else 'outside_cone' if base['valid'] else 'baseline_rejected',False),
                    ('tracker',tracked['fresh_valid'],tracked['direction'],tracked['state'],tracked['reason'],tracked['stale'])]
        for method,fresh,estimate,state,reason,stale in candidates:
            error=angle(np.asarray(label['target_unit_vector']),np.asarray(estimate)) if fresh and label['scope']=='target_active' else None
            rows.append(dict(frame_index=base['index'],row_start=base['row_start'],row_stop=base['row_stop'],
                timestamp_ms=base['end_seconds_exclusive']*1000,method=method,scope=label['scope'],episode=label['episode'],
                fresh_valid=bool(fresh),state=state,reason=reason,stale=stale,error_deg=error,
                estimate_x=estimate[0] if fresh else None,estimate_y=estimate[1] if fresh else None,estimate_z=estimate[2] if fresh else None,
                baseline_valid=base['valid'],residual_samples=base['residual_samples'],
                display_expires_at_ms=tracked['display_expires_at_ms'] if method=='tracker' else None))
    return rows,annotations


def summarize(rows):
    active=[r for r in rows if r['scope']=='target_active']
    absent=[r for r in rows if r['scope']=='target_absent']
    errors=[r['error_deg'] for r in active if r['fresh_valid']]
    n,v=len(active),len(errors);wrong=sum(e>30 for e in errors)
    false=sum(r['fresh_valid'] for r in absent)
    return dict(all_frames=len(rows),active_frames=n,active_fresh_frames=v,
        active_fresh_rate=v/n if n else None,p50_error_deg=float(np.percentile(errors,50)) if v else None,
        p95_error_deg=float(np.percentile(errors,95)) if v else None,
        active_wrong_over30=wrong,active_wrong_rate_all=wrong/n if n else None,
        active_wrong_rate_fresh=wrong/v if v else None,
        active_correct_within10_rate=sum(e<=10 for e in errors)/n if n else None,
        absent_frames=len(absent),absent_fresh_false_outputs=false,
        absent_false_output_rate=false/len(absent) if absent else None,
        absent_hold_display_frames=sum(r['stale'] for r in absent),
        transition_frames=sum(r['scope']=='transition' for r in rows),
        transition_fresh_outputs=sum(r['fresh_valid'] for r in rows if r['scope']=='transition'),
        hold_frames=sum(r['stale'] for r in rows))


def latencies(rows,plan):
    result=[]
    for method in METHODS:
        group=[r for r in rows if r['method']==method]
        for index,episode in enumerate(plan['episodes']):
            eligible=[r for r in group if r['scope']=='target_active' and r['episode']==index]
            correct=[r for r in eligible if r['fresh_valid'] and r['error_deg']<=10]
            result.append(dict(method=method,episode=index,onset_ms=episode['start']/48,
                applicable=bool(eligible),found=bool(correct),
                first_correct_ready_ms=correct[0]['timestamp_ms'] if correct else None,
                onset_to_first_correct_ms=correct[0]['timestamp_ms']-episode['start']/48 if correct else None))
    return result


def write_csv(path,rows):
    with Path(path).open('w',encoding='utf-8',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def run(plan,config,out,plan_path=None,config_path=None):
    out=Path(out)
    if out.exists():raise ValueError('output path must be new')
    out.mkdir(parents=True);(out/'annotations').mkdir();(out/'trials').mkdir()
    entry.write_json(out/'frozen-plan.json',plan)
    entry.write_json(out/'tracking-config.json',asdict(config))
    all_rows=[];per_seed=[];latency_rows=[];trials=[]
    for scenario in plan['scenarios']:
        for seed in plan['seeds']:
            segment,env,directions=generate(plan,scenario,seed)
            rows,annotations=evaluate(segment,env,directions,config)
            tagged=[dict(scenario=scenario,seed=seed,**r) for r in rows]
            all_rows.extend(tagged)
            for method in METHODS:
                per_seed.append(dict(scenario=scenario,seed=seed,method=method,
                                     **summarize([r for r in rows if r['method']==method])))
            latency_rows.extend(dict(scenario=scenario,seed=seed,**r) for r in latencies(rows,plan))
            annotation_file=out/'annotations'/f'{scenario}.json'
            if annotation_file.exists():
                if json.loads(annotation_file.read_text(encoding='utf-8'))!=annotations:raise ValueError('annotation depends on random seed')
            else:entry.write_json(annotation_file,annotations)
            record=dict(scenario=scenario,seed=seed,frame_count=len(annotations),input_shape=list(segment.samples.T.shape),
                input_sha256_time_major_float64=segment.provenance['samples_sha256'],
                annotation_sha256=entry.sha256(annotation_file),
                presence_counts=dict(Counter(a['scope'] for a in annotations)))
            entry.write_json(out/'trials'/f'{scenario}-{seed}.json',record);trials.append(record)
            print(f'{scenario} seed={seed}: {len(annotations)} frames',flush=True)
    pooled=[];distribution=[];paired=[]
    metrics=['active_fresh_rate','active_correct_within10_rate','active_wrong_rate_all','absent_false_output_rate']
    for scenario in plan['scenarios']:
        for method in METHODS:
            pooled.append(dict(scenario=scenario,method=method,
                **summarize([r for r in all_rows if r['scenario']==scenario and r['method']==method])))
            group=[r for r in per_seed if r['scenario']==scenario and r['method']==method]
            for metric in metrics:
                values=[r[metric] for r in group if r[metric] is not None]
                distribution.append(dict(scenario=scenario,method=method,metric=metric,defined_seeds=len(values),
                    median=float(np.median(values)) if values else None,
                    minimum=min(values) if values else None,maximum=max(values) if values else None))
        for seed in plan['seeds']:
            group={r['method']:r for r in per_seed if r['scenario']==scenario and r['seed']==seed}
            for metric in metrics:
                for comparator in ['baseline','cone_only']:
                    a,c=group['tracker'][metric],group[comparator][metric]
                    paired.append(dict(scenario=scenario,seed=seed,metric=metric,comparison='tracker-minus-'+comparator,
                                       delta=a-c if a is not None and c is not None else None))
    for name,rows in [('frames',all_rows),('per-seed',per_seed),('pooled',pooled),('seed-distribution',distribution),('paired-differences',paired),('latencies',latency_rows)]:
        write_csv(out/(name+'.csv'),rows)
    entry.write_json(out/'pooled.json',pooled)
    directory=Path(__file__).resolve().parent
    outputs={p.relative_to(out).as_posix():entry.sha256(p) for p in sorted(out.rglob('*')) if p.is_file()}
    entry.write_json(out/'run.json',dict(status='COMPLETE_SYNTHETIC_BATCH',trials=len(trials),
        acoustic_frames=sum(t['frame_count'] for t in trials),method_rows=len(all_rows),
        plan_file_sha256=entry.sha256(plan_path) if plan_path else None,
        config_file_sha256=entry.sha256(config_path) if config_path else None,
        source_sha256={name:entry.sha256(directory/name) for name in
            ['batch_presence.py','six_mic_track.py','sector_tracker.py','six_mic_localize.py','six_mic_baseline_core.py','audio_frames.py','h1_reader.py']},
        artifact_sha256=outputs,python=platform.python_version(),numpy=np.__version__,
        annotation_semantics='All-zero target envelope -> absent; entire frame one envelope at unity -> active; otherwise transition. Truth never enters algorithms.',
        signal_semantics='Continuous band-limited probes; post-render 20ms amplitude ramps; 1.5m spherical model; padded crop. Noise/competitor persist during target absence.',
        inference_unit='Random seed/trial, not overlapping frame. Seed min/median/max are descriptive, not confidence intervals.',
        waveform_storage='Regenerate exactly from frozen plan, seeds and source; per-trial input hashes recorded. No full waveform copies.',
        limitations=['Synthetic only; no natural speech, measured RIR, physical departure or hardware acceptance.',
                     'Presence means target component emitting at array, not physical person in room.',
                     'Absent fresh output is a false desired-target output even if it localizes a real competitor.',
                     'HOLD display is separate from fresh false output; transitions excluded from steady metrics.',
                     'No parameter tuning or human H3 approval.']))
    return pooled


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,required=True);parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    try:
        pooled=run(load_plan(args.plan),load_config(args.config),args.out,args.plan,args.config)
    except (ValueError,TypeError,OSError,OverflowError,EOFError) as error:
        print(json.dumps(dict(status='ERROR',message=str(error))),file=sys.stderr);return 2
    print(f'COMPLETE_SYNTHETIC_BATCH: {len(pooled)} scenario/method summaries');return 0


if __name__=='__main__':sys.exit(main())
