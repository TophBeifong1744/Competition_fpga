"""Retrospective causal diagnostics; no tuning or tracker changes."""
import csv, gzip, hashlib, importlib.util, json, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PRIOR=ROOT/'research/effective-perturbation-01'
spec=importlib.util.spec_from_file_location('effective_frozen',PRIOR/'features.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
sys.path.insert(0,str(ROOT/'research/narrowband-guard-01'))
import study as source
from audio_frames import adapt_six_mic_baseline, iter_frames
from six_mic_localize import solve_delays
s=source.s

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def angle(u,v=(1.,0.,0.)):return float(f.b.angle(np.array(u),np.array(v)))
def stats(x):
    a=np.array(x,dtype=float);a=a[np.isfinite(a)]
    return dict(n=len(a),min=float(a.min()),median=float(np.median(a)),p95=float(np.percentile(a,95)),max=float(a.max())) if len(a) else dict(n=0)
def inside(u):return angle(u)<=30+1e-10
def tau(x):return np.array([np.nan if t is None else t for t in x],dtype=float)
def verify():
    snap=read(HERE/'fixed-files.json')
    assert all(sha(ROOT/n)==h for n,h in snap.items())
    return len(snap)
def components(plan,m,room):
    count=plan['duration_samples'];seed=m['seed'];noise=m['noise']
    rng=np.random.default_rng(np.random.SeedSequence([seed,1]))
    if noise=='narrow_target':
        freq=np.fft.rfftfreq(count,1/48000)
        x=np.fft.irfft(np.fft.rfft(rng.normal(size=count))*((freq>=800)&(freq<=1400)),n=count);x/=np.std(x)
    else:x=s.batch.probe(rng,count)
    env=sum(s.batch.envelope(np.arange(count),e['start'],e['stop'],plan['edge_samples']) for e in plan['episodes'])
    rir,meta=s.make_rir(plan,m['direction'],room,seed);target=s.convolve(x*env,rir,count)
    if noise.startswith('tone'):
        channels=[]
        for mic in range(6):
            rng=np.random.default_rng(np.random.SeedSequence([seed,200+mic]));t=np.arange(count)/48000
            z=np.sin(2*np.pi*float(noise[4:])*t+rng.uniform(-np.pi,np.pi))+.05*rng.normal(size=count)
            channels.append(z/np.sqrt(np.mean(z*z)))
        background=np.array(channels)
    else:background=s.noise(plan,'band' if noise=='narrow_target' else noise,seed,count)*(.1 if noise=='narrow_target' else 1)
    return target,background,meta

def run():
    verify();p=read(PRIOR/'protocol.json');plan=read(PRIOR/'evidence/plan.json')['acoustic']
    inputs={(m['condition'],m['seed']):m for m in read(PRIOR/'evidence/inputs.json')}
    selected=[];groups=defaultdict(list);population=Counter();similarities=[]
    with gzip.open(PRIOR/'evidence/features.jsonl.gz','rt',encoding='utf-8') as stream:
        for line in stream:
            r=json.loads(line);m=inputs[r['condition'],r['seed']]
            if r['scope']!='target_active' or m['allowed']:continue
            population['outside_active']+=1
            full=r['full'];d=r['diagnostic']
            if not full['valid'] or not inside(full['unit_vector']) or d['category']!='stable':continue
            truth=f.b.unit(m['direction']['az'],m['direction']['el'])
            direct=np.array([v['direct_delay_samples'] for v in m['paths']]);reference=np.array([direct[i]-direct[j] for i,j in f.b.PAIRS])
            error=tau(full['pair_delays_samples'])-reference
            deleted=[r['deleted'][k] for k in d['comparable_indices']]
            cones=[angle(v['unit_vector']) for v in deleted]
            cos=[]
            for v in deleted:
                other=tau(v['pair_delays_samples'])-reference;common=np.isfinite(error)&np.isfinite(other)
                a,b=error[common],other[common];den=np.linalg.norm(a)*np.linalg.norm(b)
                if den>1e-12:cos.append(float(a@b/den))
            similarities.extend(cos)
            solved=solve_delays(tau(full['pair_delays_samples']))
            item=dict(condition=r['condition'],seed=r['seed'],frame=r['frame'],noise=m['noise'],room=m['room']['name'],direction=m['direction']['name'],
                cone_deg=angle(full['unit_vector']),truth_error_deg=angle(full['unit_vector'],truth),crossings=d['cone_crossings'],
                max_angle_change=d['max_angle_change'],deleted_cones=cones,all_deleted_under_truth=all(c<32 for c in cones),
                residual_samples=solved['residual_samples'],direct_pair_rmse=float(np.sqrt(np.nanmean(error**2))),error_cosines=cos)
            selected.append(item);groups[r['condition'],r['seed']].append(item)
    assert len(selected)==563
    assert sum(x['crossings']==0 for x in selected)==246
    tracked={}
    with (PRIOR/'evidence/frames.csv').open(encoding='utf-8',newline='') as stream:
        for r in csv.DictReader(stream):
            if r['method']=='effective_known_only':tracked[r['condition'],int(r['seed']),int(r['frame_index'])]=r['fresh_valid']=='True'
    for x in selected:x['same_frame_fresh_output']=tracked[x['condition'],x['seed'],x['frame']]
    controls=[];checks=[]
    dry=next(r for r in plan['rooms'] if r['name']=='dry')
    for key,cohort in sorted(groups.items()):
        m=inputs[key];original,meta=source.generate(plan,m['noise'],m['direction'],m['room'],m['seed'])
        assert meta['input_sha256']==m['input_sha256']
        target,background,roommeta=components(plan,m,m['room'])
        assert s.array_hash(target)==m['target_sha256'] and s.array_hash(background)==m['noise_sha256']
        clean,drynoise,drymeta=components(plan,m,dry)
        assert np.array_equal(background,drynoise)
        original_check=adapt_six_mic_baseline(target+background,sample_rate_hz=48000,positions_m=f.b.POS,source_id='check',source_sha256=sha(Path(__file__)))
        assert original_check.provenance['samples_sha256']==m['input_sha256']
        indexes={v['frame'] for v in cohort}
        for name,data,cmeta in [('original',target+background,roommeta),('no_noise',target,roommeta),('dry',clean+background,drymeta),('dry_no_noise',clean,drymeta)]:
            segment=adapt_six_mic_baseline(data,sample_rate_hz=48000,positions_m=f.b.POS,source_id=name,source_sha256=sha(Path(__file__)))
            for frame in iter_frames(segment):
                if frame.index not in indexes:continue
                label=s.labels(plan,frame.row_start,frame.row_stop,cmeta,m['direction'])
                assert label['scope']=='target_active'
                est=f.old.estimates(frame,p['omitted_bands_hz']);d=f.assess(est[0],est[1:],f.impacts(frame,p['omitted_bands_hz']),p['impact'],p['loo'])
                u=est[0]['unit_vector'];valid=est[0]['valid']
                controls.append(dict(condition=key[0],seed=key[1],frame=frame.index,control=name,room=m['room']['name'],noise=m['noise'],valid=valid,
                    cone_deg=angle(u) if valid else None,error_deg=angle(u,f.b.unit(m['direction']['az'],m['direction']['el'])) if valid else None,
                    wrong_incone=bool(valid and inside(u)),category=d['category']))
                if name=='original':assert valid and inside(u) and d['category']=='stable'
        checks.append(dict(condition=key[0],seed=key[1],original_input_hash=m['input_sha256'],target_and_noise_hash_match=True,selected_frames=len(indexes)))
        print(key,len(indexes),flush=True)
    summary=dict(population=dict(population),selected=len(selected),affected_trials=len(groups),crossing=sum(x['crossings']>0 for x in selected),
        all_deleted_under_truth=sum(x['all_deleted_under_truth'] for x in selected),same_frame_fresh_output=sum(x['same_frame_fresh_output'] for x in selected),
        distributions={k:stats([x[k] for x in selected]) for k in ['cone_deg','truth_error_deg','max_angle_change','residual_samples','direct_pair_rmse']},
        error_cosine=stats(similarities),by_condition=dict(Counter(x['condition'] for x in selected)),controls={})
    for name in ['original','no_noise','dry','dry_no_noise']:
        summary['controls'][name]={}
        for room in ['all','dry','early_late']:
            rows=[x for x in controls if x['control']==name and (room=='all' or x['room']==room)]
            summary['controls'][name][room]=dict(n=len(rows),valid=sum(x['valid'] for x in rows),wrong_incone=sum(x['wrong_incone'] for x in rows),
                wrong_stable=sum(x['wrong_incone'] and x['category']=='stable' for x in rows),error_deg=stats([x['error_deg'] for x in rows if x['valid']]))
    write(HERE/'cohort.json',selected);write(HERE/'controls.json',controls);write(HERE/'summary.json',summary)
    write(HERE/'verification.json',dict(prior_files_unchanged=verify(),regenerated_trials=checks,controls_rows=len(controls),selected_count_and_crossing_assertions=True,all_control_frames_target_active=True))
    print(json.dumps(summary,ensure_ascii=False),flush=True)

if __name__=='__main__':run()
