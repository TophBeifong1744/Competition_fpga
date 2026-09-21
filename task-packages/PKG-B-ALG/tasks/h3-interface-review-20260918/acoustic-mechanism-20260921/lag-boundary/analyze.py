import argparse,collections,hashlib,json,pathlib

def aggregate(rows):
    return dict(frames=len(rows),frames_tau_bound=sum(r['bound'] for r in rows),pair_tau_bound=sum(r['bound_pairs'] for r in rows),cycle_analyzable=sum(r['cycle'] is not None for r in rows),cycle_fail=sum(r['cycle'] is not None and r['cycle']>.5 for r in rows),cycle_fail_with_bound=sum(r['cycle'] is not None and r['cycle']>.5 and r['bound'] for r in rows),cycle_fail_without_bound=sum(r['cycle'] is not None and r['cycle']>.5 and not r['bound'] for r in rows),valid_pair_histogram=dict(sorted(collections.Counter(r['valid_pairs'] for r in rows).items())))

def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
    root=a.repo/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918'; seal=json.loads((root/'checkpoint-20260923/SNAPSHOT-SHA256.json').read_text(encoding='utf-8'))['files'];pins={}
    def read(rel):
        f=root/rel;h=hashlib.sha256(f.read_bytes()).hexdigest()
        if h!=seal[rel]:raise ValueError('HASH_MISMATCH '+rel)
        pins[rel]=h;return json.loads(f.read_text(encoding='utf-8'))
    freq=read('acoustic-mechanism-20260921/frequency-diagnostic/run01/frames.json');lookup={(r['capture'],r['start']):r['variants']['full'] for r in freq}
    rows=[]
    for f in sorted((root/'checkpoint-20260923/evidence/run01').glob('*-frames.json')):
        name=f.name[:-12]
        for r in read(f.relative_to(root).as_posix()):
            reasons=r['pair_reasons'];v=lookup.get((name,r['start']))
            if v is not None:assert v['pair_reasons']==reasons
            rows.append(dict(capture=name,start=r['start'],background='_bg_' in name,marker=r['marker_excluded'],gate=r['candidates']['band_calibrated_duration'],bound='TAU_BOUND' in reasons,bound_pairs=reasons.count('TAU_BOUND'),valid_pairs=reasons.count('VALID'),cycle=None if v is None else v['cycle'],cycle_cache_present=v is not None))
    assert len(rows)==4488 and sum(r['cycle_cache_present'] for r in rows)==1442
    groups={'all':rows,'background':[r for r in rows if r['background']],'target_nonmarker':[r for r in rows if not r['background'] and not r['marker']],'target_marker':[r for r in rows if not r['background'] and r['marker']],'target_nonmarker_gate':[r for r in rows if not r['background'] and not r['marker'] and r['gate']],'selected_nonmarker':[r for r in rows if not r['background'] and not r['marker'] and r['cycle_cache_present']]}
    edges=[]
    for r in read('closeout-0918-20260921/acoustic/pairs01/frames.json'):
        pairs=[p for p in r['pairs'] if 'edge_peak' in p];edges.append(dict(capture=r['capture'],start=r['start'],marker=r['marker_excluded'],scored_pairs=len(pairs),edge_pairs=sum(p['edge_peak'] for p in pairs),edge_bound_pairs=sum(p['edge_peak'] and p['reason']=='TAU_BOUND' for p in pairs),bound_pairs=sum(p['reason']=='TAU_BOUND' for p in pairs)))
    edge_groups={}
    for name,rs in [('selected_target',edges),('selected_nonmarker',[r for r in edges if not r['marker']])]:
        edge_groups[name]={'frames':len(rs),**{k:sum(r[k] for r in rs) for k in ('scored_pairs','edge_pairs','edge_bound_pairs','bound_pairs')},'frames_edge':sum(r['edge_pairs']>0 for r in rs)}
    result=dict(status='AUTHOR_DIAGNOSTIC_NOT_ACCEPTANCE',pins=pins,counts={k:aggregate(v) for k,v in groups.items()},edge_counts=edge_groups,fft_calls=0,ifft_calls=0,limitations='Cycle cache covers 1122 background plus biased 320 selected target frames only; edge cache covers those 320 target frames only. None means unavailable or unfit, never zero residual. No threshold changes.')
    a.out.mkdir(parents=True,exist_ok=False)
    for name,value in [('result',result),('frames',rows),('edges',edges)]: (a.out/(name+'.json')).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'counts':result['counts'],'edge_counts':edge_groups},indent=2))
if __name__=='__main__':main()
