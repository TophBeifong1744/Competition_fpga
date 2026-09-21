"""Portable consolidation check: provenance/unchanged evidence, arithmetic and focused tests."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback

HERE=Path(__file__).resolve().parent
PACKAGE=HERE.parent
REPO=HERE.parents[4]
BASE='fe67547635ff254f9f91c7f917e8dedb6daf3363'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def execute(out,git_repo):
    original=load(HERE/'SNAPSHOT-before-consolidation.json')['files']
    for name,want in original.items():assert sha(PACKAGE/name)==want,name
    current=PACKAGE/'checkpoint-20260923/SNAPSHOT-SHA256.json'
    actual={p.relative_to(PACKAGE).as_posix():sha(p) for p in PACKAGE.rglob('*') if p.is_file() and p!=current}
    assert actual==load(current)['files'],'current package file set/hash mismatch'
    copied={}
    for folder,seal in [('acoustic','WORK-JOINT-SHA256.json'),('fixed','WORK-SHA256.json')]:
        manifest=load(HERE/folder/seal);files=manifest.get('files',manifest)
        for name,want in files.items():assert sha(HERE/folder/name)==want,(folder,name)
        copied[folder]=len(files)
    identities=load(HERE/'fixed/checks-02/source-identities.json')
    for name,entry in identities.items():
        raw=subprocess.check_output(['git','-C',str(git_repo),'cat-file','blob',BASE+':'+name])
        assert hashlib.sha256(raw).hexdigest()==entry['blob_sha256'],name
    budget=load(HERE/'fixed/checks-02/budget.json')
    assert budget['historical_slot_sum_cycles']==8*7366+6*7406==103364
    assert budget['listed_bytes']==sum(budget['buffers_bytes'].values())==107496
    assert budget['hop_cycles_100mhz']==100000000*512//48000==1066666
    for name in ['total_wcet_cycles','actual_resources','actual_memory_bytes','end_to_end_latency_cycles','stall_upper_bound_cycles']:
        assert budget[name] is None,name
    commands=[]
    jobs=[('joint-tests',[sys.executable,'-B','-m','unittest','discover','-s',str(HERE/'acoustic'),'-p','test_joint.py','-v']),
          ('paired-analysis',[sys.executable,'-B',str(HERE/'acoustic/summarize_joint.py'),'--repo',str(REPO),'--study',str(HERE/'acoustic/joint01'),'--out',str(out/'paired')])]
    for name,cmd in jobs:
        p=subprocess.run(cmd,capture_output=True)
        (out/(name+'-stdout.txt')).write_bytes(p.stdout);(out/(name+'-stderr.txt')).write_bytes(p.stderr)
        commands.append(dict(name=name,argv=cmd,exit_code=p.returncode));dump(out/'commands.json',commands)
        if p.returncode:raise RuntimeError(name+' failed; see retained logs')
    result=dict(status='CONSOLIDATION_CHECK_PASS_NOT_INDEPENDENT_APPROVAL',original_files_unchanged=len(original),
                current_files=len(actual),copied_sealed_files=copied,git_source_identities=len(identities),
                focused_tests=4,paired_frames=4488,budget=budget,
                no_fft_or_audio_regeneration=True,no_new_fixed_point_boundary_tests=True,full_h3_approved=False)
    dump(out/'result.json',result);print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--git-repo',type=Path,default=REPO)
    a=p.parse_args();out=a.out.resolve()
    if out==REPO or REPO in out.parents:raise ValueError('output must be outside checkout')
    out.mkdir(parents=True,exist_ok=False)
    try:execute(out,a.git_repo.resolve())
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
