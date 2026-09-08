"""Independently recompute saved transfer-study labels and metrics; no tuning."""
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
import numpy as np
from audit_candidate_quality import verify_metrics
from audit_capture_research import ROOT,read,sha,records
sys.path.insert(0,str(ROOT/'payload/model/python'))
import robustness_sweep as sweep


def audit():
    path=ROOT/'evidence/robustness-run-01';run=read(path/'run.json');p=read(path/'frozen-plan.json')
    sweep.verify_fixed()
    assert sha(sweep.PLAN)==run['plan_sha256']
    for n,h in run['artifact_sha256'].items():assert sha(path/n)==h,n
    for n,h in run['source_sha256'].items():assert sha(ROOT/'payload/model/python'/n)==h,n
    inputs=read(path/'inputs.json');ix={(i['condition'],str(i['seed'])):i for i in inputs}
    assert len(ix)==144 and len({i['condition'] for i in inputs})==48
    label_index={};rir_checked=set()
    for i in inputs:
        h=np.load(path/i['rir_file'],allow_pickle=False)
        assert sweep.array_hash(h)==i['rir_sha256']
        support=np.nonzero(h)[1];first,last=int(support.min()),int(support.max())
        assert (first,last)==(i['support_first'],i['support_last'])
        rir_checked.add(i['rir_file'])
        for a in read(path/i['annotation_file']):
            start,stop=a['row_start'],a['row_stop'];full=[];present=False;emitting=False
            for eidx,e in enumerate(p['episodes']):
                if start>=e['start']+p['edge_samples']+last and stop-1<=e['stop']-p['edge_samples']+first:full.append(eidx)
                present|=start<e['stop']+last and stop>e['start']+1+first
                emitting|=start<e['stop'] and stop>e['start']+1
            scope='target_absent' if not present else 'target_active' if len(full)==1 else 'transition'
            assert a['scope']==scope and a['episode']==(full[0] if scope=='target_active' else None)
            assert a['emission_off']==(not emitting)
            assert a['tail_possible_after_emission']==(not emitting and present)
            label_index[i['condition'],str(i['seed']),str(a['frame_index'])]=a
    groups=defaultdict(list);pools=defaultdict(list)
    rows=records(path/'frames.csv')
    for r in rows:
        key=r['condition'],r['seed'];a=label_index[*key,r['frame_index']]
        assert r['scope']==a['scope']
        for k in ['emission_off','tail_possible_after_emission']:assert (r[k]=='True')==a[k]
        fresh=r['fresh_valid']=='True';stale=r['stale']=='True'
        assert not(fresh and stale)
        if fresh:
            assert r['candidate_valid']=='True'
            u=np.array([float(r['estimate_'+c]) for c in 'xyz'])
            assert np.isclose(np.linalg.norm(u),1)
            if r['method'].endswith('_quorum'):assert np.degrees(np.arccos(np.clip(u[0],-1,1)))<=30+1e-8
            if a['scope']=='target_active':
                truth=np.array(a['target_unit_vector']);err=np.degrees(np.arccos(np.clip(truth@u,-1,1)))
                assert math.isclose(float(r['error_deg']),err,abs_tol=1e-6)
        if not fresh or a['scope']!='target_active':assert r['error_deg']==''
        groups[*key,r['method']].append(r);pools[r['condition'],r['method']].append(r)
    def check(s,g):
        verify_metrics(s,g)
        tail=[r for r in g if r['tail_possible_after_emission']=='True']
        assert int(s['tail_after_emission_frames'])==len(tail)
        assert int(s['tail_after_emission_fresh'])==sum(r['fresh_valid']=='True' for r in tail)
        assert int(s['tail_after_emission_hold'])==sum(r['stale']=='True' for r in tail)
    per=records(path/'per-seed.csv');pool=read(path/'pooled.json')
    for s in per:check(s,groups[s['condition'],s['seed'],s['method']])
    for s in pool:check(s,pools[s['condition'],s['method']])
    poolix={(s['condition'],s['method']):s for s in pool}
    for c in read(path/'comparisons.json'):
        a=poolix[c['condition'],'original_quorum'];b=poolix[c['condition'],'gcc_beta075_quorum'];flags=[];lim=p['side_effect_flags']
        if c['target_allowed']:
            if b['active_correct_within10_rate']-a['active_correct_within10_rate'] < -lim['correct_rate_drop']:flags.append('correct_rate_drop')
            if a['p95_error_deg'] is not None and b['p95_error_deg'] is not None and b['p95_error_deg']-a['p95_error_deg']>lim['p95_error_increase_deg']:flags.append('p95_increase')
        elif b['active_fresh_rate']-a['active_fresh_rate']>lim['outside_fresh_increase']:flags.append('outside_target_output_increase')
        if b['absent_false_output_rate']-a['absent_false_output_rate']>lim['absent_false_increase']:flags.append('absent_false_increase')
        assert c['side_effect_flags']=='|'.join(flags)
        for prefix,s in [('old',a),('new',b)]:
            for k,m in [('fresh','active_fresh_rate'),('correct','active_correct_within10_rate'),('absent_false','absent_false_output_rate'),('p95','p95_error_deg')]:assert c[prefix+'_'+k]==s[m]
        assert math.isclose(c['correct_delta'],b['active_correct_within10_rate']-a['active_correct_within10_rate'],abs_tol=1e-12)
    pi={(s['condition'],s['seed'],s['method']):s for s in per}
    for d in records(path/'paired.csv'):
        old=pi[d['condition'],d['seed'],'original_'+d['layer']];new=pi[d['condition'],d['seed'],'gcc_beta075_'+d['layer']]
        for k,m in [('fresh_delta','active_fresh_rate'),('correct_delta','active_correct_within10_rate'),('absent_false_delta','absent_false_output_rate')]:
            assert math.isclose(float(d[k]),float(new[m])-float(old[m]),abs_tol=1e-12)
    for d in records(path/'latencies.csv'):
        g=groups[d['condition'],d['seed'],d['method']]
        good=[r for r in g if r['scope']=='target_active' and r['episode']==d['episode'] and r['fresh_valid']=='True' and float(r['error_deg'])<=10]
        assert (d['found']=='True')==bool(good)
        if good:assert math.isclose(float(d['onset_to_correct_ms']),float(good[0]['timestamp_ms'])-p['episodes'][int(d['episode'])]['start']/48,abs_tol=1e-12)
        else:assert d['onset_to_correct_ms']==''
    # Reconstruct 12 complete mixtures, one per noise x room, first direction/seed.
    reconstructed=0
    for i in inputs:
        if i['direction']['name']=='front' and i['seed']==p['seeds'][0]:
            _,meta,_=sweep.generate(p,i['noise'],i['direction'],i['room'],i['seed'])
            for k in ['input_sha256','noise_sha256','target_sha256','rir_sha256']:assert meta[k]==i[k]
            reconstructed+=1
    return dict(status='PASS',method_rows=len(rows),trials=len(inputs),unique_rir_checked=len(rir_checked),reconstructed_mixtures=reconstructed,
        per_seed_groups=len(per),pooled_groups=len(pool),frozen_references_unchanged=True,
        checks='Saved artifact/source hashes; received/tail labels against RIR support; directions; fresh/HOLD; pooled and seed metrics; paired deltas; latencies. 12/144 mixtures reconstructed, no algorithm rerun.',
        auditor_sha256=sha(Path(__file__)),helper_sha256={n:sha(ROOT/n) for n in ['audit_candidate_quality.py','audit_capture_research.py']})


if __name__=='__main__':
    out=ROOT/'evidence/robustness-audit.json'
    if out.exists():raise ValueError('audit output exists')
    result=audit();out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
