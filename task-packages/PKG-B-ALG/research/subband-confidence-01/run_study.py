import csv,json,sys,gzip
from pathlib import Path
from collections import defaultdict
import numpy as np
import features as f
HERE=Path(__file__).resolve().parent;ROOT=f.ROOT
sys.path.insert(0,str(ROOT/'research/narrowband-guard-01'))
import study as source
import guard
import robustness_sweep as s
from audio_frames import iter_frames
from quorum_tracker import QuorumSession
from six_mic_track import load_config

def verify():
    for n,h in s.read(HERE/'fixed-files.json').items():assert s.entry.sha256(ROOT/n)==h,n

def summarize(g):
    a=s.batch.summarize(g);active=[r for r in g if r['scope']=='target_active']
    return a|{k:sum(r['category']==k for r in active) for k in ['full_rejected','unsupported','inconsistent','boundary_uncertain','inside_supported']}

def run():
    verify();p=s.read(HERE/'protocol.json');plan=s.read(ROOT/'payload/config/robustness-sweep.json')
    used=set(plan['seeds'])
    for name in ['capture-research-protocol.json','candidate-quality-protocol.json']:
        old=s.read(ROOT/'payload/config'/name);used.update(old['development_seeds']+old['validation_seeds'])
    old=s.read(ROOT/'research/narrowband-guard-01/protocol.json');used.update(old['development_seeds']+old['validation_seeds'])
    assert not used&set(p['seeds'])
    out=HERE/'evidence'
    if out.exists():raise ValueError('output exists')
    out.mkdir();s.entry.write_json(out/'plan.json',dict(protocol=p,acoustic=plan));rows=[];per=[];inputs=[];lat=[]
    with gzip.open(out/'features.jsonl.gz','wt',encoding='utf-8') as detail:
        for noise in p['noises']:
            for direction in p['directions']:
                allowed=s.batch.b.angle(np.array([1.,0,0]),s.batch.b.unit(direction['az'],direction['el']))<=30+1e-10
                for room in plan['rooms']:
                    if room['name'] not in p['rooms']:continue
                    condition=noise+'__'+direction['name']+'__'+room['name']
                    for seed in p['seeds']:
                        segment,meta=source.generate(plan,noise,direction,room,seed)
                        inputs.append(dict(condition=condition,seed=seed,noise=noise,direction=direction,room=room,allowed=bool(allowed),**meta))
                        sessions={m:QuorumSession(load_config(ROOT/'payload/config/sector-tracking.json')) for m in p['methods']};trial=[]
                        for frame in iter_frames(segment):
                            full=guard.localize(frame,'cap150');subs=f.subband_candidates(frame,p['subbands_hz']);d=f.assess(full,subs,p['consistency'])
                            candidates=dict(zip(p['methods'],[full,f.screened(full,d),f.screened(full,d,True)]))
                            tracked={m:sessions[m].update(c) for m,c in candidates.items()}
                            label=s.labels(plan,frame.row_start,frame.row_stop,meta,direction)
                            detail.write(json.dumps(dict(condition=condition,seed=seed,frame=frame.index,scope=label['scope'],full={k:full[k] for k in ['valid','unit_vector','pair_delays_samples']},subbands=subs,diagnostic=d),allow_nan=False)+'\n')
                            for m,c in candidates.items():
                                r=s.candidate_study.metrics_row(c,label,m,tracked[m])
                                trial.append(dict(condition=condition,seed=seed,allowed=bool(allowed),**r,**d,original_valid=full['valid']))
                        rows.extend(trial)
                        for m in p['methods']:
                            g=[r for r in trial if r['method']==m];per.append(dict(condition=condition,seed=seed,allowed=bool(allowed),method=m,**summarize(g)))
                            for i,e in enumerate(plan['episodes']):
                                good=[r for r in g if r['scope']=='target_active' and r['episode']==i and r['fresh_valid'] and r['error_deg']<=10]
                                lat.append(dict(condition=condition,seed=seed,method=m,episode=i,allowed=bool(allowed),found=bool(good),latency_ms=good[0]['timestamp_ms']-e['start']/48 if good else None))
                        print(condition,seed,flush=True)
    groups=defaultdict(list)
    for r in rows:groups[r['condition'],r['method']].append(r)
    pooled=[dict(condition=c,method=m,allowed=g[0]['allowed'],**summarize(g)) for (c,m),g in sorted(groups.items())]
    for n,r in [('frames',rows),('per-seed',per),('latencies',lat)]:s.batch.write_csv(out/(n+'.csv'),r)
    for n,r in [('pooled',pooled),('inputs',inputs)]:s.entry.write_json(out/(n+'.json'),r)
    verify();s.entry.write_json(out/'run.json',dict(status='COMPLETE_FIXED_DIAGNOSTIC',trials=len(inputs),method_rows=len(rows),acoustic_frames=len(rows)//3,
        source_sha256={n:s.entry.sha256(HERE/n) for n in ['features.py','run_study.py']},protocol_sha256=s.entry.sha256(HERE/'protocol.json'),
        artifacts={p.name:s.entry.sha256(p) for p in out.iterdir() if p.is_file()}))

if __name__=='__main__':run()
