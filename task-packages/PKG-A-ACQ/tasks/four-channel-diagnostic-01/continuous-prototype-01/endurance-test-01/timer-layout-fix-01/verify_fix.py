"""Read-only replay against the user's failed-build artifacts; never compiles firmware."""
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

HERE=Path(__file__).resolve().parent
ENTRY=HERE.parent
sys.path.insert(0,str(ENTRY))
import check_endurance as gate
out=HERE/('recheck_'+time.strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8]);out.mkdir()
app=Path('F:/College/verilog_digital_system/Vitis/four_mic_endurance')
tools=Path('F:/AMD/2025.2/Vitis/gnu/aarch32/nt/gcc-arm-none-eabi/bin')

def run(name,argv):
    proc=subprocess.run([str(x) for x in argv],capture_output=True,text=True)
    gate.base.safe.write_json(out/(name+'.json'),dict(argv=list(map(str,argv)),returncode=proc.returncode,
                               stdout=proc.stdout,stderr=proc.stderr))
    gate.need(proc.returncode==0,'Failed '+name)
    print(name+': PASS')

try:
    # Snapshot and live files must match; no stale test fixture substituted for current ELF.
    pairs=[(HERE/'build/main.c.obj',app/'build/CMakeFiles/four_mic_endurance.elf.dir/main.c.obj'),
           (HERE/'build/four_mic_endurance.elf',app/'build/four_mic_endurance.elf'),
           (HERE/'build/memory.map',app/'build/memory.map')]
    gate.need(all(gate.base.digest(a)==gate.base.digest(b) for a,b in pairs),'Live artifacts changed')
    gate.base.safe.write_json(out/'artifact-binding.json',{str(b):gate.base.digest(b) for a,b in pairs})
    run('layout-tests',[sys.executable,'-B',ENTRY/'tests/test_timer_layout.py'])
    run('profile-tests',[sys.executable,'-B',ENTRY/'tests/test_gate.py'])
    for name,path in [('new-object',pairs[0][1]),('new-elf',pairs[1][1]),
                      ('old-object',gate.base.REFERENCE/'build/main.c.obj'),
                      ('old-elf',gate.base.REFERENCE/'runtime/four_mic_continuous.elf')]:
        run(name+'-disassembly',[tools/'arm-none-eabi-objdump.exe','-d','--disassemble=now_us',path])
    run('object-relocations',[tools/'arm-none-eabi-objdump.exe','-r',pairs[0][1]])
    # Only checker executions, with all output inside this increment. New pre is AFTER
    # the user's build, so its matching post correctly reports fresh_compilation=false.
    record=ENTRY/'evidence'/out.name
    for stage in ('pre','post'):
        run('full-'+stage,[sys.executable,'-B',ENTRY/'check_endurance.py','--stage',stage,
            '--app',app,'--platform',app.parent/'continuous_platform','--tools-bin',tools,
            '--record-root',record])
    report=json.loads(next(record.glob('*_post_*/result.json')).read_text(encoding='utf-8'))
    gate.need(report['fresh_compilation_observed'] is False,'Replay must not claim a new build')
    gate.base.safe.write_json(out/'result.json',dict(status='EXISTING_USER_ARTIFACT_RECHECK_PASS_NOT_NEW_BUILD_NOT_BOARD',
        record_root=str(record),compiled=report['compiled'],board_test='NOT_RUN'))
except Exception as exc:
    gate.base.safe.write_json(out/'failure.json',dict(error=str(exc)));raise
