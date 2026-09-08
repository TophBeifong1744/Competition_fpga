"""Independent persisted candidate-quality audit and diagnostic summaries."""
import argparse
from collections import defaultdict,Counter
import math
from pathlib import Path
import numpy as np
from audit_capture_research import read,sha,records,ROOT


def verify_metrics(s,rows):
    active=[r for r in rows if r['scope']=='target_active'];absent=[r for r in rows if r['scope']=='target_absent']
    errors=[float(r['error_deg']) for r in active if r['fresh_valid']=='True']
    wrong=sum(e>30 for e in errors);false=sum(r['fresh_valid']=='True' for r in absent)
    expected=dict(all_frames=len(rows),active_frames=len(active),active_fresh_frames=len(errors),
        active_fresh_rate=len(errors)/len(active) if active else None,
        active_correct_within10_rate=sum(e<=10 for e in errors)/len(active) if active else None,
        active_wrong_over30=wrong,active_wrong_rate_all=wrong/len(active) if active else None,
        active_wrong_rate_fresh=wrong/len(errors) if errors else None,
        p50_error_deg=float(np.percentile(errors,50)) if errors else None,
        p95_error_deg=float(np.percentile(errors,95)) if errors else None,
        absent_frames=len(absent),absent_fresh_false_outputs=false,absent_false_output_rate=false/len(absent) if absent else None,
        absent_hold_display_frames=sum(r['stale']=='True' for r in absent),
        transition_frames=sum(r['scope']=='transition' for r in rows),
        transition_fresh_outputs=sum(r['scope']=='transition' and r['fresh_valid']=='True' for r in rows),
        hold_frames=sum(r['stale']=='True' for r in rows))
    for key,value in expected.items():
        if value is None:assert s[key] in ('',None),key
        else:assert math.isclose(float(s[key]),value,abs_tol=1e-12,rel_tol=1e-12),key


