"""Audit research artifacts without running or tuning the experimental tracker."""
from collections import defaultdict
import csv
import json
import math
from pathlib import Path
import numpy as np
import hashlib

ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def records(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def audit():
    protocol=read(ROOT/'payload/config/capture-research-protocol.json')
    frozen=read(ROOT/'reference/batch-presence-fixed/frozen-files.json')
    for name,h in frozen['files'].items():assert sha(ROOT/name)==h,name
    development=ROOT/'evidence/capture-development-01';heldout=ROOT/'evidence/capture-heldout-01'
    selection=read(development/'selection.json')
    assert not set(protocol['development_seeds'])&set(protocol['validation_seeds'])
    assert selection['selected']['name']=='quorum5of12'
    totals={};seed_statistics={}
    for path,split in [(development,'development_seeds'),(heldout,'validation_seeds')]:
        run=read(path/'run.json');plan=read(path/'plan.json')
        assert run['seeds']==plan['seeds']==protocol[split]
        assert run['source_sha256']==selection['source_sha256']
        assert run['protocol_sha256']==selection['protocol_sha256']==sha(ROOT/'payload/config/capture-research-protocol.json')
        for name,h in run['artifact_sha256'].items():assert sha(path/name)==h,name
        for name,h in run['source_sha256'].items():assert sha(ROOT/'payload/model/python'/name)==h,name
        if path==heldout:assert run['selected_from_sha256']==sha(development/'selection.json')
        groups=defaultdict(list);pooled_groups=defaultdict(list)
        rows=records(path/'frames.csv')
        for r in rows:
            start,stop=int(r['row_start']),int(r['row_stop']);fresh=r['fresh_valid']=='True';stale=r['stale']=='True'
            assert not(fresh and stale)
            if fresh:assert r['baseline_valid']=='True'
            if stale:assert float(r['timestamp_ms'])<=float(r['display_expires_at_ms'])+1e-10
            active=[];emitting=False
            if r['scenario']!='interferer_only':
                for i,e in enumerate(plan['episodes']):
                    if start>=e['start']+plan['edge_samples'] and stop-1<=e['stop']-plan['edge_samples']:active.append(i)
                    emitting|=max(start,e['start']+1)<min(stop,e['stop'])
            scope='target_absent' if not emitting else 'target_active' if len(active)==1 else 'transition'
            assert r['scope']==scope
            if fresh:
                u=np.array([float(r['estimate_'+a]) for a in 'xyz'])
                assert np.isclose(np.linalg.norm(u),1,atol=1e-10)
                if r['method']!='baseline':assert np.degrees(np.arccos(np.clip(u[0],-1,1)))<=30+1e-8
                if scope=='target_active':
                    e=plan['episodes'][active[0]];az,el=np.deg2rad([e['azimuth_deg'],e['elevation_deg']])
                    truth=np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
                    error=np.degrees(np.arccos(np.clip(truth@u,-1,1)))
                    assert math.isclose(float(r['error_deg']),error,abs_tol=1e-6)
            if not fresh or scope!='target_active':assert r['error_deg']==''
            groups[r['scenario'],r['seed'],r['method']].append(r)
            pooled_groups[r['scenario'],r['method']].append(r)
        def verify(s,group):
            a=[r for r in group if r['scope']=='target_active'];z=[r for r in group if r['scope']=='target_absent']
            errors=[float(r['error_deg']) for r in a if r['fresh_valid']=='True']
            wrong=sum(e>30 for e in errors);false=sum(r['fresh_valid']=='True' for r in z)
            expected=dict(all_frames=len(group),active_frames=len(a),active_fresh_frames=len(errors),
                active_fresh_rate=len(errors)/len(a) if a else None,
                active_correct_within10_rate=sum(e<=10 for e in errors)/len(a) if a else None,
                p50_error_deg=float(np.percentile(errors,50)) if errors else None,
                p95_error_deg=float(np.percentile(errors,95)) if errors else None,
                active_wrong_over30=wrong,active_wrong_rate_all=wrong/len(a) if a else None,
                active_wrong_rate_fresh=wrong/len(errors) if errors else None,
                absent_frames=len(z),absent_fresh_false_outputs=false,
                absent_false_output_rate=false/len(z) if z else None,
                absent_hold_display_frames=sum(r['stale']=='True' for r in z),
                transition_frames=sum(r['scope']=='transition' for r in group),
                transition_fresh_outputs=sum(r['scope']=='transition' and r['fresh_valid']=='True' for r in group),
                hold_frames=sum(r['stale']=='True' for r in group))
            for k,v in expected.items():
                if v is None:assert s[k] in ('',None)
                else:assert math.isclose(float(s[k]),v,abs_tol=1e-12,rel_tol=1e-12),k
        per=records(path/'per-seed.csv')
        for s in per:verify(s,groups[s['scenario'],s['seed'],s['method']])
        pooled=read(path/'pooled.json')
        for s in pooled:verify(s,pooled_groups[s['scenario'],s['method']])
        index={(r['scenario'],r['seed'],r['method']):r for r in per}
        for r in records(path/'paired.csv'):
            a=index[r['scenario'],r['seed'],r['variant']][r['metric']]
            b=index[r['scenario'],r['seed'],'tracker'][r['metric']]
            if a=='' or b=='':assert r['delta']==''
            else:assert math.isclose(float(r['delta']),float(a)-float(b),abs_tol=1e-12)
        for r in records(path/'latencies.csv'):
            eligible=[g for g in groups[r['scenario'],r['seed'],r['method']] if g['scope']=='target_active' and g['episode']==r['episode']]
            correct=[g for g in eligible if g['fresh_valid']=='True' and float(g['error_deg'])<=10]
            assert (r['found']=='True')==bool(correct)
            assert (r['applicable']=='True')==bool(eligible)
            if correct:assert math.isclose(float(r['onset_to_first_correct_ms']),float(correct[0]['timestamp_ms'])-float(r['onset_ms']),abs_tol=1e-12)
            else:assert r['onset_to_first_correct_ms']==''
        name=path.name;totals[name]=dict(rows=len(rows),per_seed_groups=len(per),pooled_groups=len(pooled))
        if path==heldout:
            data=[]
            for seed in protocol['validation_seeds']:
                old=index['band_noise0',str(seed),'tracker'];new=index['band_noise0',str(seed),'quorum5of12']
                data.append(dict(seed=seed,old_fresh=float(old['active_fresh_rate']),new_fresh=float(new['active_fresh_rate']),
                    correct_gain=float(new['active_correct_within10_rate'])-float(old['active_correct_within10_rate'])))
            seed_statistics=dict(noise_per_seed=data,improved_seeds=sum(x['correct_gain']>0 for x in data),
                new_fresh_min=min(x['new_fresh'] for x in data),new_fresh_max=max(x['new_fresh'] for x in data),
                correct_gain_min=min(x['correct_gain'] for x in data),correct_gain_max=max(x['correct_gain'] for x in data))
    return dict(status='PASS',fixed_reference_files=len(frozen['files']),seed_splits_disjoint=True,
        selected_code_matches_heldout=True,phases=totals,heldout_seed_statistics=seed_statistics,
        auditor_sha256=sha(Path(__file__)),selection_sha256=sha(development/'selection.json'),heldout_run_sha256=sha(heldout/'run.json'),
        checks='All rows: presence, angles, fresh quality/range gates, HOLD exclusion; all summary denominators, paired gains and latencies; frozen files and provenance.')


if __name__=='__main__':
    target=ROOT/'evidence/capture-research-audit.json'
    if target.exists():raise ValueError('audit output exists')
    result=audit();target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
