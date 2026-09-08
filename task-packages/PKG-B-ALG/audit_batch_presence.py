"""Independent persisted-result audit: interval labels, denominators, hashes and replay."""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def csvrows(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def check(run,repeat=None):
    metadata=read(run/'run.json');plan=read(run/'frozen-plan.json')
    assert metadata['status']=='COMPLETE_SYNTHETIC_BATCH'
    for name,h in metadata['artifact_sha256'].items():assert sha(run/name)==h,name
    for name,h in metadata['source_sha256'].items():assert sha(ROOT/'payload/model/python'/name)==h,name
    expected_frames=1+(plan['duration_samples']-1024)//512
    annotations={}
    for scenario in plan['scenarios']:
        items=read(run/'annotations'/f'{scenario}.json')
        assert len(items)==expected_frames
        for i,item in enumerate(items):
            start,stop=i*512,i*512+1024
            assert (item['row_start'],item['row_stop'])==(start,stop)
            assert item['first_sample_id']==start+plan['margin_samples']
            assert item['last_sample_id']==stop-1+plan['margin_samples']
            full=[];emitting=0;unity=0
            if scenario!='interferer_only':
                for k,e in enumerate(plan['episodes']):
                    if start>=e['start']+plan['edge_samples'] and stop-1<=e['stop']-plan['edge_samples']:full.append(k)
                    emitting+=max(0,min(stop,e['stop'])-max(start,e['start']+1))
                    unity+=max(0,min(stop,e['stop']-plan['edge_samples']+1)-max(start,e['start']+plan['edge_samples']))
            expected='target_absent' if emitting==0 else 'target_active' if len(full)==1 else 'transition'
            assert item['scope']==expected,(scenario,i)
            assert item['active_sample_count']==emitting and item['full_amplitude_sample_count']==unity
            assert item['episode']==(full[0] if expected=='target_active' else None)
            if expected!='target_active':assert item['target_unit_vector'] is None
            annotations[scenario,i]=item
    rows=csvrows(run/'frames.csv');groups=defaultdict(list);pooled_groups=defaultdict(list)
    for r in rows:
        a=annotations[r['scenario'],int(r['frame_index'])]
        assert r['scope']==a['scope']
        assert r['episode']==('' if a['episode'] is None else str(a['episode']))
        assert int(r['row_start'])==a['row_start'] and int(r['row_stop'])==a['row_stop']
        assert math.isclose(float(r['timestamp_ms']),a['row_stop']/48,abs_tol=1e-10)
        fresh=r['fresh_valid']=='True';stale=r['stale']=='True'
        assert not (fresh and stale)
        assert stale==(r['state']=='HOLD')
        if stale:assert float(r['timestamp_ms'])<=float(r['display_expires_at_ms'])+1e-10
        if fresh:
            estimate=np.array([float(r['estimate_'+axis]) for axis in 'xyz'])
            assert np.isclose(np.linalg.norm(estimate),1,atol=1e-10)
        else:assert all(r['estimate_'+axis]=='' for axis in 'xyz')
        if fresh and a['scope']=='target_active':
            e=plan['episodes'][a['episode']];az,el=np.deg2rad([e['azimuth_deg'],e['elevation_deg']])
            truth=np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
            error=float(np.degrees(np.arccos(np.clip(truth@estimate,-1,1))))
            assert math.isclose(error,float(r['error_deg']),abs_tol=1e-6)
        else:assert r['error_deg']==''
        groups[r['scenario'],r['seed'],r['method']].append(r)
        pooled_groups[r['scenario'],r['method']].append(r)
    def verify(summary,group):
        active=[r for r in group if r['scope']=='target_active'];absent=[r for r in group if r['scope']=='target_absent']
        errors=[float(r['error_deg']) for r in active if r['fresh_valid']=='True']
        wrong=sum(e>30 for e in errors);false=sum(r['fresh_valid']=='True' for r in absent)
        expected=dict(all_frames=len(group),active_frames=len(active),active_fresh_frames=len(errors),
            active_fresh_rate=len(errors)/len(active) if active else None,
            p50_error_deg=float(np.percentile(errors,50)) if errors else None,
            p95_error_deg=float(np.percentile(errors,95)) if errors else None,
            active_wrong_over30=wrong,active_wrong_rate_all=wrong/len(active) if active else None,
            active_wrong_rate_fresh=wrong/len(errors) if errors else None,
            active_correct_within10_rate=sum(e<=10 for e in errors)/len(active) if active else None,
            absent_frames=len(absent),absent_fresh_false_outputs=false,
            absent_false_output_rate=false/len(absent) if absent else None,
            absent_hold_display_frames=sum(r['stale']=='True' for r in absent),
            transition_frames=sum(r['scope']=='transition' for r in group),
            transition_fresh_outputs=sum(r['scope']=='transition' and r['fresh_valid']=='True' for r in group),
            hold_frames=sum(r['stale']=='True' for r in group))
        for key,value in expected.items():
            if value is None:assert summary[key] in (None,''),key
            else:assert math.isclose(float(summary[key]),value,abs_tol=1e-12,rel_tol=1e-12),key
    per_seed=csvrows(run/'per-seed.csv')
    for item in per_seed:
        group=groups[item['scenario'],item['seed'],item['method']]
        assert len(group)==expected_frames
        verify(item,group)
    for item in read(run/'pooled.json'):verify(item,pooled_groups[item['scenario'],item['method']])
    index={(r['scenario'],r['seed'],r['method']):r for r in per_seed}
    for r in csvrows(run/'paired-differences.csv'):
        comparator=r['comparison'].removeprefix('tracker-minus-')
        a=index[r['scenario'],r['seed'],'tracker'][r['metric']]
        b=index[r['scenario'],r['seed'],comparator][r['metric']]
        if not a or not b:assert r['delta']==''
        else:assert math.isclose(float(r['delta']),float(a)-float(b),abs_tol=1e-12)
    for r in csvrows(run/'seed-distribution.csv'):
        values=[float(s[r['metric']]) for s in per_seed if s['scenario']==r['scenario'] and s['method']==r['method'] and s[r['metric']]!='']
        assert int(r['defined_seeds'])==len(values)
        for key,value in [('median',float(np.median(values)) if values else None),('minimum',min(values) if values else None),('maximum',max(values) if values else None)]:
            if value is None:assert r[key]==''
            else:assert math.isclose(float(r[key]),value,abs_tol=1e-12)
    latency_rows=csvrows(run/'latencies.csv')
    for r in latency_rows:
        eligible=[g for g in groups[r['scenario'],r['seed'],r['method']]
                  if g['scope']=='target_active' and g['episode']==r['episode']]
        correct=[g for g in eligible if g['fresh_valid']=='True' and float(g['error_deg'])<=10]
        assert (r['applicable']=='True')==bool(eligible)
        assert (r['found']=='True')==bool(correct)
        onset=plan['episodes'][int(r['episode'])]['start']/48
        assert float(r['onset_ms'])==onset
        if correct:
            ready=float(correct[0]['timestamp_ms'])
            assert float(r['first_correct_ready_ms'])==ready
            assert math.isclose(float(r['onset_to_first_correct_ms']),ready-onset,abs_tol=1e-12)
        else:assert r['first_correct_ready_ms']==r['onset_to_first_correct_ms']==''
    assert len(rows)==len(plan['scenarios'])*len(plan['seeds'])*expected_frames*3
    replay_files=0
    if repeat:
        files=metadata['artifact_sha256']|{'run.json':sha(run/'run.json')}
        for name,h in files.items():assert sha(repeat/name)==h,name
        replay_files=len(files)
    return dict(status='PASS',frames_rows_checked=len(rows),annotation_windows_checked=len(annotations),
        per_seed_groups_checked=len(per_seed),pooled_groups_checked=len(pooled_groups),
        latency_rows_checked=len(latency_rows),
        replay_files_identical=replay_files,run_sha256=sha(run/'run.json'),auditor_sha256=sha(Path(__file__)),
        checks='Independent integer-interval annotation, angles, all summary denominators, paired differences, seed ranges, stale exclusion, artifact/source hashes.')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--repeat',type=Path);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    if args.out.exists():parser.error('output must be new')
    result=check(args.run,args.repeat)
    args.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result));return 0


if __name__=='__main__':raise SystemExit(main())
