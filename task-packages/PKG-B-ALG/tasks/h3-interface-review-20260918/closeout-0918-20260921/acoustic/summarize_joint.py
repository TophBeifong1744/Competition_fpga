"""Reproduce paired validity and floor-effect analysis without rerunning FFT."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def execute(repo,study,out):
    out.mkdir(parents=True,exist_ok=False)
    cp=repo/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923'
    seal=load(cp/'SNAPSHOT-SHA256.json')['files'];manifest=load(study/'OUTPUT-SHA256.json')
    for name,want in manifest.items():assert sha(study/name)==want,name
    counts=Counter();boundary=Counter();frames=0
    for f in sorted(study.glob('*-frames.json')):
        original=cp/'evidence/run01'/f.name
        assert sha(original)==seal[original.relative_to(cp.parent).as_posix()]
        for a,b in zip(load(original),load(f),strict=True):
            assert (a['start'],a['stop'])==(b['start'],b['stop'])
            old=a['projection'].get('advisory_consistent',False);new=b['candidate']['valid']
            counts[f'old_{old}_new_{new}']+=1;frames+=1
            if a['candidates']['band_calibrated_duration']:counts[f'gated_old_{old}_new_{new}']+=1
            if not old and new:
                boundary['old_norm_below_0.1']+=a['projection'].get('projection_norm',100)<.1
                boundary['old_norm_above_1.3']+=a['projection'].get('projection_norm',0)>1.3
                boundary['new_radius_at_floor']+=abs(b['candidate']['radius']-.1)<1e-12
    assert frames==4488
    # Validate the post-run exploratory files, not silently regenerate different values.
    assert dict(counts)==load(study/'paired-validity.json')
    assert dict(boundary)==load(study/'gained-boundary-analysis.json')
    result=dict(status='PAIRED_ANALYSIS_REPRODUCED',frames=frames,paired=dict(counts),boundary=dict(boundary),
                meaning='validity is candidate acceptance, not physical correctness',
                study_result_sha256=sha(study/'result.json'),script_sha256=sha(Path(__file__)))
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('PAIRED_ANALYSIS_PASS',frames,dict(boundary))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--study',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();execute(a.repo,a.study,a.out)
