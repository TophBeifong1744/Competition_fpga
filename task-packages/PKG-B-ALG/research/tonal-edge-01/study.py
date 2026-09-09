"""Retrospective mechanism diagnosis; frozen algorithms, no model selection."""
import csv,hashlib,json,sys
from pathlib import Path
from collections import defaultdict,Counter
from dataclasses import replace
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'payload/model/python'))
import robustness_sweep as s
from audio_frames import adapt_six_mic_baseline,iter_frames,to_six_mic_baseline
from quorum_tracker import QuorumSession
from six_mic_track import load_config

def backgrounds(plan,seed,count):
    tone=[];white=[]
    for m in range(6):
        rng=np.random.default_rng(np.random.SeedSequence([seed,200+m]))
        time=np.arange(count)/48000
        t=np.sin(2*np.pi*1000*time+rng.uniform(-np.pi,np.pi))
        w=.05*rng.normal(size=count)
        scale=plan['noise_nominal_rms']/np.sqrt(np.mean((t+w)**2))
        tone.append(t*scale);white.append(w*scale)
    tone=np.array(tone);white=np.array(white)
    replacement=[]
    for m in range(6):
        x=s.batch.probe(np.random.default_rng(np.random.SeedSequence([seed,300+m])),count)
        x=x*np.sqrt(np.mean(tone[m]**2))+white[m]
        replacement.append(x/np.sqrt(np.mean(x*x))*plan['noise_nominal_rms'])
    return {'original_tone':tone+white,'tone_removed':white,'equal_rms_band':np.array(replacement)}

def spectral(frame):
    x=np.fft.rfft(to_six_mic_baseline(frame)*np.hanning(1024),axis=1)
    freq=np.fft.rfftfreq(1024,1/48000);band=(freq>=300)&(freq<=4000);near=(freq>=900)&(freq<=1100)
    shares={1:[],.75:[]};counts=[];power=[]
    for i,j in s.batch.b.PAIRS:
        amp=np.abs(x[i]*x[j].conj());mask=band&(amp>=.02*max(float(amp[band].max()),1e-15));counts.append(int(mask.sum()))
        power.append(float(amp[near&band].sum()/max(amp[band].sum(),1e-15)))
        for beta in shares:
            weights=np.where(mask,amp**(1-beta),0)
            shares[beta].append(float(weights[near].sum()/max(weights.sum(),1e-15)))
    return {b:dict(tone_weight_share=float(np.mean(v)),cross_amp_tone_share=float(np.mean(power)),mask_bins_mean=float(np.mean(counts)),mask_under12_pairs=sum(n<12 for n in counts)) for b,v in shares.items()}

def bucket(c,out):
    if not c['valid']:return 'baseline_rejected'
    if s.batch.b.angle(np.array(c['unit_vector']),np.array([1.,0,0]))>30+1e-10:return 'outside_cone'
    if not out['fresh_valid']:return 'tracker_wait_or_jump'
    return 'fresh'

