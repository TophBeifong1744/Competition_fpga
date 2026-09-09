# Revised auditor; original immutable source: research/leave-band-out-01/audit.py
import sys
from common import ROOT, DIFF, angle, angle as stable_angle, verify_package
sys.path.insert(0, str(ROOT/'research/leave-band-out-01'))
"""Audit saved subband evidence and screening statistics; retain unknown cases."""
import csv,gzip,json,math,sys
from collections import defaultdict,Counter
import numpy as np
import run_study as s
sys.path.insert(0,str(s.ROOT))
from audit_candidate_quality import verify_metrics

def records(path):
    with path.open(encoding='utf-8',newline='') as file:return list(csv.DictReader(file))

def run():
    verify_package();out=s.HERE/'evidence';p=s.s.read(s.HERE/'protocol.json');run=s.s.read(out/'run.json');plan=s.s.read(out/'plan.json')['acoustic']
    assert run['trials']==144 and run['acoustic_frames']==67248 and run['method_rows']==268992
    assert run['protocol_sha256']==s.s.entry.sha256(s.HERE/'protocol.json')
    for n,h in run['source_sha256'].items():assert s.s.entry.sha256(s.HERE/n)==h
    for n,h in run['artifacts'].items():assert s.s.entry.sha256(out/n)==h
    inputs=s.s.read(out/'inputs.json');ix={(i['condition'],str(i['seed'])):i for i in inputs};assert len(ix)==144
    assert set(ix)=={(noise+'__'+d['name']+'__'+room,str(seed)) for noise in p['noises'] for d in p['directions'] for room in p['rooms'] for seed in p['seeds']}
    diagnostics={};risk=defaultdict(Counter);cross_risk=defaultdict(Counter);category_by_case=defaultdict(Counter)
    with gzip.open(out/'features.jsonl.gz','rt',encoding='utf-8') as file:
        for line in file:
            r=json.loads(line);key=r['condition'],str(r['seed']),str(r['frame']);assert key not in diagnostics
            full=r['full'];angles=[];changes=[];comparable=[];crossings=0
            if full['valid']:
                u=np.array(full['unit_vector']);tau=np.array([np.nan if t is None else t for t in full['pair_delays_samples']])
                inside=float(np.degrees(np.arccos(np.clip(u[0],-1,1))))<=30+1e-10
                for j,v in enumerate(r['deleted']):
                    if not v['valid']:continue
                    other=np.array([np.nan if t is None else t for t in v['pair_delays_samples']]);good=np.isfinite(tau)&np.isfinite(other)
                    if good.sum()<5:continue
                    comparable.append(j);vec=np.array(v['unit_vector'])
                    angles.append(stable_angle(u,vec))
                    changes.append(float(np.median(np.abs(tau[good]-other[good]))))
                    crossings+=inside!=(float(np.degrees(np.arccos(np.clip(vec[0],-1,1))))<=30+1e-10)
            angle=max(angles) if angles else None;change=max(changes) if changes else None
            if not full['valid']:category='full_rejected'
            elif len(comparable)<2:category='unknown'
            elif angle>5 or change>.5:category='sensitive'
            else:category='stable'
            expected=dict(category=category,comparable_count=len(comparable),comparable_indices=comparable,max_angle_change=angle,max_median_delay_change=change,cone_crossings=int(crossings))
            for k,v in expected.items():
                actual=r['diagnostic'][k]
                if isinstance(v,float):DIFF.numeric(actual,v,k,angular=k in ['direction_spread','cone_max','max_angle_change'])
                else:assert actual==v,k
            diagnostics[key]=dict(scope=r['scope'],full_valid=full['valid'],split_consistent=r['split_diagnostic']['consistent'],**expected)
            if r['scope']=='target_active':
                category_by_case[r['condition']][category]+=1
                if full['valid'] and inside:
                    risk[category]['inside' if ix[key[:2]]['allowed'] else 'outside']+=1
                    cross_risk[category+('_crosses' if crossings else '_no_crossing')]['inside' if ix[key[:2]]['allowed'] else 'outside']+=1
    assert len(diagnostics)==67248
    rows=records(out/'frames.csv');groups=defaultdict(list);pools=defaultdict(list);keys=set()
    for r in rows:
        key=r['condition'],r['seed'];meta=ix[key];d=diagnostics[*key,r['frame_index']]
        start,stop=int(r['row_start']),int(r['row_stop']);full=[];present=False
        for j,e in enumerate(plan['episodes']):
            if start>=e['start']+plan['edge_samples']+meta['support_last'] and stop-1<=e['stop']-plan['edge_samples']+meta['support_first']:full.append(j)
            present|=start<e['stop']+meta['support_last'] and stop>e['start']+1+meta['support_first']
        scope='target_absent' if not present else 'target_active' if len(full)==1 else 'transition'
        assert r['scope']==d['scope']==scope and r['category']==d['category']
        assert r['episode']==(str(full[0]) if scope=='target_active' else '')
        expected_valid=d['full_valid'] if r['method']=='cap150_quorum' else d['split_consistent'] if r['method']=='split_strict_quorum' else d['category']=='stable' if r['method']=='loo_strict_quorum' else d['category'] in ['stable','unknown']
        assert (r['candidate_valid']=='True')==expected_valid
        assert (r['original_valid']=='True')==d['full_valid']
        fresh=r['fresh_valid']=='True';assert not(fresh and r['stale']=='True')
        if fresh:
            assert expected_valid
            u=np.array([float(r['estimate_'+a]) for a in 'xyz']);assert np.isclose(np.linalg.norm(u),1)
            assert np.degrees(np.arccos(np.clip(u[0],-1,1)))<=30+1e-8
            if scope=='target_active':
                az,el=np.deg2rad([meta['direction']['az'],meta['direction']['el']]);truth=np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
                assert math.isclose(float(r['error_deg']),float(np.degrees(np.arccos(np.clip(u@truth,-1,1)))),abs_tol=1e-6)
        if not fresh or scope!='target_active':assert r['error_deg']==''
        if r['stale']=='True':assert float(r['timestamp_ms'])<=float(r['display_expires_at_ms'])+1e-10
        k=(*key,r['method'],r['frame_index']);assert k not in keys;keys.add(k)
        groups[*key,r['method']].append(r);pools[r['condition'],r['method']].append(r)
    assert set(groups)=={(*key,m) for key in ix for m in p['methods']}
    assert all(len(g)==467 for g in groups.values())
    per=records(out/'per-seed.csv');pooled=s.s.read(out/'pooled.json')
    for r in per:verify_metrics(r,groups[r['condition'],r['seed'],r['method']])
    for r in pooled:
        verify_metrics(r,pools[r['condition'],r['method']])
        for cat in ['full_rejected','unknown','sensitive','stable']:assert r[cat]==category_by_case[r['condition']][cat]
    for r in records(out/'latencies.csv'):
        good=[v for v in groups[r['condition'],r['seed'],r['method']] if v['scope']=='target_active' and v['episode']==r['episode'] and v['fresh_valid']=='True' and float(v['error_deg'])<=10]
        assert (r['found']=='True')==bool(good)
        if good:assert math.isclose(float(r['latency_ms']),float(good[0]['timestamp_ms'])-plan['episodes'][int(r['episode'])]['start']/48,abs_tol=1e-10)
        else:assert r['latency_ms']==''
    rebuilt=0
    for i in inputs:
        if i['seed']==p['seeds'][0] and i['direction']['name']=='front':
            _,meta=s.source.generate(plan,i['noise'],i['direction'],i['room'],i['seed'])
            DIFF.input(i,meta)
            rebuilt+=1
    return dict(status='PASS',trials=len(inputs),method_rows=len(rows),diagnostic_frames=len(diagnostics),reconstructed_inputs=rebuilt,
        category_risk_among_full_incone={k:dict(v) for k,v in risk.items()},crossing_risk_among_full_incone={k:dict(v) for k,v in cross_risk.items()},category_by_condition={k:dict(v) for k,v in category_by_case.items()},
        auditor_sha256=s.s.entry.sha256(__file__),metric_helper_sha256=s.s.entry.sha256(s.ROOT/'audit_candidate_quality.py'),
        checks='All hashes, independent deletion angle/delay changes and category recomputation; legacy split decision linked to recorded trace, candidate veto semantics, received labels, angles, metrics, latency.8 complete input reconstructions. Not confidence calibration or complete algorithm rerun.')
