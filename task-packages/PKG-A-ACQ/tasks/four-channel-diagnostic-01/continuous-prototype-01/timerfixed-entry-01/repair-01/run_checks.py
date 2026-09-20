"""Capture exact test commands in a NEW directory. Never builds or uses hardware."""
import json
from pathlib import Path
import subprocess
import sys
import os
from datetime import datetime, timezone
entry=Path(__file__).resolve().parents[1]
out=Path(sys.argv[1]).resolve()
out.mkdir(parents=True,exist_ok=False)
jobs=[
 ('original18',[sys.executable,'-B','-m','unittest','-v','test_entry'],entry),
 ('repair',[sys.executable,'-B','-m','unittest','discover','-s','repair-01','-p','test_repair.py','-v'],entry),
 ('loader',[sys.executable,'-B','-m','unittest','discover','-s','repair-01','-p','test_loader.py','-v'],entry),
 ('parent10',[sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_entry.py','-v'],entry.parent),
 ('safety34',[sys.executable,'-B','-m','unittest','discover','-s','.','-p','test_build_current.py','-v'],entry.parent.parent/'current_build'),
]
results=[]
for name,argv,cwd in jobs:
    started=datetime.now(timezone.utc).isoformat()
    case_out=out/'loader-cases'
    if name=='loader':case_out.mkdir()
    env=dict(os.environ,TF_CASE_LOG_ROOT=str(case_out),PYTHONDONTWRITEBYTECODE='1')
    p=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,text=True,errors='replace')
    row=dict(name=name,argv=argv,cwd=str(cwd),started_utc=started,
             returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
    (out/(name+'.json')).write_text(json.dumps(row,indent=2,ensure_ascii=False),encoding='utf-8')
    results.append(dict(name=name,returncode=p.returncode))
    print(name,p.returncode,flush=True)
(out/'result.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
sys.exit(any(r['returncode'] for r in results))
