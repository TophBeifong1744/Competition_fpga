"""Author candidate reproduction, fresh external output only; never approval."""
import argparse
import subprocess
import sys
import traceback
import numpy as np
from common import HERE,ROOT,load,dump,sha,new_output
from verify import verify

def execute(out):
    before=verify()
    commands=[]
    jobs=[('tests',[sys.executable,'-B','-m','unittest','discover','-s',str(HERE/'source'),'-p','test_candidates.py','-v']),
          ('study',[sys.executable,'-B',str(HERE/'source/run.py'),'--out',str(out/'study')]),
          ('golden',[sys.executable,'-B',str(HERE/'source/golden.py'),'--study',str(out/'study'),'--out',str(out/'golden')])]
    for name,cmd in jobs:
        p=subprocess.run(cmd,cwd=ROOT,capture_output=True)
        (out/(name+'-stdout.txt')).write_bytes(p.stdout)
        (out/(name+'-stderr.txt')).write_bytes(p.stderr)
        commands.append(dict(name=name,argv=cmd,returncode=p.returncode))
        dump(out/'commands.json',commands)
        if p.returncode:raise RuntimeError(name+' failed; retain logs')
    archived=HERE/'evidence/run01'
    for p in archived.glob('*.json'):
        if p.name=='OUTPUT-SHA256.json':continue
        a=load(p);b=load(out/'study'/p.name)
        if p.name=='summary.json':a.pop('environment');b.pop('environment')
        if a!=b:raise AssertionError('numerical/control JSON mismatch: '+p.name)
    waves=list((archived/'audio').glob('*.wav'))
    assert len(waves)==48
    for p in waves:
        if sha(p)!=sha(out/'study/audio'/p.name):raise AssertionError('PCM/WAV mismatch '+p.name)
    golden=HERE/'evidence/golden02';arrays=0
    for p in golden.glob('*.npz'):
        with np.load(p,allow_pickle=False) as a,np.load(out/'golden'/p.name,allow_pickle=False) as b:
            assert a.files==b.files
            for key in a.files:
                np.testing.assert_array_equal(a[key],b[key]);arrays+=1
    assert load(golden/'summary.json')==load(out/'golden/summary.json')
    assert before==verify()
    result=dict(status='AUTHOR_REPRODUCED_NOT_INDEPENDENT_APPROVAL',snapshot=before,wavs_exact=len(waves),
        integer_arrays_exact=arrays,study_json_exact=True,commands=commands,production_or_hardware_approval=False)
    dump(out/'result.json',result)
    print('PASS_CANDIDATE_REPRODUCTION',len(waves),arrays)

if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__);p.add_argument('--out',required=True)
    out=new_output(p.parse_args().out)
    try:execute(out)
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
