"""Run targeted tests, render and verify without overwriting previous evidence."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parents[3]


def main():
    ap=argparse.ArgumentParser(__doc__)
    ap.add_argument('--out',type=Path,required=True)
    out=ap.parse_args().out.resolve()
    out.mkdir(parents=True,exist_ok=False)
    commands=[
        ('audio-tests',[sys.executable,'-B',str(HERE/'test_audio.py'),'-v']),
        ('tracker-adapter-tests',[sys.executable,'-B',str(HERE.parent/'test_tracking.py'),'-v']),
        ('manual-render-tests',[sys.executable,'-B',str(HERE.parent.parent/'real-audio-compare-01/test_render_audio.py'),'-v']),
        ('render',[sys.executable,'-B',str(HERE/'render_three.py'),'--out',str(out/'audio')]),
        ('audit',[sys.executable,'-B',str(HERE/'audit.py'),'--directory',str(out/'audio'),'--out',str(out/'audit.json')])]
    records=[]
    for label,command in commands:
        with (out/(label+'.log')).open('xb') as log:
            result=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        records.append(dict(label=label,command=command,cwd=str(ROOT),returncode=result.returncode))
        (out/'commands.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(label,'PASS' if result.returncode==0 else 'FAIL',flush=True)
        if result.returncode: raise SystemExit(result.returncode)


if __name__=='__main__':main()
