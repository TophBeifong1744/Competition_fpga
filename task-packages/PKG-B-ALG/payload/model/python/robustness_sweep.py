"""Frozen GCC/capture transfer check with new noise, directions and causal synthetic RIRs."""
import argparse
from collections import defaultdict
import hashlib
import itertools
import json
from pathlib import Path
import platform
import numpy as np
import batch_presence as batch
import candidate_quality_research as candidate_study
import six_mic_localize as entry
from audio_frames import adapt_six_mic_baseline,iter_frames
from quorum_tracker import QuorumSession,CaptureConfig
from six_mic_track import load_config
import weighted_gcc

ROOT=Path(__file__).resolve().parents[3]
PLAN=ROOT/'payload/config/robustness-sweep.json'
METHODS=['original_raw','original_quorum','gcc_beta075_raw','gcc_beta075_quorum']


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def array_hash(x):return hashlib.sha256(np.asarray(x,dtype='<f8').tobytes(order='C')).hexdigest()


def fractional_tap(rir,delay,amplitude):
    i=int(np.floor(delay));f=delay-i
    if i<0 or i+1>=len(rir):raise ValueError('tap outside causal response')
    rir[i]+=amplitude*(1-f);rir[i+1]+=amplitude*f


def make_rir(plan,direction,room,seed):
    b=batch.b;center=np.array(plan['array_center_m']);dims=np.array(plan['room_dimensions_m'])
    source=center+plan['distance_m']*b.unit(direction['az'],direction['el'])
    microphones=center+b.POS
    if not np.all((source>0)&(source<dims)):raise ValueError('source outside synthetic room')
    images=[]
    if room['wall_gain']:
        for axis in range(3):
            low=source.copy();low[axis]=-source[axis]
            high=source.copy();high[axis]=2*dims[axis]-source[axis]
            images.extend([low,high])
    length=int(np.ceil(plan['tail_stop_s']*b.FS))+2
    rir=np.zeros((6,length));paths=[]
    for m,mic in enumerate(microphones):
        direct_distance=np.linalg.norm(source-mic)
        direct_amp=plan['distance_m']/direct_distance
        fractional_tap(rir[m],direct_distance/b.C*b.FS,direct_amp)
        for image in images:
            distance=np.linalg.norm(image-mic)
            fractional_tap(rir[m],distance/b.C*b.FS,room['wall_gain']*plan['distance_m']/distance)
        if room['tail_relative_l2']:
            start=int(plan['tail_start_s']*b.FS);stop=int(plan['tail_stop_s']*b.FS)
            t=np.arange(stop-start)/b.FS
            rng=np.random.default_rng(np.random.SeedSequence([seed,100+m]))
            tail=rng.normal(size=len(t))*np.exp(-np.log(1000)*t/plan['tail_decay_60db_s'])
            tail*=room['tail_relative_l2']*direct_amp/np.linalg.norm(tail)
            rir[m,start:stop]+=tail
        support=np.flatnonzero(rir[m]!=0)
        paths.append(dict(microphone=m,first_tap=int(support[0]),last_tap=int(support[-1]),direct_delay_samples=direct_distance/b.C*b.FS))
    earliest=min(p['first_tap'] for p in paths);latest=max(p['last_tap'] for p in paths)
    rir=rir[:,:latest+1]
    return rir,dict(source_m=source.tolist(),support_first=earliest,support_last=latest,paths=paths,
                    rir_sha256=array_hash(rir),interpolation='two-tap linear fractional delay',
                    tail_note='Independent per-mic stochastic FIR tail. Nominal envelope decay only; not measured RT60.')


def convolve(signal,rir,count):
    size=1<<(len(signal)+rir.shape[1]-2).bit_length()
    return np.fft.irfft(np.fft.rfft(signal,n=size)[None,:]*np.fft.rfft(rir,n=size,axis=1),n=size,axis=1)[:,:count]


def noise(plan,kind,seed,count):
    channels=[]
    for m in range(6):
        rng=np.random.default_rng(np.random.SeedSequence([seed,200+m]))
        if kind=='band':x=batch.probe(rng,count)
        elif kind=='pink':
            f=np.fft.rfftfreq(count,1/48000);weight=1/np.sqrt(np.maximum(f,20));weight[0]=0
            x=np.fft.irfft(np.fft.rfft(rng.normal(size=count))*weight,n=count)
        elif kind=='tonal':
            t=np.arange(count)/48000;x=np.sin(2*np.pi*1000*t+rng.uniform(-np.pi,np.pi))+.05*rng.normal(size=count)
        elif kind=='impulsive':
            x=rng.normal(size=count)*(rng.random(count)<.002)+.005*rng.normal(size=count)
        else:raise ValueError('unknown noise')
        rms=np.sqrt(np.mean(x*x))
        if not rms>0:raise ValueError('empty noise')
        channels.append(x/rms*plan['noise_nominal_rms'])
    return np.array(channels)


