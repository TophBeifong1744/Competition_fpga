"""Independently audit persisted labels, metrics, pairing and selection/holdout lock."""
import csv,math,sys
from collections import defaultdict
import numpy as np
import study as s
sys.path.insert(0,str(s.ROOT))
from audit_candidate_quality import verify_metrics

def records(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def audit():
    s.verify();p=s.s.read(s.HERE/'protocol.json');chosen=s.s.read(s.HERE/'development/selection.json');phases={}
    for phase,expected in [('development',96),('validation',216)]:
        path=s.HERE/phase;run=s.s.read(path/'run.json');inputs=s.s.read(path/'inputs.json');plan=s.s.read(path/'plan.json')['acoustic_plan']
        assert run['trials']==expected==len(inputs)
        for n,h in run['artifacts'].items():assert s.s.entry.sha256(path/n)==h,n
        for n,h in run['source_sha256'].items():assert s.s.entry.sha256(s.HERE/n)==h,n
        assert run['protocol_sha256']==s.s.entry.sha256(s.HERE/'protocol.json')
        assert set(i['seed'] for i in inputs)==set(p[phase+'_seeds'])
        if phase=='validation':
            assert run['selection_sha256']==s.s.entry.sha256(s.HERE/'development/selection.json')
            assert run['source_sha256']==chosen['source_sha256']
        ix={(i['condition'],str(i['seed'])):i for i in inputs};assert len(ix)==expected
        expected_cases={(noise+'__'+direction['name']+'__'+room,str(seed)) for noise in p[phase+'_noises'] for direction in p['directions'] for room in p[phase+'_rooms'] for seed in p[phase+'_seeds']}
        assert set(ix)==expected_cases
        groups=defaultdict(list);pool=defaultdict(list);rowkeys=set()
        rows=records(path/'frames.csv')
        for r in rows:
            key=r['condition'],r['seed'];meta=ix[key];start,stop=int(r['row_start']),int(r['row_stop']);full=[];present=False
            assert (r['allowed']=='True')==meta['allowed']
            for idx,e in enumerate(plan['episodes']):
                if start>=e['start']+plan['edge_samples']+meta['support_last'] and stop-1<=e['stop']-plan['edge_samples']+meta['support_first']:full.append(idx)
                present|=start<e['stop']+meta['support_last'] and stop>e['start']+1+meta['support_first']
            scope='target_absent' if not present else 'target_active' if len(full)==1 else 'transition'
            assert r['scope']==scope
            assert r['episode']==(str(full[0]) if scope=='target_active' else '')
            fresh=r['fresh_valid']=='True';assert not(fresh and r['stale']=='True')
            if fresh:
                assert r['candidate_valid']=='True'
                u=np.array([float(r['estimate_'+a]) for a in 'xyz']);assert np.isclose(np.linalg.norm(u),1)
                assert np.degrees(np.arccos(np.clip(u[0],-1,1)))<=30+1e-8
                if scope=='target_active':
                    az,el=np.deg2rad([meta['direction']['az'],meta['direction']['el']]);truth=np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
                    assert math.isclose(float(r['error_deg']),float(np.degrees(np.arccos(np.clip(u@truth,-1,1)))),abs_tol=1e-6)
            if not fresh or scope!='target_active':assert r['error_deg']==''
            if r['method']=='fallback035':assert (r['guard_trigger']=='True')==(float(r['guard_score'])>=.35)
            if r['stale']=='True':assert float(r['timestamp_ms'])<=float(r['display_expires_at_ms'])+1e-10
            k=(*key,r['method'],r['frame_index']);assert k not in rowkeys;rowkeys.add(k)
            groups[*key,r['method']].append(r);pool[r['condition'],r['method']].append(r)
        def check(summary,g):
            verify_metrics(summary,g);active=[r for r in g if r['scope']=='target_active']
            values=dict(raw_active_valid=sum(r['candidate_valid']=='True' for r in active),raw_active_correct=sum(r['raw_error']!='' and float(r['raw_error'])<=10 for r in active),
                active_guard_trigger=sum(r['guard_trigger']=='True' for r in active),absent_guard_trigger=sum(r['scope']=='target_absent' and r['guard_trigger']=='True' for r in g),
                active_raw_outside=sum(r['raw_cone_angle']!='' and float(r['raw_cone_angle'])>30+1e-10 for r in active))
            for k,v in values.items():assert int(summary[k])==v,k
        per=records(path/'per-seed.csv');pooled=s.s.read(path/'pooled.json')
        for r in per:check(r,groups[r['condition'],r['seed'],r['method']])
        for r in pooled:check(r,pool[r['condition'],r['method']])
        for r in records(path/'latencies.csv'):
            g=groups[r['condition'],r['seed'],r['method']]
            good=[v for v in g if v['scope']=='target_active' and v['episode']==r['episode'] and v['fresh_valid']=='True' and float(v['error_deg'])<=10]
            assert (r['found']=='True')==bool(good)
            if good:assert math.isclose(float(r['latency_ms']),float(good[0]['timestamp_ms'])-plan['episodes'][int(r['episode'])]['start']/48,abs_tol=1e-10)
            else:assert r['latency_ms']==''
        methods=p['candidates'] if phase=='development' else [chosen['selected']]
        assert set(groups)=={(*key,m) for key in ix for m in ['phat','beta075']+methods}
        assert all(len(g)==467 for g in groups.values())
        decisions=s.s.read(path/'gates.json')
        # Gate calculation uses audited independent counts, then verifies saved decision.
        for method in methods:assert s.gates(pooled,method,p)==decisions[method]
        if phase=='development':
            eligible=[m for m in methods if decisions[m]['passed']]
            assert chosen['development_passed']==bool(eligible)
            assert chosen['selected']==max(eligible or methods,key=lambda m:decisions[m]['tonal_mean_correct'])
        rebuilt=0
        for i in inputs:
            if i['seed']==p[phase+'_seeds'][0] and i['direction']['name']=='front' and i['room']['name']=='dry':
                _,meta=s.generate(plan,i['noise'],i['direction'],i['room'],i['seed'])
                for k in ['input_sha256','target_sha256','noise_sha256','rir_sha256']:assert i[k]==meta[k]
                rebuilt+=1
        phases[phase]=dict(trials=len(inputs),method_rows=len(rows),reconstructed_inputs=rebuilt,per_seed_groups=len(per),pooled_groups=len(pooled),decisions=decisions)
    return dict(status='PASS',phases=phases,checker_sha256=s.s.entry.sha256(__file__),metric_helper_sha256=s.s.entry.sha256(s.ROOT/'audit_candidate_quality.py'),
        checks='All hashes, received labels, angles, fresh/HOLD, independent metric counts, latencies; saved gate/selection consistency and source lock; 10 complete input reconstructions. Gate formula reused from frozen runner, not a separate implementation. No retuning.')

if __name__=='__main__':
    out=s.HERE/'audit.json'
    if out.exists():raise ValueError('output exists')
    result=audit();s.s.entry.write_json(out,result);print(result)
