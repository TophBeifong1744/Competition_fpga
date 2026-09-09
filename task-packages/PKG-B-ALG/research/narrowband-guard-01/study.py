"""Development then locked holdout evaluation of two prespecified guards."""
import argparse,csv,json,sys
from collections import defaultdict
from pathlib import Path
import numpy as np
import guard
HERE=Path(__file__).resolve().parent;ROOT=guard.ROOT
import robustness_sweep as s
from audio_frames import adapt_six_mic_baseline,iter_frames
from quorum_tracker import QuorumSession
from six_mic_track import load_config

def verify():
    for n,h in s.read(HERE/'fixed-files.json').items():assert s.entry.sha256(ROOT/n)==h,n

def generate(plan,noise,direction,room,seed):
    count=plan['duration_samples'];rng=np.random.default_rng(np.random.SeedSequence([seed,1]))
    if noise=='narrow_target':
        f=np.fft.rfftfreq(count,1/48000);x=np.fft.irfft(np.fft.rfft(rng.normal(size=count))*((f>=800)&(f<=1400)),n=count);x/=np.std(x)
    else:x=s.batch.probe(rng,count)
    env=sum(s.batch.envelope(np.arange(count),e['start'],e['stop'],plan['edge_samples']) for e in plan['episodes'])
    rir,meta=s.make_rir(plan,direction,room,seed);target=s.convolve(x*env,rir,count)
    if noise.startswith('tone'):
        frequency=float(noise[4:]);channels=[]
        for m in range(6):
            nrng=np.random.default_rng(np.random.SeedSequence([seed,200+m]));t=np.arange(count)/48000
            z=np.sin(2*np.pi*frequency*t+nrng.uniform(-np.pi,np.pi))+.05*nrng.normal(size=count)
            channels.append(z/np.sqrt(np.mean(z*z)))
        background=np.array(channels)
    else:background=s.noise(plan,'band' if noise=='narrow_target' else noise,seed,count)*(.1 if noise=='narrow_target' else 1)
    segment=adapt_six_mic_baseline(target+background,sample_rate_hz=48000,positions_m=s.batch.b.POS,source_id=f'{noise}:{direction["name"]}:{room["name"]}:{seed}',source_sha256=s.entry.sha256(__file__))
    return segment,meta|dict(input_sha256=segment.provenance['samples_sha256'],target_sha256=s.array_hash(target),noise_sha256=s.array_hash(background))

def summary(rows):
    result=s.batch.summarize(rows);active=[r for r in rows if r['scope']=='target_active']
    return result|dict(raw_active_valid=sum(r['candidate_valid'] for r in active),raw_active_correct=sum(r['raw_error'] is not None and r['raw_error']<=10 for r in active),
        active_guard_trigger=sum(r['guard_trigger'] for r in active),absent_guard_trigger=sum(r['guard_trigger'] for r in rows if r['scope']=='target_absent'),
        active_raw_outside=sum(r['raw_cone_angle'] is not None and r['raw_cone_angle']>30+1e-10 for r in active))

def gates(pooled,method,protocol):
    ix={(r['condition'],r['method']):r for r in pooled};fail=[];band_old=[];band_new=[];tonal=[]
    for condition in sorted({r['condition'] for r in pooled}):
        a,b,c=[ix[condition,m] for m in ['phat','beta075',method]];allowed=c['allowed'];lim=protocol['gates']
        if allowed:
            if condition.startswith('tone'):
                tonal.append(c['active_correct_within10_rate'])
                if c['active_correct_within10_rate']<a['active_correct_within10_rate']-lim['tonal_correct_drop_vs_phat_max']:fail.append(condition+':tonal_vs_phat')
            elif condition.startswith('band__'):
                band_old.append(b['active_correct_within10_rate']-a['active_correct_within10_rate']);band_new.append(c['active_correct_within10_rate']-a['active_correct_within10_rate'])
            elif c['active_correct_within10_rate']<b['active_correct_within10_rate']-lim['control_drop_vs_beta075_max']:fail.append(condition+':control_drop')
        elif c['active_fresh_rate']>min(a['active_fresh_rate'],b['active_fresh_rate'])+lim['outside_output_increase_max']:fail.append(condition+':outside_output')
        if c['absent_false_output_rate']>min(a['absent_false_output_rate'],b['absent_false_output_rate'])+lim['absent_false_increase_max']:fail.append(condition+':absent_output')
    required=max(0.,float(np.mean(band_old)))*protocol['gates']['band_gain_retention'];gain=float(np.mean(band_new))
    if gain<required:fail.append('band_gain_retention')
    return dict(passed=not fail,failures=fail,tonal_mean_correct=float(np.mean(tonal)),band_mean_gain=gain,band_required_gain=required)

