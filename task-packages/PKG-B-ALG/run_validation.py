"""Run B's reader, localization, tracking, presence and independent candidate-research tests."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import platform
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'payload/model/python'))
from h1_reader import ReaderSession


class Results(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs); self.records={}
    def addSuccess(self,test):
        super().addSuccess(test); self.records[test.id()]='PASS'
    def addFailure(self,test,err):
        super().addFailure(test,err); self.records[test.id()]='FAIL'
    def addError(self,test,err):
        super().addError(test,err); self.records[test.id()]='ERROR'
    def addSubTest(self,test,subtest,err):
        super().addSubTest(test,subtest,err)
        if err is not None:self.records[test.id()]='FAIL'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):parser.error('output directory must be new or empty')
    args.out.mkdir(parents=True,exist_ok=True)
    ref=ROOT/'reference/h1-ss-data-draft-0.3'
    raw=(ref/'evidence/h1-files.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='ef09838face445cc4f2a87d56245ad64574fa3e9f4d12032e4b0723a7f1eca96'
    for item in json.loads(raw)['files']:
        assert hashlib.sha256((ref/item['path']).read_bytes()).hexdigest()==item['sha256']
    suite=unittest.defaultTestLoader.discover(str(ROOT/'payload/tb/python'))
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=Results).run(suite)
    (args.out/'tests.txt').write_text(stream.getvalue(),encoding='utf-8')
    plan=json.loads((ref/'payload/examples/h1/reader-test-plan.json').read_text(encoding='utf-8'))
    statuses=[]
    for case in plan['cases']:
        test='test_h1_reader.H1Required.test_'+case['id'].replace('-','_')
        statuses.append(dict(id=case['id'],expected=case['expected'],test=test,status=result.records.get(test,'NOT_RUN')))
    passed=result.wasSuccessful() and all(s['status']=='PASS' for s in statuses)
    report=dict(status='PASS' if passed else 'FAIL',tests_run=result.testsRun,
        required_cases=statuses,python=platform.python_version(),numpy=np.__version__,
        interface_version='ss-data-draft-0.3',interface_manifest_sha256=hashlib.sha256(raw).hexdigest(),
        source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'payload').rglob('*.py'))},
        test_results=result.records,scope='Reader, localization, tracking, presence, quorum and weighted-GCC behavior; no hardware or H2/H3 approval')
    (args.out/'validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if passed:
        session=ReaderSession()
        examples={name:session.load(ref/'payload/examples/h1'/name).summary() for name in ['code-pattern','restart']}
        (args.out/'fixture-diagnostics.json').write_text(json.dumps(examples,indent=2)+'\n',encoding='utf-8')
    print(f"{report['status']}: {result.testsRun} tests; {sum(s['status']=='PASS' for s in statuses)}/15 A-authored cases")
    if not passed:print(stream.getvalue())
    return 0 if passed else 1


if __name__=='__main__':sys.exit(main())
