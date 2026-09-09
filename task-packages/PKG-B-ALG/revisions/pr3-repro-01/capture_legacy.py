"""Read-only execution of pre-revision auditors, retaining their actual outcomes."""
import argparse
import subprocess
import sys
from common import ROOT, write, environment

def main():
    from pathlib import Path
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    write(args.out/'environment.json',environment())
    rows=[]
    for name in ['leave-band-out-01','effective-perturbation-01']:
        command=[sys.executable,'-B','-c','import audit; print(audit.run())']
        with (args.out/(name+'.log')).open('w',encoding='utf-8') as log:
            p=subprocess.run(command,cwd=ROOT/'research'/name,stdout=log,stderr=subprocess.STDOUT)
        rows.append(dict(package=name,command=command,returncode=p.returncode))
        print(name,p.returncode,flush=True)
    write(args.out/'results.json',rows)

if __name__=='__main__':main()
