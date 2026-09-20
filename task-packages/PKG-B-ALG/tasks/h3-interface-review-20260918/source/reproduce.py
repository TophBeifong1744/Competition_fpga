"""Incremental handoff checks, preserving all frozen inputs and old evidence."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from datetime import datetime, timezone
import numpy as np
from framing_review import PACKAGE, REPO, generate, compare

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify_inputs():
    rows=json.loads((PACKAGE/'references.json').read_text(encoding='utf-8'))['files']
    for r in rows:
        if sha(REPO/r['local_path'])!=r['sha256']:
            raise ValueError('Pinned dependency changed: '+r['local_path'])
    return len(rows)

def verify_package():
    manifest=PACKAGE/'PACKAGE-SHA256.json'
    expected=json.loads(manifest.read_text())['files']
    actual={p.relative_to(PACKAGE).as_posix():sha(p) for p in PACKAGE.rglob('*')
            if p.is_file() and p!=manifest}
    if actual!=expected:raise ValueError('Package changed/missing/extra')
    return len(actual)

def negative_checks(out):
    records=[]
    for field in ['row_start','first_sample_id','slot_sequence','pcm_array','budget']:
        with tempfile.TemporaryDirectory(prefix='negative-',dir=out) as temp:
            temp=Path(temp)
            for name in ['framing.json','synthetic-frames.npz','budget.json']:
                shutil.copyfile(PACKAGE/'golden'/name,temp/name)
            if field in ['row_start','first_sample_id','slot_sequence']:
                p=temp/'framing.json';v=json.loads(p.read_text())
                f=v['cases'][1]['frames'][0]
                if field=='row_start':f[field]+=1
                elif field=='first_sample_id':f[field]=str(int(f[field])+1)
                else:f[field][0]^=1
                p.write_text(json.dumps(v))
            elif field=='pcm_array':
                p=temp/'synthetic-frames.npz'
                with np.load(p,allow_pickle=False) as z:data={k:z[k].copy() for k in z.files}
                data[sorted(data)[0]][0,0]+=1
                np.savez_compressed(p,**data)
            else:
                p=temp/'budget.json';v=json.loads(p.read_text())
                v['transforms']['service_cycles_sum']+=1;p.write_text(json.dumps(v))
            try:compare(PACKAGE/'golden',temp)
            except ValueError as exc:records.append({'mutation':field,'result':'REJECTED','reason':str(exc)})
            else:raise AssertionError('Mutation incorrectly accepted: '+field)
    return records

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    out=a.out.resolve()
    if out==PACKAGE or PACKAGE in out.parents:raise ValueError('Output must be outside frozen package')
    out.mkdir(parents=True,exist_ok=False)
    report={'status':'INCOMPLETE','utc':datetime.now(timezone.utc).isoformat(),
            'python':sys.version,'numpy':np.__version__,'argv':sys.argv,'cwd':str(Path.cwd())}
    try:
        report['package_files']=verify_package()
        report['pinned_input_files']=verify_inputs()
        result=generate(out/'generated')
        compare(PACKAGE/'golden',out/'generated')
        report['golden_cases']=len(result['cases'])
        report['invalid_input_rejections']=result['rejections']
        report['golden_mutations']=negative_checks(out)
        report['s1_frames']=len(result['cases'][-1]['frames'])
        report['s1_unused_tail']=result['cases'][-1]['summary']['unused_clean_rows']
        report['inputs_post']=verify_inputs()
        report['package_post']=verify_package()
        report['status']='PASS_AUTHOR_HANDOFF_INCREMENT_NOT_A_APPROVAL'
    except Exception as exc:
        report['status']='FAIL';report['error']=repr(exc)
    (out/'result.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
    return int(report['status']=='FAIL')

if __name__=='__main__':raise SystemExit(main())