def audit():
    protocol=read(ROOT/'payload/config/candidate-quality-protocol.json')
    old=read(ROOT/'payload/config/capture-research-protocol.json')
    dev,test=set(protocol['development_seeds']),set(protocol['validation_seeds'])
    assert not dev&test and not(dev|test)&set(old['development_seeds']+old['validation_seeds'])
    count=0
    for manifest in ['reference/batch-presence-fixed/frozen-files.json','reference/candidate-quality-fixed/files.json']:
        files=read(ROOT/manifest)['files']
        for name,h in files.items():assert sha(ROOT/name)==h,name
        count+=len(files)
    selection_path=ROOT/'evidence/candidate-development-01/selection.json';selection=read(selection_path)
    assert selection['selected']==protocol['candidates'][0]
    phases={};diagnostics=[];seed_gains=[]
    for phase,name,seeds in [('develop','candidate-development-01',dev),('validate','candidate-heldout-01',test)]:
        path=ROOT/'evidence'/name;run=read(path/'run.json');plan=read(path/'plan.json')
        assert set(run['seeds'])==set(plan['seeds'])==seeds
        assert run['source_sha256']==selection['source_sha256']
        assert run['protocol_sha256']==selection['protocol_sha256']==sha(ROOT/'payload/config/candidate-quality-protocol.json')
        if phase=='validate':assert run['selection_sha256']==sha(selection_path)
        for name,h in run['source_sha256'].items():assert sha(ROOT/'payload/model/python'/name)==h,name
        for name,h in run['artifact_sha256'].items():assert sha(path/name)==h,name
        rows=records(path/'frames.csv');groups=defaultdict(list);pool=defaultdict(list);row_index={}
        for r in rows:
            start,stop=int(r['row_start']),int(r['row_stop']);full=[];present=False
            if r['scenario']!='interferer_only':
                for i,e in enumerate(plan['episodes']):
                    if start>=e['start']+plan['edge_samples'] and stop-1<=e['stop']-plan['edge_samples']:full.append(i)
                    present|=max(start,e['start']+1)<min(stop,e['stop'])
            scope='target_absent' if not present else 'target_active' if len(full)==1 else 'transition'
            assert scope==r['scope']
            fresh=r['fresh_valid']=='True';stale=r['stale']=='True'
            assert not(fresh and stale)
            if fresh:
                assert r['candidate_valid']=='True'
                assert int(r['finite_pairs'])>=5 and .7<=float(r['raw_vector_norm'])<=1.3 and float(r['residual_samples'])<=.5
                u=np.array([float(r['estimate_'+a]) for a in 'xyz'])
                assert np.isclose(np.linalg.norm(u),1,atol=1e-10)
                if r['method'].endswith('_quorum'):assert np.degrees(np.arccos(np.clip(u[0],-1,1)))<=30+1e-8
                if scope=='target_active':
                    e=plan['episodes'][full[0]];a,v=np.deg2rad([e['azimuth_deg'],e['elevation_deg']])
                    truth=np.array([np.cos(v)*np.cos(a),np.cos(v)*np.sin(a),np.sin(v)])
                    error=np.degrees(np.arccos(np.clip(truth@u,-1,1)))
                    assert math.isclose(float(r['error_deg']),error,abs_tol=1e-6)
            if not fresh or scope!='target_active':assert r['error_deg']==''
            if stale:assert float(r['timestamp_ms'])<=float(r['display_expires_at_ms'])+1e-10
            groups[r['scenario'],r['seed'],r['method']].append(r);pool[r['scenario'],r['method']].append(r)
            row_index[r['scenario'],r['seed'],r['frame_index'],r['method']]=r
        per=records(path/'per-seed.csv');pooled=read(path/'pooled.json')
        for s in per:verify_metrics(s,groups[s['scenario'],s['seed'],s['method']])
        for s in pooled:verify_metrics(s,pool[s['scenario'],s['method']])
        index={(r['scenario'],r['seed'],r['method']):r for r in per}
        for r in records(path/'paired.csv'):
            suffix='_quorum' if r['method'].endswith('_quorum') else '_raw'
            a=index[r['scenario'],r['seed'],r['method']][r['metric']];b=index[r['scenario'],r['seed'],'original'+suffix][r['metric']]
            if a=='' or b=='':assert r['delta']==''
            else:assert math.isclose(float(r['delta']),float(a)-float(b),abs_tol=1e-12)
        for r in records(path/'latencies.csv'):
            eligible=[v for v in groups[r['scenario'],r['seed'],r['method']] if v['scope']=='target_active' and v['episode']==r['episode']]
            good=[v for v in eligible if v['fresh_valid']=='True' and float(v['error_deg'])<=10]
            assert (r['found']=='True')==bool(good) and (r['applicable']=='True')==bool(eligible)
            if good:assert math.isclose(float(r['onset_to_first_correct_ms']),float(good[0]['timestamp_ms'])-float(r['onset_ms']),abs_tol=1e-12)
            else:assert r['onset_to_first_correct_ms']==''
        diag=records(path/'candidate-diagnostics.csv');diagnostic_groups=defaultdict(list)
        for d in diag:
            corresponding=row_index[d['scenario'],d['seed'],d['frame_index'],d['method']+'_raw']
            assert d['valid']==corresponding['fresh_valid'] and d['scope']==corresponding['scope']
            for k in ['residual_samples','finite_pairs','raw_vector_norm']:assert d[k]==corresponding[k]
            if d['scope']=='target_active':diagnostic_groups[d['scenario'],d['method']].append(d)
        for (scenario,method),group in diagnostic_groups.items():
            rms=[float(d['pair_error_rms_samples']) for d in group if d['pair_error_rms_samples']!='']
            diagnostics.append(dict(phase=phase,scenario=scenario,method=method,active_frames=len(group),
                rejected=sum(d['valid']=='False' for d in group),
                rejection_reasons=dict(Counter(reason for d in group for reason in d['rejection_reasons'].split('|') if reason)),
                pair_rms_defined_frames=len(rms),pair_rms_p50=float(np.percentile(rms,50)) if rms else None,
                pair_rms_p95=float(np.percentile(rms,95)) if rms else None,
                rescued_from_old_rejection=sum(d['old_valid']=='False' and d['valid']=='True' for d in group),
                lost_old_valid=sum(d['old_valid']=='True' and d['valid']=='False' for d in group)))
        if phase=='validate':
            for seed in sorted(seeds):
                orig=index['band_noise0',str(seed),'original_quorum'];new=index['band_noise0',str(seed),'gcc_beta075_quorum']
                seed_gains.append(dict(seed=seed,new_fresh_rate=float(new['active_fresh_rate']),
                    correct_gain=float(new['active_correct_within10_rate'])-float(orig['active_correct_within10_rate'])))
        phases[phase]=dict(method_rows=len(rows),diagnostic_rows=len(diag),per_seed_groups=len(per),pooled_groups=len(pooled))
    return dict(status='PASS',reference_hash_entries_checked=count,seed_splits_disjoint=True,frozen_selected_code_matches=True,
        phases=phases,heldout_noise_seed_gains=seed_gains,diagnostic_summaries=diagnostics,
        auditor_sha256=sha(Path(__file__)),helper_sha256=sha(ROOT/'audit_capture_research.py'),selection_sha256=sha(selection_path),
        checks='All result rows: labels, angles, unchanged acceptance limits, HOLD exclusion, summaries, paired gains and latencies. Diagnostics linked to raw output. No algorithm rerun/tuning.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    if args.out.exists():p.error('output must be new')
    result=audit();import json
    args.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['diagnostic_summaries','heldout_noise_seed_gains']}))
