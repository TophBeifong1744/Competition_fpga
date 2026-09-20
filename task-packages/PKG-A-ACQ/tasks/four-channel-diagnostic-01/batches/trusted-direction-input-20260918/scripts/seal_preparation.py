"""Create a new immutable preparation inventory; excludes no files except itself as output."""
import json
import platform
import subprocess
import sys
from pathlib import Path
import numpy as np
from prepare import HERE, save, sha

def main():
    output=HERE/'SHA256.json'
    if output.exists(): raise ValueError('Preparation manifest already exists; do not overwrite history')
    log=(HERE/'evidence/test-offline-01.log').read_text(encoding='utf-8-sig')
    if 'Ran 10 tests' not in log or not log.rstrip().endswith('OK'): raise ValueError('Missing preparation unit-test evidence')
    save(HERE/'evidence/preparation-summary.json',dict(
        status='PREPARED_WAITING_FOR_OPERATOR_PRECHECK',new_board_captures=0,target_captures=8,
        python=sys.version,numpy=np.__version__,os=platform.platform(),
        tests=dict(methods=10,result='PASS',exit_code=0,source='test-offline-01.log',
            scope='Synthetic alignment/failure checks plus existing 9/17 BIN/UART regression; no new hardware test'),
        current_host_preflight='REUSED_S1_LOAD_PREFLIGHT_PASS_NOT_BOARD',
        full_new_export_workflow='NOT_RUN_PENDING_FIRST_NEW_RECORDING',
        unchanged_hardware_and_firmware=True,agent_board_operations=False,
        known_playback=dict(device='phone loudspeaker',model=None,effects='operator confirmed all visible effects off',
                            volume='fixed; actual setting pending',internal_processing='unknown')))
    dependencies=[HERE.parent/'background-target-stop-20260917'/v for v in ('check_scene.py','finish_scene.py','POLICY.json')]
    save(HERE/'evidence/reused-dependencies.json',{str(p):sha(p) for p in dependencies})
    files={p.relative_to(HERE).as_posix():sha(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p!=output}
    save(output,dict(scope='Preparation only. New recording manifests must be separate; do not rewrite this inventory.',files=files))
    print('PREPARATION_MANIFEST',sha(output))

if __name__=='__main__':main()
