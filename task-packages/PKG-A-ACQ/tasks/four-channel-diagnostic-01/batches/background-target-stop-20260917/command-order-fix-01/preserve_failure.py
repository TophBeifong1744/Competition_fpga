"""Snapshot this user's failed build, never modify or build the Vitis application."""
from pathlib import Path
import shutil,json,hashlib
HERE=Path(__file__).resolve().parent
BATCH=HERE.parent
APP=Path('F:/College/verilog_digital_system/Vitis/four_mic_endurance')
out=HERE/'before-fix'
out.mkdir(exist_ok=False)
for name in ('check_scene.py','POLICY.json','tests/test_gate.py','SHA256.json'):
    dst=out/'checker'/name;dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(BATCH/name,dst)
for name in ('src','_ide/launch.json','vitis-comp.json','build/compile_commands.json',
             'build/build.ninja','build/memory.map','build/four_mic_endurance.elf',
             'build/CMakeFiles/four_mic_endurance.elf.dir/main.c.obj',
             'scene_checks/20260917_150012_pre_b504f6fee7',
             'scene_checks/20260917_150013_post_f0ac8be96d'):
    source=APP/name;dst=out/'app'/name;dst.parent.mkdir(parents=True,exist_ok=True)
    if source.is_dir():shutil.copytree(source,dst)
    else:shutil.copyfile(source,dst)
files={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
       for p in sorted(out.rglob('*')) if p.is_file()}
(out/'SHA256.json').write_text(json.dumps(dict(scope='Original failed user build, no agent compilation',
    files=files),indent=2),encoding='utf-8')
print(out)
