"""Rerun entry regression and preserved 34 baseline safety tests, with logs."""
import argparse,sys
from pathlib import Path
import run as candidate
p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args()
out=candidate.fresh(a.output)
try:
    for name,root,pattern in [('entry',candidate.HERE/'tests','test_entry.py'),
                             ('baseline34',candidate.HERE.parent/'current_build','test_build_current.py')]:
        candidate.run([sys.executable,'-B','-m','unittest','discover','-s',root,'-p',pattern,'-v'],out,name)
    candidate.write(out/'result.json',{'status':'OFFLINE_TESTS_PASS','candidate_entry':10,'preserved_baseline_safety':34,'board':False})
finally:candidate.manifest(out)
