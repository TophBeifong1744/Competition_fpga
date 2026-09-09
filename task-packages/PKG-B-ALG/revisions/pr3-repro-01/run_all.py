"""Run real tests, live audits and paired reconstruction; never reuse old PASS.

Usage: python -B revisions/pr3-repro-01/run_all.py --out NEW_DIRECTORY
Every child gets a fresh import namespace. Failed stages keep their logs and
numeric/hash differences. Existing output directories are rejected.
"""
import argparse
import csv
import importlib
import json
import subprocess
import sys
import traceback
import unittest
from pathlib import Path
from common import ROOT, HERE, PACKAGES, DIFF, read, write, sha, environment, verify_package


def compare_tree(old, new, path=''):
    if isinstance(old, dict):
        assert old.keys() == new.keys(), path
        for k in old: compare_tree(old[k],new[k],path+'/'+k)
    elif isinstance(old, list):
        assert len(old) == len(new), path
        for a,b in zip(old,new): compare_tree(a,b,path+'[]')
    elif isinstance(old, float):
        angular = any(k in path for k in ['cone','error_deg','truth_error','max_angle_change'])
        DIFF.numeric(old,new,path,angular=angular,atol=1e-8)
    else:
        assert type(old) is type(new) and old == new, (path,old,new)


def stable(out):
    import stable_rerun as study
    study.OUT=out
    study.run()
    base=ROOT/'research/stable-wrong-01'
    for name in ['cohort.json','controls.json','summary.json']:
        compare_tree(read(base/name),read(out/name),name)
    summary=read(out/'summary.json')
    assert (summary['selected'],summary['crossing'],summary['selected']-summary['crossing'],summary['same_frame_fresh_output']) == (563,317,246,182)
    methods=['original','no_noise','dry','dry_no_noise']
    assert [summary['controls'][m]['all']['wrong_incone'] for m in methods] == [563,185,309,0]
    assert [summary['controls'][m]['all']['valid'] for m in methods] == [563,563,549,563]
    with (ROOT/'research/effective-perturbation-01/evidence/frames.csv').open(newline='',encoding='utf-8') as stream:
        outside=sum(r['method']=='effective_known_only' and r['scope']=='target_active' and r['allowed']=='False' and r['fresh_valid']=='True' for r in csv.DictReader(stream))
    assert outside == 205
    return dict(status='PASS',controls=2252,cohort=563,crossing=317,not_crossing=246,
                same_frame_fresh=182,whole_batch_outside_fresh=outside,dry_invalid=14,
                all_discrete_fields_equal=True,original_files_byte_equal={n:sha(base/n)==sha(out/n) for n in ['cohort.json','controls.json','summary.json']})


def tests(name):
    sys.path.insert(0,str(ROOT/'payload/model/python'))
    directory=ROOT/'research'/name
    sys.path.insert(0,str(directory))
    suite=unittest.defaultTestLoader.discover(str(ROOT/'payload/tb/python'))
    if name=='stable-wrong-01':
        import stable_tests
        module=stable_tests
    else:
        module=importlib.import_module('test_study' if name=='tonal-edge-01' else 'test_guard' if name=='narrowband-guard-01' else 'test_features')
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful(), 'regression failure'
    return dict(status='PASS',tests=result.testsRun,base_tests=167)


def stage(kind,name,out):
    if kind=='tests': return tests(name)
    if kind=='audit':
        module=importlib.import_module('audit_'+name.replace('-','_'))
        return (module.audit if name=='narrowband-guard-01' else module.run)()
    if kind=='final':return importlib.import_module('final_'+name.replace('-','_')).check()
    if kind=='stable':return stable(out)
    if kind=='unit':
        import test_revision
        result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_revision))
        assert result.wasSuccessful()
        return dict(status='PASS',tests=result.testsRun)
    raise ValueError(kind)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--stage',choices=['tests','audit','final','stable','unit'])
    parser.add_argument('--package',default='')
    args=parser.parse_args()
    out=args.out.resolve()
    out.mkdir(parents=True,exist_ok=False)
    if args.stage:
        try:
            result=stage(args.stage,args.package,out)
            write(out/'result.json',result)
        except Exception:
            write(out/'failure.json',dict(status='FAIL',traceback=traceback.format_exc()))
            raise
        finally:
            write(out/'differences.json',dict(numerical=DIFF.values,input_hashes=DIFF.inputs))
        return
    write(out/'environment.json',environment())
    write(out/'integrity.json',verify_package())
    stages=[('unit','')]+[('tests',n) for n in PACKAGES]+[('final',n) for n in PACKAGES[:-1]]+[('audit',n) for n in PACKAGES[1:-1]]+[('stable','')]
    results=[]
    for kind,name in stages:
        key=kind+('-'+name if name else '')
        command=[sys.executable,'-B',str(Path(__file__).resolve()),'--stage',kind,'--package',name,'--out',str(out/key)]
        print('RUN',key,flush=True)
        with (out/(key+'.log')).open('w',encoding='utf-8') as log:
            result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
        results.append(dict(stage=key,command=command,returncode=result.returncode))
        write(out/'stages.json',results)
        print('PASS' if result.returncode==0 else 'FAIL',key,flush=True)
    write(out/'integrity-after.json',verify_package())
    write(out/'run.json',dict(status='PASS' if all(r['returncode']==0 for r in results) else 'FAIL',stages=results,
                            sources={p.name:sha(p) for p in HERE.glob('*.py')}))
    if any(r['returncode'] for r in results):raise SystemExit(1)


if __name__=='__main__':main()
