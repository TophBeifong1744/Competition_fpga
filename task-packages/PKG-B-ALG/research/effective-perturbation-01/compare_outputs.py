"""Verify output equivalence separately from revised confidence labels."""
import csv
import run_study as s

def run():
    ix={};differences=[];pairs=0
    fields=['fresh_valid','state','reason','stale','error_deg','estimate_x','estimate_y','estimate_z','candidate_valid','display_expires_at_ms']
    with (s.HERE/'evidence/frames.csv').open(encoding='utf-8',newline='') as file:
        for r in csv.DictReader(file):
            key=r['condition'],r['seed'],r['frame_index']
            if r['method']=='old_loo_known_only':ix[key]=r
            elif r['method']=='effective_known_only':
                old=ix.pop(key);changed=[k for k in fields if old[k]!=r[k]];pairs+=1
                if changed:differences.append(dict(condition=key[0],seed=key[1],frame=key[2],changed=changed))
    assert not ix and pairs==67248
    return dict(compared_frame_pairs=pairs,different_pairs=len(differences),differences=differences,fields=fields,source_sha256=s.s.entry.sha256(__file__))

if __name__=='__main__':
    path=s.HERE/'output-equivalence.json'
    if path.exists():raise ValueError('output exists')
    r=run();s.s.entry.write_json(path,r);print(r)
