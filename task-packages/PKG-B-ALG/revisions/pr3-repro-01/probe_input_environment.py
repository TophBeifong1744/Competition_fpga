"""Fail closed when a regenerated waveform differs from the historical hash.

This small preflight is useful before a full audit on another CPU. Its success
does not replace the per-input checks in run_all.
"""
import argparse
from pathlib import Path
import sys
from common import ROOT, DIFF, read, write, environment

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    write(args.out/'environment.json',environment())
    sys.path.insert(0,str(ROOT/'research/narrowband-guard-01'))
    import study
    folder=ROOT/'research/subband-confidence-01/evidence'
    plan=read(folder/'plan.json')['acoustic']
    # A full six-channel input, not a sample fragment or a changed experiment.
    saved=next(m for m in read(folder/'inputs.json') if m['room']['name']=='early_late')
    _,rebuilt=study.generate(plan,saved['noise'],saved['direction'],saved['room'],saved['seed'])
    try:
        DIFF.input(saved,rebuilt)
    finally:
        write(args.out/'input-hashes.json',DIFF.inputs)
    write(args.out/'result.json',dict(status='PASS_EXACT_INPUT_PREFLIGHT',not_full_audit=True))

if __name__=='__main__':main()
