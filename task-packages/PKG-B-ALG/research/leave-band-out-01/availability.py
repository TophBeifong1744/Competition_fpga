"""Post-result descriptive check: stable deletion may leave no changed retained bins."""
import gzip,json
from collections import Counter,defaultdict
import numpy as np
import run_study as s

def run():
    counts=defaultdict(Counter)
    with gzip.open(s.HERE/'evidence/features.jsonl.gz','rt',encoding='utf-8') as file:
        for line in file:
            r=json.loads(line)
            if r['scope']!='target_active' or r['diagnostic']['category']!='stable':continue
            noise=r['condition'].split('__')[0];c=counts[noise];c['stable_frames']+=1
            indices=r['diagnostic']['comparable_indices'];c['comparable_'+str(len(indices))]+=1
            # Every retained full bin occurs in exactly two complements; tested separately.
            retained=np.array([v['retained_bins'] for v in r['deleted']]);full=retained.sum(axis=0)/2
            assert np.equal(full,np.floor(full)).all()
            no_change=sum(np.array_equal(full,retained[k]) for k in indices)
            c['zero_removed_bin_comparisons']+=no_change
            c['frames_all_comparisons_remove_zero_bins']+=no_change==len(indices)
    return dict(scope='Post-result descriptive analysis; no rule change or independent validation',counts={k:dict(v) for k,v in counts.items()},source_sha256=s.s.entry.sha256(__file__))

if __name__=='__main__':
    out=s.HERE/'availability.json'
    if out.exists():raise ValueError('output exists')
    r=run();s.s.entry.write_json(out,r);print(r)