def run(phase):
    verify();protocol=s.read(HERE/'protocol.json');plan=s.read(ROOT/'payload/config/robustness-sweep.json')
    assert not set(protocol['development_seeds'])&set(protocol['validation_seeds'])
    prior=set(plan['seeds'])
    for name in ['capture-research-protocol.json','candidate-quality-protocol.json']:
        old=s.read(ROOT/'payload/config'/name);prior.update(old['development_seeds']+old['validation_seeds'])
    assert not prior&set(protocol['development_seeds']+protocol['validation_seeds'])
    source={n:s.entry.sha256(HERE/n) for n in ['guard.py','study.py']}
    if phase=='validation':
        selection=s.read(HERE/'development/selection.json')
        assert selection['source_sha256']==source and selection['protocol_sha256']==s.entry.sha256(HERE/'protocol.json')
        candidates=[selection['selected']]
    else:candidates=protocol['candidates']
    methods=['phat','beta075']+candidates;out=HERE/phase
    if out.exists():raise ValueError('output exists')
    out.mkdir();s.entry.write_json(out/'plan.json',dict(protocol=protocol,acoustic_plan=plan,phase=phase))
    rows=[];per=[];inputs=[];lat=[];config=load_config(ROOT/'payload/config/sector-tracking.json')
    for noise in protocol[phase+'_noises']:
        for direction in protocol['directions']:
            allowed=s.batch.b.angle(np.array([1.,0,0]),s.batch.b.unit(direction['az'],direction['el']))<=30
            for room in plan['rooms']:
                if room['name'] not in protocol[phase+'_rooms']:continue
                condition=noise+'__'+direction['name']+'__'+room['name']
                for seed in protocol[phase+'_seeds']:
                    segment,meta=generate(plan,noise,direction,room,seed);trial=[]
                    sessions={m:QuorumSession(config) for m in methods}
                    inputs.append(dict(condition=condition,noise=noise,direction=direction,room=room,seed=seed,allowed=bool(allowed),**meta))
                    for frame in iter_frames(segment):
                        cs={'phat':s.entry.localize_frame(frame),'beta075':s.weighted_gcc.localize(frame,.75)}
                        cs.update({m:guard.localize(frame,m) for m in candidates})
                        tracked={m:sessions[m].update(c) for m,c in cs.items()}
                        label=s.labels(plan,frame.row_start,frame.row_stop,meta,direction)
                        for method,c in cs.items():
                            u=np.array(c['unit_vector']) if c['valid'] else None
                            r=s.candidate_study.metrics_row(c,label,method,tracked[method])
                            trial.append(dict(condition=condition,seed=seed,allowed=bool(allowed),**r,
                                guard_score=c.get('guard_score'),guard_trigger=c.get('guard_trigger',False),
                                raw_error=s.batch.b.angle(u,np.array(label['target_unit_vector'])) if c['valid'] and label['scope']=='target_active' else None,
                                raw_cone_angle=s.batch.b.angle(u,np.array([1.,0,0])) if c['valid'] else None))
                    rows.extend(trial)
                    for m in methods:
                        group=[r for r in trial if r['method']==m]
                        per.append(dict(condition=condition,seed=seed,method=m,allowed=bool(allowed),**summary(group)))
                        for i,e in enumerate(plan['episodes']):
                            good=[r for r in group if r['scope']=='target_active' and r['episode']==i and r['fresh_valid'] and r['error_deg']<=10]
                            lat.append(dict(condition=condition,seed=seed,method=m,episode=i,allowed=bool(allowed),found=bool(good),latency_ms=good[0]['timestamp_ms']-e['start']/48 if good else None))
                    print(phase,condition,seed,flush=True)
    groups=defaultdict(list)
    for r in rows:groups[r['condition'],r['method']].append(r)
    pooled=[dict(condition=c,method=m,allowed=g[0]['allowed'],**summary(g)) for (c,m),g in sorted(groups.items())]
    for n,data in [('frames',rows),('per-seed',per),('latencies',lat)]:s.batch.write_csv(out/(n+'.csv'),data)
    for n,data in [('pooled',pooled),('inputs',inputs)]:s.entry.write_json(out/(n+'.json'),data)
    decisions={m:gates(pooled,m,protocol) for m in candidates};s.entry.write_json(out/'gates.json',decisions)
    if phase=='development':
        eligible=[m for m in candidates if decisions[m]['passed']];choices=eligible or candidates
        chosen=max(choices,key=lambda m:decisions[m]['tonal_mean_correct'])
        s.entry.write_json(out/'selection.json',dict(selected=chosen,development_passed=bool(eligible),source_sha256=source,protocol_sha256=s.entry.sha256(HERE/'protocol.json'),decisions=decisions,policy=protocol['selection']))
    verify();s.entry.write_json(out/'run.json',dict(status='COMPLETE',phase=phase,trials=len(inputs),method_rows=len(rows),source_sha256=source,protocol_sha256=s.entry.sha256(HERE/'protocol.json'),
        selection_sha256=s.entry.sha256(HERE/'development/selection.json') if phase=='validation' else None,
        artifacts={p.name:s.entry.sha256(p) for p in out.iterdir() if p.is_file()}))
    print(json.dumps(decisions))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['development','validation']);run(p.parse_args().phase)
