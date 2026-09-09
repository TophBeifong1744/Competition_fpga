"""Post-result descriptive loss analysis; does not change the frozen screening."""
import gzip,json
from collections import defaultdict,Counter
import run_study as s

def run():
    counts=defaultdict(Counter);reject=defaultdict(Counter)
    with gzip.open(s.HERE/'evidence/features.jsonl.gz','rt',encoding='utf-8') as file:
        for line in file:
            r=json.loads(line)
            if r['scope']!='target_active':continue
            noise=r['condition'].split('__')[0];counts[noise]['frames']+=1
            counts[noise][r['diagnostic']['category']]+=1;counts[noise]['valid_bands_'+str(r['diagnostic']['valid_subbands'])]+=1
            for j,b in enumerate(r['subbands']):
                row=reject[noise+':band'+str(j)];row['frames']+=1;row['valid']+=b['valid'];row['pairs_under12']+=sum(x<12 for x in b['retained_bins'])
                row.update(b['rejection_reasons'])
    p=s.s.read(s.HERE/'protocol.json');plan=s.s.read(s.ROOT/'payload/config/robustness-sweep.json')|dict(noise_nominal_rms=0.)
    controls=[]
    # Explicitly post-result clean sanity controls, not another validation or tuning set.
    for direction in p['directions']:
        for room in plan['rooms']:
            if room['name'] not in p['rooms']:continue
            segment,meta=s.source.generate(plan,'band',direction,room,p['seeds'][0]);c=Counter()
            for frame in s.iter_frames(segment):
                label=s.s.labels(plan,frame.row_start,frame.row_stop,meta,direction)
                if label['scope']!='target_active':continue
                full=s.guard.localize(frame,'cap150');subs=s.f.subband_candidates(frame,p['subbands_hz']);d=s.f.assess(full,subs,p['consistency'])
                c['frames']+=1;c['full_valid']+=full['valid'];c['valid_bands_'+str(d['valid_subbands'])]+=1;c[d['category']]+=1
            controls.append(dict(direction=direction,room=room,seed=p['seeds'][0],input_sha256=meta['input_sha256'],noise_sha256=meta['noise_sha256'],counts=dict(c)))
    return dict(status='DESCRIPTIVE_POST_RESULT_CONTROL',counts={k:dict(v) for k,v in counts.items()},subband_rejections={k:dict(v) for k,v in reject.items()},
        clean_controls=controls,source_sha256=s.s.entry.sha256(__file__),scope='12 zero-background sanity controls with same signal/RIR and first study seed after outcomes. No threshold change, no gating rerun or independent generalization claim.')

if __name__=='__main__':
    path=s.HERE/'loss-diagnosis.json'
    if path.exists():raise ValueError('output exists')
    result=run();s.s.entry.write_json(path,result);print(result['clean_controls'])
