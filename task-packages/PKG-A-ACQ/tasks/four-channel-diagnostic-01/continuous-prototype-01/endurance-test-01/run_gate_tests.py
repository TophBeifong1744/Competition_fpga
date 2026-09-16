import json
from pathlib import Path
import subprocess
import sys
import time
import uuid
HERE=Path(__file__).resolve().parent
out=HERE/'evidence'/(time.strftime('%Y%m%d_%H%M%S')+'_gate_'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
command=[sys.executable,'-B',str(HERE/'tests/test_gate.py')]
p=subprocess.run(command,capture_output=True,text=True)
with (out/'test.json').open('x',encoding='utf-8') as stream:
    json.dump(dict(argv=command,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,
                   scope='Host contract/source mutations and real historical ELF rejection; no new ARM compilation'),stream,indent=2)
print(p.stdout+p.stderr)
raise SystemExit(p.returncode)
