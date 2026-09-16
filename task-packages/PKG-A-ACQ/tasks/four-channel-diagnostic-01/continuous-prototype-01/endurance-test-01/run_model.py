"""Host-only simulation of the proposed C receive loop. No ARM/Vitis build."""
import argparse
from pathlib import Path
import sys
import time
import uuid
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root.parent/'timerfixed-entry-01'))
import check_entry as prior
p=argparse.ArgumentParser()
p.add_argument('--gcc',default='F:/Program/env/mingw64/bin/gcc.exe')
a=p.parse_args()
out=root/'evidence'/(time.strftime('%Y%m%d_%H%M%S')+'_model_'+uuid.uuid4().hex[:8])
out.mkdir(parents=True)
try:
    gcc=prior.safe.need_tool(a.gcc)
    cmd=[gcc,'-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',
         '-I'+str(root/'proposed-src/continuous'),'-I'+str(root.parent/'tests'),
         root/'proposed-src/continuous/continuous_core.c',root/'tests/test_endurance.c',
         '-o',out/'test_endurance.exe']
    prior.safe.run_command(cmd,out,'host-compile',root)
    log=prior.safe.run_command([out/'test_endurance.exe'],out,'host-test',root)
    prior.need('ENDURANCE_MODEL_PASS' in log,'Missing pass marker')
    prior.safe.write_json(out/'result.json',{'status':'HOST_MODEL_PASS_NOT_ARM_NOT_BOARD',
        'sources':{str(f):prior.digest(f) for f in [root/'proposed-src/continuous/continuous_core.c',
            root/'proposed-src/continuous/continuous_core.h',root/'tests/test_endurance.c',root.parent/'tests/test_core.c']}})
    print(log)
except Exception as exc:
    prior.safe.write_json(out/'failure.json',{'status':'FAIL','error':str(exc)})
    raise
