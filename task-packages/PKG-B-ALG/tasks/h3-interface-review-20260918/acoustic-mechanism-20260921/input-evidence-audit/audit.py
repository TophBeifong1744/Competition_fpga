"""Audit pinned metadata without changing or decoding frozen recordings."""
import argparse, hashlib, json, pathlib, platform

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',type=pathlib.Path,required=True); ap.add_argument('--output',type=pathlib.Path,required=True); a=ap.parse_args()
    root=a.repo.resolve(); pkg=root/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918'
    source=pkg/'checkpoint-20260923/evidence/run01/summary.json'
    s=json.loads(source.read_text(encoding='utf-8')); records=[]; checked={}
    for rel,expected in s['pins'].items():
        actual=sha(root/rel)
        if actual!=expected: raise ValueError(f'INPUT_HASH_MISMATCH {rel}: expected={expected} actual={actual}')
        checked[rel]=actual
        if rel.endswith('/metadata.json'):
            m=json.loads((root/rel).read_text(encoding='utf-8'))
            records.append({'path':rel,'sha256':actual,'fields':{k:v for k,v in m.items() if any(t in k.lower() for t in ('geometry','calibrat','channel','sample','source_placement','adapter','provisional'))}})
    if len(records)!=8: raise ValueError(f'Expected eight metadata records, got {len(records)}')
    docs=['task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/c-adapter-first-20260913/GEOMETRY.md','task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/trusted-direction-input-20260918/HANDOFF-20260920.md','docs/acoustic-validation-plan.md']
    result={'status':'AUTHOR_EVIDENCE_AUDIT_NOT_ACCEPTANCE','python':platform.python_version(),'source_summary_sha256':sha(source),'input_commit':s['config']['input_commit'],'checked_pin_count':len(checked),'pins':checked,'document_hashes':{p:sha(root/p) for p in docs},'records':records}
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'PASS: {len(checked)} pinned files; {len(records)} metadata; no FFT, no waveform rewrite')
if __name__=='__main__': main()
