"""Persisted-row audit, loss attribution and matched intervention summaries."""
import csv,json,math
from collections import defaultdict,Counter
import numpy as np
import study as d

def readrows(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def aggregate(g):
    def avg(k):
        values=[float(r[k]) for r in g if r[k]!='']
        return float(np.mean(values)) if values else None
    return dict(frames=len(g),valid=sum(r['valid']=='True' for r in g),
        rejected=sum(r['bucket']=='baseline_rejected' for r in g),outside=sum(r['bucket']=='outside_cone' for r in g),
        waiting=sum(r['bucket']=='tracker_wait_or_jump' for r in g),fresh=sum(r['fresh']=='True' for r in g),correct=sum(r['correct']=='True' for r in g),
        wide_correct=sum(r['wide_correct']=='True' for r in g),pair_rmse_mean=avg('pair_rmse'),residual_mean=avg('residual'),
        cone_angle_valid_mean=avg('cone_angle'),tone_weight_share_mean=avg('tone_weight_share'),cross_amp_tone_share_mean=avg('cross_amp_tone_share'),
        mask_bins_mean=avg('mask_bins_mean'),mask_under12_pairs_mean=avg('mask_under12_pairs'),
        rejection_reasons=dict(Counter(x for r in g for x in r['rejections'].split('|') if x)))

def main():
    out=d.HERE/'evidence-run-02';run=d.s.read(out/'run.json')
    assert d.s.entry.sha256(d.HERE/'study.py')==run['source_sha256']
    for n,h in run['artifacts'].items():assert d.s.entry.sha256(out/n)==h
    fixed=d.s.read(d.HERE/'fixed-files.json')
    for n,h in fixed.items():assert d.s.entry.sha256(d.ROOT/n)==h
    rows=readrows(out/'frames.csv');groups=defaultdict(list);perseed=defaultdict(list);ix={}
    for r in rows:
        groups[r['condition'],r['intervention'],r['beta']].append(r)
        perseed[r['condition'],r['intervention'],r['seed'],r['beta']].append(r)
        key=r['condition'],r['intervention'],r['seed'],r['frame'],r['beta'];assert key not in ix;ix[key]=r
        assert r['bucket'] in ['baseline_rejected','outside_cone','tracker_wait_or_jump','fresh']
        assert (r['bucket']=='baseline_rejected')==(r['valid']=='False')
        if r['valid']=='True':assert (r['bucket']=='outside_cone')==(float(r['cone_angle'])>30+1e-10)
        assert (r['bucket']=='fresh')==(r['fresh']=='True')
        assert r['correct']!='True' or r['fresh']=='True'
    # Compare all original-tone active candidates and tracking outputs with approved evidence.
    matched=0
    with (d.ROOT/'evidence/robustness-run-01/frames.csv').open(encoding='utf-8',newline='') as f:
        for old in csv.DictReader(f):
            if not old['condition'].startswith('tonal__') or '__outside__' in old['condition'] or old['scope']!='target_active':continue
            beta='1' if old['method'].startswith('original') else '0.75'
            r=ix[old['condition'][7:],'original_tone',old['seed'],old['frame_index'],beta]
            assert (r['valid']=='True')==(old['candidate_valid']=='True')
            if old['method'].endswith('_quorum'):
                assert r['fresh']==old['fresh_valid'] and r['tracker_reason']==old['reason']
                assert (r['correct']=='True')==(old['fresh_valid']=='True' and float(old['error_deg'])<=10)
            elif old['fresh_valid']=='True':assert math.isclose(float(r['error']),float(old['error_deg']),abs_tol=1e-8)
            matched+=1
    summaries=[];seed_summaries=[];flow=[]
    for (condition,intervention,beta),g in sorted(groups.items()):
        a=aggregate(g);assert sum(a[k] for k in ['rejected','outside','waiting','fresh'])==a['frames']
        summaries.append(dict(condition=condition,intervention=intervention,beta=beta,**a))
    for (condition,intervention,seed,beta),g in sorted(perseed.items()):seed_summaries.append(dict(condition=condition,intervention=intervention,seed=seed,beta=beta,**aggregate(g)))
    for condition,intervention in sorted({(r['condition'],r['intervention']) for r in rows}):
        g=groups[condition,intervention,'1'];lost=Counter();gained=Counter();both=Counter();candidate_transitions=Counter()
        for old in g:
            new=ix[condition,intervention,old['seed'],old['frame'],'0.75']
            oc,nc=old['correct']=='True',new['correct']=='True'
            if oc and not nc:lost[new['bucket'] if new['bucket']!='fresh' else 'fresh_wrong_over10']+=1
            if nc and not oc:gained[old['bucket'] if old['bucket']!='fresh' else 'fresh_wrong_over10']+=1
            both[str(oc)+'->'+str(nc)]+=1
            candidate_transitions[old['bucket']+'->'+new['bucket']]+=1
        flow.append(dict(condition=condition,intervention=intervention,lost=dict(lost),gained=dict(gained),correct_transitions=dict(both),bucket_transitions=dict(candidate_transitions)))
    report=dict(status='PASS',active_method_rows=len(rows),prior_method_rows_matched=matched,prior_files_unchanged=len(fixed),trials=run['trials'],
        summaries=summaries,per_seed=seed_summaries,flows=flow,auditor_sha256=d.s.entry.sha256(__file__),
        checks='All input and source hashes; unchanged prior files; disjoint buckets; every original-tone active raw/quorum row matches approved local evidence; pooled and paired loss/gain attribution. Historical seeds reused for diagnosis.')
    path=d.HERE/'analysis.json'
    if path.exists():raise ValueError('output exists')
    d.s.entry.write_json(path,report)
    for condition in sorted({r['condition'] for r in summaries}):
        for intervention in ['original_tone','tone_removed','equal_rms_band']:
            a,b=[next(r for r in summaries if (r['condition'],r['intervention'],r['beta'])==(condition,intervention,beta)) for beta in ['1','0.75']]
            print(condition,intervention,'correct%',round(100*a['correct']/a['frames'],2),round(100*b['correct']/b['frames'],2),'reject',a['rejected'],b['rejected'],'outside',a['outside'],b['outside'],'wait',a['waiting'],b['waiting'],'wide_delta_pp',round(100*(b['wide_correct']-a['wide_correct'])/a['frames'],2),'pairRMSE',round(a['pair_rmse_mean'],3),round(b['pair_rmse_mean'],3),'weight',round(a['tone_weight_share_mean'],3),round(b['tone_weight_share_mean'],3))
    print('PASS',len(rows),'active rows;',matched,'prior rows matched')

if __name__=='__main__':main()
