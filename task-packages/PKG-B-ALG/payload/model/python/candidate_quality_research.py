"""Independent candidate-quality experiment; fixed 5/12 capture, fresh seed split."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import numpy as np
import batch_presence as batch
import six_mic_localize as entry
from audio_frames import iter_frames
from six_mic_track import load_config
from quorum_tracker import QuorumSession,CaptureConfig
from sector_tracker import angle
import weighted_gcc

ROOT=Path(__file__).resolve().parents[3]
PROTOCOL=ROOT/'payload/config/candidate-quality-protocol.json'


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))


def verify_references():
    for manifest in ['reference/batch-presence-fixed/frozen-files.json','reference/candidate-quality-fixed/files.json']:
        for name,h in read(ROOT/manifest)['files'].items():
            if entry.sha256(ROOT/name)!=h:raise ValueError('reference changed: '+name)


def sources():
    directory=Path(__file__).resolve().parent
    return {name:entry.sha256(directory/name) for name in ['candidate_quality_research.py','weighted_gcc.py','batch_presence.py',
        'quorum_tracker.py','sector_tracker.py','six_mic_track.py','six_mic_localize.py','six_mic_baseline_core.py','audio_frames.py','h1_reader.py']}


def metrics_row(base,label,method,output=None):
    fresh=base['valid'] if output is None else output['fresh_valid']
    u=base['unit_vector'] if output is None else output['direction']
    return dict(frame_index=base['index'],row_start=base['row_start'],row_stop=base['row_stop'],
        timestamp_ms=base['end_seconds_exclusive']*1000,method=method,scope=label['scope'],episode=label['episode'],
        fresh_valid=fresh,state='FRAME' if output is None else output['state'],
        reason=('accepted' if fresh else '|'.join(base['rejection_reasons'])) if output is None else output['reason'],
        stale=False if output is None else output['stale'],
        error_deg=angle(np.array(label['target_unit_vector']),np.asarray(u)) if fresh and label['scope']=='target_active' else None,
        estimate_x=u[0] if fresh else None,estimate_y=u[1] if fresh else None,estimate_z=u[2] if fresh else None,
        candidate_valid=base['valid'],residual_samples=base['residual_samples'],raw_vector_norm=base['raw_vector_norm'],
        finite_pairs=base['finite_pairs'],display_expires_at_ms=output['display_expires_at_ms'] if output else None)


def evaluate(segment,env,directions,config,candidates):
    variants=[dict(name='original',beta=1)]+candidates
    sessions={v['name']:QuorumSession(config,CaptureConfig(5,12,120)) for v in variants}
    rows=[];diagnostics=[]
    for frame in iter_frames(segment):
        old=entry.localize_frame(frame)
        # All algorithms operate without presence, truth, target sector, or source labels.
        estimates={'original':old}|{v['name']:weighted_gcc.localize(frame,v['beta']) for v in candidates}
        outputs={name:sessions[name].update(estimate) for name,estimate in estimates.items()}
        label=batch.label_frame(env,frame.row_start,frame.row_stop,directions)
        for name,estimate in estimates.items():
            rows.append(metrics_row(estimate,label,name+'_raw'))
            rows.append(metrics_row(estimate,label,name+'_quorum',outputs[name]))
            diagnostic=dict(frame_index=frame.index,method=name,scope=label['scope'],valid=estimate['valid'],
                rejection_reasons='|'.join(estimate['rejection_reasons']),finite_pairs=estimate['finite_pairs'],
                residual_samples=estimate['residual_samples'],raw_vector_norm=estimate['raw_vector_norm'],
                old_valid=old['valid'],pair_error_rms_samples=None,pair_error_max_samples=None)
            if label['scope']=='target_active':
                u=np.array(label['target_unit_vector']);d=np.linalg.norm(1.5*u-batch.b.POS,axis=1)
                expected=np.array([(d[i]-d[j])/batch.b.C*batch.b.FS for i,j in batch.b.PAIRS])
                tau=np.array([np.nan if t is None else t for t in estimate['pair_delays_samples']])
                good=np.isfinite(tau)
                if good.any():
                    errors=tau[good]-expected[good]
                    diagnostic.update(pair_error_rms_samples=float(np.sqrt(np.mean(errors**2))),pair_error_max_samples=float(np.max(np.abs(errors))))
            diagnostics.append(diagnostic)
    return rows,diagnostics


def gates(pooled,name,protocol):
    ix={(r['scenario'],r['method']):r for r in pooled};limits=protocol['gates']
    n=ix['band_noise0',name+'_raw'];o=ix['band_noise0','original_raw']
    nt=ix['band_noise0',name+'_quorum'];ot=ix['band_noise0','original_quorum']
    checks=dict(raw_noise_correct_gain=n['active_correct_within10_rate']-o['active_correct_within10_rate']>=limits['noise_raw_correct_gain_min'],
        tracked_noise_correct_gain=nt['active_correct_within10_rate']-ot['active_correct_within10_rate']>=limits['noise_tracked_correct_gain_min'],
        noise_p95=all(r['p95_error_deg'] is not None and r['p95_error_deg']<=limits['p95_max_deg'] for r in [n,nt]),
        absent_false_outputs=all(ix[s,name+'_quorum']['absent_false_output_rate']-ix[s,'original_quorum']['absent_false_output_rate']<=limits['absent_false_increase_max']+1e-12 for s in batch.SCENARIOS),
        normal_correct=all(ix['drop_return',name+suffix]['active_correct_within10_rate']>=ix['drop_return','original'+suffix]['active_correct_within10_rate']-limits['normal_correct_drop_max'] for suffix in ['_raw','_quorum']),
        noise_wrong=all(ix['band_noise0',name+suffix]['active_wrong_rate_all']-ix['band_noise0','original'+suffix]['active_wrong_rate_all']<=limits['noise_wrong_increase_max']+1e-12 for suffix in ['_raw','_quorum']))
    return dict(passed=all(checks.values()),checks=checks)


def execute(phase,out,selection_path=None):
    verify_references();protocol=read(PROTOCOL)
    prior=set(read(ROOT/'payload/config/capture-research-protocol.json')['development_seeds'])|set(read(ROOT/'payload/config/capture-research-protocol.json')['validation_seeds'])
    dev,test=set(protocol['development_seeds']),set(protocol['validation_seeds'])
    if dev&test or (dev|test)&prior:raise ValueError('new split overlaps earlier study')
    if phase=='develop':candidates=protocol['candidates']
    else:
        if selection_path is None:raise ValueError('frozen selection required')
        selected=read(selection_path)
        if selected['source_sha256']!=sources() or selected['protocol_sha256']!=entry.sha256(PROTOCOL):raise ValueError('selected code changed')
        candidates=[selected['validation_candidate']]
    plan=batch.load_plan(ROOT/'payload/config/batch-presence.json')|dict(seeds=protocol['development_seeds'] if phase=='develop' else protocol['validation_seeds'])
    config=load_config(ROOT/'payload/config/sector-tracking.json');out=Path(out)
    if out.exists():raise ValueError('output must be new')
    out.mkdir(parents=True);entry.write_json(out/'plan.json',plan);entry.write_json(out/'protocol.json',protocol)
    all_rows=[];all_diag=[];per_seed=[];latencies=[];inputs=[]
    methods=[v['name']+suffix for v in [dict(name='original')]+candidates for suffix in ['_raw','_quorum']]
    for scenario in plan['scenarios']:
        for seed in plan['seeds']:
            segment,env,directions=batch.generate(plan,scenario,seed)
            rows,diag=evaluate(segment,env,directions,config,candidates)
            all_rows.extend(dict(scenario=scenario,seed=seed,**r) for r in rows)
            all_diag.extend(dict(scenario=scenario,seed=seed,**r) for r in diag)
            inputs.append(dict(scenario=scenario,seed=seed,input_sha256=segment.provenance['samples_sha256']))
            for method in methods:
                group=[r for r in rows if r['method']==method]
                per_seed.append(dict(scenario=scenario,seed=seed,method=method,**batch.summarize(group)))
                temp=[r|dict(method='baseline') for r in group]
                latencies.extend(dict(scenario=scenario,seed=seed,**(r|dict(method=method))) for r in batch.latencies(temp,plan) if r['method']=='baseline')
            print(f'{phase}: {scenario} seed={seed}',flush=True)
    pooled=[dict(scenario=s,method=m,**batch.summarize([r for r in all_rows if r['scenario']==s and r['method']==m])) for s in plan['scenarios'] for m in methods]
    paired=[]
    for c in candidates:
        for s in plan['scenarios']:
            for seed in plan['seeds']:
                ix={r['method']:r for r in per_seed if r['scenario']==s and r['seed']==seed}
                for suffix in ['_raw','_quorum']:
                    for metric in ['active_fresh_rate','active_correct_within10_rate','active_wrong_rate_all','absent_false_output_rate']:
                        a,b=ix[c['name']+suffix][metric],ix['original'+suffix][metric]
                        paired.append(dict(scenario=s,seed=seed,method=c['name']+suffix,metric=metric,delta=a-b if a is not None and b is not None else None))
    for name,rows in [('frames',all_rows),('candidate-diagnostics',all_diag),('per-seed',per_seed),('pooled',pooled),('paired',paired),('latencies',latencies)]:batch.write_csv(out/(name+'.csv'),rows)
    entry.write_json(out/'pooled.json',pooled);entry.write_json(out/'inputs.json',inputs)
    results={c['name']:gates(pooled,c['name'],protocol) for c in candidates};entry.write_json(out/'gates.json',results)
    if phase=='develop':
        chosen=next((c for c in candidates if results[c['name']]['passed']),None)
        entry.write_json(out/'selection.json',dict(selected=chosen,validation_candidate=chosen or candidates[0],
            negative_hypothesis_only=chosen is None,source_sha256=sources(),protocol_sha256=entry.sha256(PROTOCOL)))
    verify_references()
    entry.write_json(out/'run.json',dict(status='COMPLETE_CANDIDATE_RESEARCH',phase=phase,seeds=plan['seeds'],
        source_sha256=sources(),protocol_sha256=entry.sha256(PROTOCOL),selection_sha256=entry.sha256(selection_path) if selection_path else None,
        method_rows=len(all_rows),diagnostic_rows=len(all_diag),python=platform.python_version(),numpy=np.__version__,
        artifact_sha256={p.name:entry.sha256(p) for p in sorted(out.iterdir()) if p.is_file()},
        scope='Exponent-only GCC candidate research, unchanged LS/quality gates and 5/12 capture. Synthetic only; no automatic replacement.'))
    print(json.dumps(results));return results


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=['develop','validate'],required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--selection',type=Path);a=p.parse_args()
    try:execute(a.phase,a.out,a.selection)
    except (ValueError,OSError,TypeError) as error:print(json.dumps(dict(status='ERROR',message=str(error))));raise SystemExit(2)