def labels(plan,start,stop,support,direction):
    first,last=support['support_first'],support['support_last']
    active=[];overlap=False;emitting=False
    for i,e in enumerate(plan['episodes']):
        if start>=e['start']+plan['edge_samples']+last and stop-1<=e['stop']-plan['edge_samples']+first:active.append(i)
        overlap|=max(start,e['start']+1+first)<min(stop,e['stop']+last)
        emitting|=max(start,e['start']+1)<min(stop,e['stop'])
    scope='target_absent' if not overlap else 'target_active' if len(active)==1 else 'transition'
    return dict(scope=scope,episode=active[0] if scope=='target_active' else None,
                target_unit_vector=batch.b.unit(direction['az'],direction['el']).tolist() if scope=='target_active' else None,
                emission_off=not emitting,tail_possible_after_emission=bool(not emitting and overlap))


def generate(plan,noise_kind,direction,room,seed):
    count=plan['duration_samples'];rng=np.random.default_rng(np.random.SeedSequence([seed,1]))
    probe=batch.probe(rng,count);indices=np.arange(count)
    env=sum(batch.envelope(indices,e['start'],e['stop'],plan['edge_samples']) for e in plan['episodes'])
    rir,metadata=make_rir(plan,direction,room,seed)
    target=convolve(probe*env,rir,count);background=noise(plan,noise_kind,seed,count)
    signal=target+background
    segment=adapt_six_mic_baseline(signal,sample_rate_hz=48000,positions_m=batch.b.POS,
        source_id=f'robustness:{noise_kind}:{direction["name"]}:{room["name"]}:{seed}',source_sha256=entry.sha256(__file__))
    metadata.update(input_sha256=segment.provenance['samples_sha256'],noise_sha256=array_hash(background),
                    noise_rms=np.sqrt(np.mean(background*background,axis=1)).tolist(),target_sha256=array_hash(target))
    return segment,metadata,rir


def evaluate(segment,plan,direction,support,config):
    sessions={name:QuorumSession(config,CaptureConfig(5,12,120)) for name in ['original','gcc_beta075']}
    rows=[];annotations=[]
    for frame in iter_frames(segment):
        candidates=dict(original=entry.localize_frame(frame),gcc_beta075=weighted_gcc.localize(frame,.75))
        tracked={k:sessions[k].update(v) for k,v in candidates.items()}
        label=labels(plan,frame.row_start,frame.row_stop,support,direction)
        annotations.append(dict(frame_index=frame.index,row_start=frame.row_start,row_stop=frame.row_stop,**label))
        for name,base in candidates.items():
            for suffix,output in [('_raw',None),('_quorum',tracked[name])]:
                rows.append(candidate_study.metrics_row(base,label,name+suffix,output)|dict(
                    emission_off=label['emission_off'],tail_possible_after_emission=label['tail_possible_after_emission']))
    return rows,annotations


def summarize(rows):
    result=batch.summarize(rows)
    tail=[r for r in rows if r['tail_possible_after_emission']]
    result.update(tail_after_emission_frames=len(tail),tail_after_emission_fresh=sum(r['fresh_valid'] for r in tail),
                  tail_after_emission_hold=sum(r['stale'] for r in tail))
    return result


def flags(old,new,allowed,limits):
    result=[]
    if allowed:
        if new['active_correct_within10_rate']<old['active_correct_within10_rate']-limits['correct_rate_drop']:result.append('correct_rate_drop')
        if old['p95_error_deg'] is not None and new['p95_error_deg'] is not None and new['p95_error_deg']>old['p95_error_deg']+limits['p95_error_increase_deg']:result.append('p95_increase')
    elif new['active_fresh_rate']>old['active_fresh_rate']+limits['outside_fresh_increase']:result.append('outside_target_output_increase')
    if new['absent_false_output_rate']>old['absent_false_output_rate']+limits['absent_false_increase']:result.append('absent_false_increase')
    return result


def verify_fixed():
    for filename in ['reference/batch-presence-fixed/frozen-files.json','reference/candidate-quality-fixed/files.json','reference/robustness-fixed/files.json']:
        for name,h in read(ROOT/filename)['files'].items():
            if entry.sha256(ROOT/name)!=h:raise ValueError('fixed reference changed: '+name)


