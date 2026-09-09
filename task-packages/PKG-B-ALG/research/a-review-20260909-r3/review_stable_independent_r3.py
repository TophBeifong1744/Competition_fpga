"""A-side recount and same-frame controls; never writes B evidence."""
import csv,gzip,hashlib,importlib.util,json,sys
from pathlib import Path
from collections import defaultdict,Counter
import numpy as np
root=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve()
here=root/'research/stable-wrong-01'; prior=root/'research/effective-perturbation-01'
spec=importlib.util.spec_from_file_location('reviewed_stable',here/'analyze_stable.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
sys.path.insert(0,str(root/'revisions/pr3-input-reference-02'))
import reference_inputs
refs=reference_inputs.References();refs.install()
assert a.s.make_rir == refs.make_rir
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def angle(u,v=(1,0,0)):
    u=np.asarray(u,dtype=float);v=np.asarray(v,dtype=float)
    return float(np.degrees(np.arctan2(np.linalg.norm(np.cross(u,v)),u@v)))
def assess(x,p):
    full=x['full']; tau=np.array(full['pair_delays_samples'],dtype=float)
    eligible=[]; angles=[]; changes=[]
    for k,(r,impact) in enumerate(zip(x['deleted'],x['impact'])):
        other=np.array(r['pair_delays_samples'],dtype=float);common=np.isfinite(tau)&np.isfinite(other)
        mass=np.array(impact['removed_mass_fraction']);bins=np.array(impact['removed_bins'])
        good=common&(bins>=3)&(mass>=.1)&(mass<=.8)
        if full['valid'] and r['valid'] and common.sum()>=5 and good.sum()>=5:
            eligible.append(k);angles.append(angle(full['unit_vector'],r['unit_vector']))
            changes.append(float(np.median(np.abs(tau[common]-other[common]))))
    cat='full_rejected' if not full['valid'] else 'unknown' if len(eligible)<2 else 'sensitive' if max(angles)>5 or max(changes)>.5 else 'stable'
    return cat,eligible,max(angles) if angles else None
p=read(prior/'protocol.json');plan=read(prior/'evidence/plan.json')['acoustic']
inputs={(m['condition'],m['seed']):m for m in read(prior/'evidence/inputs.json')}
groups=defaultdict(list);selected={};pop=0;classdiff=[];maxanglediff=0.;cross=0
with gzip.open(prior/'evidence/features.jsonl.gz','rt',encoding='utf-8') as stream:
    for line in stream:
        x=json.loads(line)
        # Freeze vocabulary without trusting the stored classification.
        if 'impact' not in x and 'impacts' in x:x['impact']=x['impacts']
        cat,eligible,change=assess(x,p)
        if cat!=x['diagnostic']['category']:classdiff.append((x['condition'],x['seed'],x['frame'],cat))
        if change is not None:maxanglediff=max(maxanglediff,abs(change-x['diagnostic']['max_angle_change']))
        m=inputs[x['condition'],x['seed']]
        if x['scope']!='target_active' or m['allowed']:continue
        pop+=1
        if x['full']['valid'] and angle(x['full']['unit_vector'])<=30+1e-10 and cat=='stable':
            key=(x['condition'],x['seed'],x['frame']);assert key not in selected
            selected[key]=x;groups[key[:2]].append(key[2])
            cross+=any(angle(x['deleted'][k]['unit_vector'])>30+1e-10 for k in eligible)
assert not classdiff,classdiff[:3]
assert (pop,len(selected),cross,len(selected)-cross)==(12312,563,317,246)
cohort=read(here/'cohort.json');assert set(selected)=={(x['condition'],x['seed'],x['frame']) for x in cohort}
fresh=totalfresh=0
with (prior/'evidence/frames.csv').open(newline='',encoding='utf-8') as stream:
    for x in csv.DictReader(stream):
        if x['method']!='effective_known_only':continue
        key=(x['condition'],int(x['seed']),int(x['frame_index']))
        if key in selected:fresh+=x['fresh_valid']=='True'
        if x['scope']=='target_active' and not inputs[key[:2]]['allowed']:totalfresh+=x['fresh_valid']=='True'
assert (fresh,totalfresh)==(182,205)
old={(x['condition'],x['seed'],x['frame'],x['control']):x for x in read(here/'controls.json')}
counts=defaultdict(Counter);inputchecks=[];framechecks=[];maxerror=0.;maxcone=0.
dry=next(r for r in plan['rooms'] if r['name']=='dry')
for key,indices in sorted(groups.items()):
    m=inputs[key];target,noise,roommeta=a.components(plan,m,m['room']);clean,same_noise,drymeta=a.components(plan,m,dry)
    assert np.array_equal(noise,same_noise)
    original,generated=a.source.generate(plan,m['noise'],m['direction'],m['room'],m['seed'])
    assert all(generated[k] == m[k] for k in ['input_sha256','target_sha256','noise_sha256','rir_sha256'])
    checks=dict(condition=key[0],seed=key[1],hashes={})
    for kind,data,meta in [('original',target+noise,roommeta),('no_noise',target,roommeta),('dry',clean+noise,drymeta),('dry_no_noise',clean,drymeta)]:
        segment=a.adapt_six_mic_baseline(data,sample_rate_hz=48000,positions_m=a.f.b.POS,source_id='A-review-'+kind,source_sha256=sha(Path(__file__)))
        checks['hashes'][kind]=segment.provenance['samples_sha256']
        if kind=='original':assert checks['hashes'][kind]==generated['input_sha256']
        for frame in a.iter_frames(segment):
            if frame.index not in indices:continue
            # Derive stable-received activity independently from causal support.
            episodes=[i for i,e in enumerate(plan['episodes']) if frame.row_start>=e['start']+plan['edge_samples']+meta['support_last'] and frame.row_stop-1<=e['stop']-plan['edge_samples']+meta['support_first']]
            assert len(episodes)==1
            estimates=a.f.old.estimates(frame,p['omitted_bands_hz'])
            diagnostic=a.f.assess(estimates[0],estimates[1:],a.f.impacts(frame,p['omitted_bands_hz']),p['impact'],p['loo'])
            full=estimates[0];valid=full['valid'];cone=angle(full['unit_vector']) if valid else None
            wrong=bool(valid and cone<=30+1e-10);ref=old[key+(frame.index,kind)]
            assert (valid,wrong,diagnostic['category'])==(ref['valid'],ref['wrong_incone'],ref['category']),(key,frame.index,kind)
            if valid:
                error=angle(full['unit_vector'],a.f.b.unit(m['direction']['az'],m['direction']['el']))
                maxerror=max(maxerror,abs(error-ref['error_deg']));maxcone=max(maxcone,abs(cone-ref['cone_deg']))
                assert abs(error-ref['error_deg'])<1e-6 and abs(cone-ref['cone_deg'])<1e-6
            counts[kind].update(n=1,valid=int(valid),wrong=int(wrong),wrong_stable=int(wrong and diagnostic['category']=='stable'))
            framechecks.append(dict(condition=key[0],seed=key[1],frame=frame.index,control=kind,row_start=frame.row_start,row_stop=frame.row_stop,episode=episodes[0],input_frame_sha256=a.s.array_hash(data[:,frame.row_start:frame.row_stop]),valid=valid,wrong_incone=wrong))
    checks['old_input_hash']=m['input_sha256'];checks['original_hash_matches']=checks['hashes']['original']==m['input_sha256']
    checks['target_hash_matches']=a.s.array_hash(target)==m['target_sha256'];checks['noise_hash_matches']=a.s.array_hash(noise)==m['noise_sha256']
    inputchecks.append(checks);print(key,'PASS',flush=True)
assert [counts[k]['wrong'] for k in ['original','no_noise','dry','dry_no_noise']]==[563,185,309,0]
assert counts['dry']['n']-counts['dry']['valid']==14
assert all(c['original_hash_matches'] and c['target_hash_matches'] and c['noise_hash_matches'] for c in inputchecks)
result=dict(reviewed_commit='6491d1bab04038b71fdd8c22d45a58455aa58ade',status='PASS_EXACT_INPUT_AND_NUMERIC_REPRODUCTION',outside_active=pop,selected=len(selected),crossing=cross,all_effective_inside=len(selected)-cross,same_frame_fresh=fresh,all_outside_fresh=totalfresh,counts={k:dict(v) for k,v in counts.items()},category_differences=classdiff,max_angle_metric_difference=maxanglediff,max_control_error_difference=maxerror,max_control_cone_difference=maxcone,inputs=inputchecks,frames=framechecks,reference_uses=refs.uses,scope='Selected retrospective cohort, raw candidate controls only; four historical input hashes strictly checked for all 26 original trials; no independent validation or tracker control rerun')
if out.exists():raise RuntimeError('Refuse overwrite')
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print({k:v for k,v in result.items() if k not in ['frames','inputs']})
