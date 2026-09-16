"""One-time candidate pins; never reads values from an operator-supplied JSON contract."""
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'timerfixed-entry-01'
REFERENCE=HERE.parent/'board-run-20260915-02/ps'
names=['main.c','continuous/main_continuous.c','continuous/continuous_core.c',
       'continuous/continuous_core.h','UserConfig.cmake','lscript.ld','Empty_applicationExample.cmake']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def textsha(path):return hashlib.sha256(path.read_text(encoding='utf-8').replace('\r\n','\n').encode()).hexdigest()
data={'profile':'E1_300S_10X10S','status':'CANDIDATE_NOT_B_APPROVED',
      'source_text_sha256':{n:textsha(HERE/'proposed-src'/n if (HERE/'proposed-src'/n).exists() else REFERENCE/n) for n in names},
      'checker_dependencies':{str(p.relative_to(HERE.parent)).replace('\\','/'):sha(p) for p in (BASE/'check_entry.py',BASE/'POLICY.json')}}
with (HERE/'POLICY.json').open('x',encoding='utf-8') as stream:json.dump(data,stream,indent=2)
print('CANDIDATE_PINS_CREATED_NOT_APPROVAL')