def run(out):
    verify_fixed();plan=read(PLAN);out=Path(out)
    prior=set()
    for name in ['capture-research-protocol.json','candidate-quality-protocol.json']:
        protocol=read(ROOT/'payload/config'/name);prior.update(protocol['development_seeds']+protocol['validation_seeds'])
    if prior&set(plan['seeds']):raise ValueError('seed reuse')
    if out.exists():raise ValueError('output must be new')
    out.mkdir(parents=True);(out/'annotations').mkdir();(out/'rir').mkdir()
    entry.write_json(out/'frozen-plan.json',plan)
    config=load_config(ROOT/'payload/config/sector-tracking.json');all_rows=[];per_seed=[];inputs=[];latency_rows=[]
    for kind,direction,room in itertools.product(plan['noise_types'],plan['directions'],plan['rooms']):
        condition=f'{kind}__{direction["name"]}__{room["name"]}'
        allowed=bool(batch.b.angle(np.array([1,0,0]),batch.b.unit(direction['az'],direction['el']))<=30)
        for seed in plan['seeds']:
            segment,metadata,rir=generate(plan,kind,direction,room,seed)
            rows,annotations=evaluate(segment,plan,direction,metadata,config)
            rirfile=out/'rir'/f'{direction["name"]}__{room["name"]}__{seed}.npy'
            if not rirfile.exists():np.save(rirfile,rir,allow_pickle=False)
            annotationfile=out/'annotations'/f'{condition}.json'
            if annotationfile.exists():
                if read(annotationfile)!=annotations:raise ValueError('annotation not reproducible across seeds')
            else:entry.write_json(annotationfile,annotations)
            inputs.append(dict(condition=condition,seed=seed,noise=kind,direction=direction,room=room,
                               target_allowed=allowed,rir_file=rirfile.relative_to(out).as_posix(),annotation_file=annotationfile.relative_to(out).as_posix(),**metadata))
            all_rows.extend(dict(condition=condition,seed=seed,target_allowed=allowed,**r) for r in rows)
            for method in METHODS:
                group=[r for r in rows if r['method']==method]
                per_seed.append(dict(condition=condition,seed=seed,target_allowed=allowed,method=method,**summarize(group)))
                for i,e in enumerate(plan['episodes']):
                    eligible=[r for r in group if r['scope']=='target_active' and r['episode']==i]
                    good=[r for r in eligible if r['fresh_valid'] and r['error_deg']<=10]
                    latency_rows.append(dict(condition=condition,seed=seed,method=method,episode=i,target_allowed=allowed,
                        found=bool(good),onset_to_correct_ms=good[0]['timestamp_ms']-e['start']/48 if good else None))
            print(f'{condition} seed={seed}',flush=True)
    pooled=[];comparisons=[];paired=[]
    for condition in sorted({r['condition'] for r in per_seed}):
        condition_rows=[r for r in all_rows if r['condition']==condition];allowed=condition_rows[0]['target_allowed']
        sums={m:summarize([r for r in condition_rows if r['method']==m]) for m in METHODS}
        pooled.extend(dict(condition=condition,target_allowed=allowed,method=m,**s) for m,s in sums.items())
        old,new=sums['original_quorum'],sums['gcc_beta075_quorum']
        side=flags(old,new,allowed,plan['side_effect_flags'])
        comparisons.append(dict(condition=condition,target_allowed=allowed,
            old_fresh=old['active_fresh_rate'],new_fresh=new['active_fresh_rate'],
            old_correct=old['active_correct_within10_rate'],new_correct=new['active_correct_within10_rate'],
            correct_delta=new['active_correct_within10_rate']-old['active_correct_within10_rate'],
            old_absent_false=old['absent_false_output_rate'],new_absent_false=new['absent_false_output_rate'],
            old_p95=old['p95_error_deg'],new_p95=new['p95_error_deg'],side_effect_flags='|'.join(side)))
        for seed in plan['seeds']:
            ix={r['method']:r for r in per_seed if r['condition']==condition and r['seed']==seed}
            for suffix in ['_raw','_quorum']:
                a,b=ix['gcc_beta075'+suffix],ix['original'+suffix]
                paired.append(dict(condition=condition,seed=seed,layer=suffix[1:],target_allowed=allowed,
                    fresh_delta=a['active_fresh_rate']-b['active_fresh_rate'],
                    correct_delta=a['active_correct_within10_rate']-b['active_correct_within10_rate'],
                    absent_false_delta=a['absent_false_output_rate']-b['absent_false_output_rate']))
    for name,rows in [('frames',all_rows),('per-seed',per_seed),('pooled',pooled),('comparisons',comparisons),('paired',paired),('latencies',latency_rows)]:batch.write_csv(out/(name+'.csv'),rows)
    entry.write_json(out/'pooled.json',pooled);entry.write_json(out/'comparisons.json',comparisons);entry.write_json(out/'inputs.json',inputs)
    verify_fixed();directory=Path(__file__).resolve().parent
    entry.write_json(out/'run.json',dict(status='COMPLETE_FROZEN_TRANSFER_CHECK',trials=len(inputs),conditions=len(comparisons),
        method_rows=len(all_rows),acoustic_frames=len(all_rows)//4,plan_sha256=entry.sha256(PLAN),
        source_sha256={p.name:entry.sha256(p) for p in [directory/n for n in ['robustness_sweep.py','candidate_quality_research.py','weighted_gcc.py','quorum_tracker.py','batch_presence.py','sector_tracker.py','six_mic_track.py','six_mic_localize.py','six_mic_baseline_core.py','audio_frames.py','h1_reader.py']]},
        artifact_sha256={p.relative_to(out).as_posix():entry.sha256(p) for p in sorted(out.rglob('*')) if p.is_file()},
        python=platform.python_version(),numpy=np.__version__,
        scope='No tuning. New noise/direction/synthetic RIR, three new seeds descriptive only. Causal tails labeled separately; not measured-room performance.'))
    print(f'COMPLETE: {len(inputs)} trials / {len(comparisons)} conditions')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    try:run(args.out)
    except (ValueError,OSError,TypeError) as error:print(json.dumps(dict(status='ERROR',message=str(error))));raise SystemExit(2)
