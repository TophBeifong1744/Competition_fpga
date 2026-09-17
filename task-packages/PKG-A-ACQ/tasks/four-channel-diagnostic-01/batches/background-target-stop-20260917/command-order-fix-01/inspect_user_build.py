"""Read-only inspection of the user's 15:00 build. Never compiles or loads firmware."""
from pathlib import Path
from types import SimpleNamespace
import importlib.util,json,sys,time,uuid,hashlib
HERE=Path(__file__).resolve().parent;BATCH=HERE.parent
sys.path.insert(0,str(BATCH))
import check_scene as current
old_path=HERE/'before-fix/checker/check_scene.py'
spec=importlib.util.spec_from_file_location('s1_before_order_fix',old_path)
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
app=Path('F:/College/verilog_digital_system/Vitis/four_mic_endurance')
out=HERE/('inspection_'+time.strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8])
out.mkdir(exist_ok=False)
report=dict(scope='Existing user ARM artifacts, not new agent compilation or board test',
            fresh_guarded_build_required=True,board_run=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(): (out/'result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
try:
    entries=json.loads((app/'build/compile_commands.json').read_text())
    commands=(HERE/'before-fix/app/scene_checks/20260917_150013_post_f0ac8be96d/generated-commands.log').read_text()
    try:old.check_commands(entries[0]['command'],commands)
    except ValueError as e:report['before_rejected']=str(e)
    else:raise ValueError('Original failure not reproduced')
    current.check_commands(entries[0]['command'],commands)
    report['command_match_after_fix']=True
    report['source_sha256']=current.source_check(app/'src')
    report['compiled']=current.compiled(app/'build/CMakeFiles/four_mic_endurance.elf.dir/main.c.obj',app/'build/four_mic_endurance.elf')
    report['graph']=current.check_build_graph((app/'build/build.ninja').read_text())
    # Run the full post checker through source, BSP/tool/XSA, real commands,
    # ARM timer, map and link library checks. It MUST reject the stale pre receipt.
    args=SimpleNamespace(app=str(app),platform=str(app.parent/'continuous_platform'),
        tools_bin='F:/AMD/2025.2/Vitis/gnu/aarch32/nt/gcc-arm-none-eabi/bin',stage='post',
        record_root=str(HERE/'before-fix/app/scene_checks'))
    try:current.verify(args,out)
    except ValueError as e:
        expected='Verifier changed since previous stage; re-run guarded pre/build, do not reuse old receipt'
        if str(e)!=expected:raise
        report['full_post_result']='EXPECTED_STALE_VERIFIER_RECEIPT_REJECTION'
        report['full_post_reason']=str(e)
    else:raise ValueError('Changed checker unexpectedly accepted old pre-build receipt')
    report['load_paths_read_only']=current.base.launch_paths(app,app.parent)
    for key,name in (('bit','system_continuous_20260915.bit'),('init','ps7_init.tcl')):
        current.base.pinned(report['load_paths_read_only'][key],current.base.POLICY['hardware_sha256'][name])
    paths=['build/four_mic_endurance.elf','build/CMakeFiles/four_mic_endurance.elf.dir/main.c.obj',
           'build/memory.map','build/build.ninja','build/compile_commands.json','_ide/launch.json']
    report['artifact_sha256']={p:sha(app/p) for p in paths}
    for p,digest in report['artifact_sha256'].items():
        if sha(HERE/'before-fix/app'/p)!=digest:raise ValueError('Actual app changed during diagnosis: '+p)
    report['status']='REPAIR_AND_READ_ONLY_BINDING_CHECKED_NOT_FRESH_BUILD_NOT_BOARD'
    put();print(json.dumps(dict(status=report['status'],record=str(out)),ensure_ascii=False))
except Exception as e:
    report.update(status='FAILED',error=str(e));put();raise