def run():
    out=HERE/'evidence-run-02'
    if out.exists():raise ValueError('output exists')
    fixed=s.read(HERE/'fixed-files.json')
    for n,h in fixed.items():assert s.entry.sha256(ROOT/n)==h,n
    plan=s.read(ROOT/'payload/config/robustness-sweep.json');protocol=s.read(HERE/'protocol.json')
    oldinputs=s.read(ROOT/'evidence/robustness-run-01/inputs.json')
    out.mkdir();rows=[];inputs=[];config=load_config(ROOT/'payload/config/sector-tracking.json')
    for direction in plan['directions']:
        if direction['name']=='outside':continue
        for room in plan['rooms']:
            condition=direction['name']+'__'+room['name']
            for seed in plan['seeds']:
                original,meta,rir=s.generate(plan,'tonal',direction,room,seed)
                previous=next(i for i in oldinputs if i['condition']=='tonal__'+condition and i['seed']==seed)
                assert meta['input_sha256']==previous['input_sha256']
                bg=backgrounds(plan,seed,plan['duration_samples'])
                # Independent decomposition must reproduce the saved noise numerically.
                np.testing.assert_allclose(bg['original_tone'],s.noise(plan,'tonal',seed,plan['duration_samples']),rtol=0,atol=5e-12)
                target=s.convolve(s.batch.probe(np.random.default_rng(np.random.SeedSequence([seed,1])),plan['duration_samples'])*sum(s.batch.envelope(np.arange(plan['duration_samples']),e['start'],e['stop'],plan['edge_samples']) for e in plan['episodes']),rir,plan['duration_samples'])
                expected=np.array([(meta['paths'][i]['direct_delay_samples']-meta['paths'][j]['direct_delay_samples']) for i,j in s.batch.b.PAIRS])
                for intervention in protocol['interventions']:
                    segment=original if intervention=='original_tone' else adapt_six_mic_baseline(target+bg[intervention],sample_rate_hz=48000,positions_m=s.batch.b.POS,source_id=condition+':'+intervention,source_sha256=s.entry.sha256(__file__))
                    inputs.append(dict(condition=condition,seed=seed,intervention=intervention,input_sha256=segment.provenance['samples_sha256']))
                    sessions={(beta,cone):QuorumSession(replace(config,cone_half_angle_deg=cone)) for beta in [1,.75] for cone in [30.,40.]}
                    for frame in iter_frames(segment):
                        candidates={1:s.entry.localize_frame(frame),.75:s.weighted_gcc.localize(frame,.75)}
                        outputs={(beta,cone):session.update(candidates[beta]) for (beta,cone),session in sessions.items()}
                        label=s.labels(plan,frame.row_start,frame.row_stop,meta,direction)
                        if label['scope']!='target_active':continue
                        spec=spectral(frame)
                        for beta,c in candidates.items():
                            o=outputs[beta,30.];wide=outputs[beta,40.];u=c['unit_vector']
                            tau=np.array([np.nan if t is None else t for t in c['pair_delays_samples']]);good=np.isfinite(tau)
                            err=s.batch.b.angle(np.array(u),np.array(label['target_unit_vector'])) if c['valid'] else None
                            tracked_error=s.batch.b.angle(np.array(o['direction']),np.array(label['target_unit_vector'])) if o['fresh_valid'] else None
                            wide_error=s.batch.b.angle(np.array(wide['direction']),np.array(label['target_unit_vector'])) if wide['fresh_valid'] else None
                            rows.append(dict(condition=condition,seed=seed,intervention=intervention,beta=beta,frame=frame.index,
                                valid=c['valid'],error=err,cone_angle=s.batch.b.angle(np.array(u),np.array([1.,0,0])) if c['valid'] else None,
                                pair_rmse=float(np.sqrt(np.mean((tau[good]-expected[good])**2))) if good.any() else None,
                                residual=c['residual_samples'],raw_norm=c['raw_vector_norm'],finite_pairs=c['finite_pairs'],rejections='|'.join(c['rejection_reasons']),
                                bucket=bucket(c,o),tracker_reason=o['reason'],fresh=o['fresh_valid'],correct=tracked_error is not None and tracked_error<=10,
                                wide_fresh=wide['fresh_valid'],wide_correct=wide_error is not None and wide_error<=10,**spec[beta]))
                    print(condition,seed,intervention,flush=True)
    s.batch.write_csv(out/'frames.csv',rows);s.entry.write_json(out/'inputs.json',inputs)
    for n,h in fixed.items():assert s.entry.sha256(ROOT/n)==h,n
    s.entry.write_json(out/'run.json',dict(trials=len(inputs),active_method_rows=len(rows),source_sha256=s.entry.sha256(__file__),protocol_sha256=s.entry.sha256(HERE/'protocol.json'),artifacts={p.name:s.entry.sha256(p) for p in out.iterdir() if p.is_file()},status='COMPLETE_RETROSPECTIVE_DIAGNOSIS'))

if __name__=='__main__':run()
