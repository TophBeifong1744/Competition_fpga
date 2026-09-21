"""Run only this dynamic-DAS/ROM/width increment, preserving each exit/log."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import numpy as np


def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parent;repo=a.repo.resolve()
    stages=[('dynamic','verify_dynamic.py',[]),('delay','verify_delay.py',['--repo',str(repo)]),('widths','derive_widths.py',[]),('width-trace','verify_widths.py',['--repo',str(repo)]),('integration','verify_integration.py',['--repo',str(repo),'--rom',str(out/'delay/delay-rom-s16.npy')])]
    results=[]
    for name,script,extra in stages:
        command=[sys.executable,'-B',str(root/script),'--out',str(out/name),*extra]
        with (out/(name+'.log')).open('wb') as log:
            result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
        results.append(dict(stage=name,command=command,returncode=result.returncode))
        if result.returncode:break
    summary=dict(python=platform.python_version(),numpy=np.__version__,platform=platform.platform(),stages=results,source_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('*.py')})
    (out/'runner.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    seal={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}
    (out/'OUTPUT-SHA256.json').write_text(json.dumps(seal,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2));return int(any(x['returncode'] for x in results))


if __name__=='__main__':sys.exit(main())
