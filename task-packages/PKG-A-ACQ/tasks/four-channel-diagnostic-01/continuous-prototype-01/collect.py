"""Collect verified build/test evidence to an exclusive package subdirectory."""
import argparse,json,shutil,zipfile
from pathlib import Path
import run as c
p=argparse.ArgumentParser()
for n in ('build','sim','host','safety','output'):p.add_argument('--'+n,required=True)
p.add_argument('--history',action='append',default=[])
p.add_argument('--short-app',required=True)
a=p.parse_args();out=c.fresh(a.output)
try:
    built=Path(a.build);sim=Path(a.sim);host=Path(a.host);safety=Path(a.safety)
    result=json.loads((built/'result.json').read_text())
    c.safe.require(result['status']=='CANDIDATE_BUILD_PASS_NOT_BOARD','build gate failed')
    for folder,marker in ((sim,'RTL_SIM_PASS_NOT_BOARD'),(host,'PS_MODEL_PASS_NOT_HARDWARE_CACHE_TEST'),(safety,'OFFLINE_TESTS_PASS')):
        c.safe.require(json.loads((folder/'result.json').read_text())['status']==marker,'test gate failed')
    c.safe.require(not c.safe.unchanged(json.loads((built/'preflight.json').read_text())),'original changed since build')
    # Simulated RTL and compiled application must be the actual built candidate.
    for p in (c.HERE/'rtl').glob('*.v'):
        c.safe.require(c.safe.sha(p)==c.safe.sha(sim/p.name)==c.safe.sha(built/'candidate/rtl'/p.name),'RTL/test/build mismatch')
    for p in (c.HERE/'ps').glob('*'):
        c.safe.require(c.safe.sha(p)==c.safe.sha(built/'ps'/p.name),'PS/build mismatch')
    for name in ('continuous_core.c','continuous_core.h'):
        c.safe.require(c.safe.sha(host/name)==c.safe.sha(c.HERE/'ps'/name),'PS host model differs from executed loop')
    c.safe.require(c.safe.sha(sim/'pdm_cic3.v')==c.safe.sha(built/'inputs/project/one.srcs/sources_1/imports/rtl/pdm_cic3.v'),'CIC simulation/build mismatch')
    c.known_ps(built/'ps')
    evidence=out/'evidence';evidence.mkdir()
    for folder,name in ((built,'build'),(sim,'simulation'),(host,'ps-model'),(safety,'safety')):
        dest=evidence/name;dest.mkdir()
        for child in ('logs','reports','candidate','ps'):
            if (folder/child).is_dir():shutil.copytree(folder/child,dest/child)
        for q in folder.iterdir():
            if q.is_file() and q.suffix in ('.json','.tcl','.log','.sv','.v','.c','.h','.py'):c.copy(q,dest/q.name)
    release=out/'release';release.mkdir()
    for src,dst in [('artifacts/hw/system_continuous.bit','system_continuous.bit'),
                    ('artifacts/hw/system_continuous.xsa','system_continuous.xsa'),
                    ('artifacts/hw/ps7_init.tcl','ps7_init.tcl'),
                    ('artifacts/ps/four_mic_continuous.elf','four_mic_continuous.elf'),
                    ('artifacts/ps/memory.map','memory.map')]:c.copy(built/src,release/dst)
    c.write(release/'VERIFIED-BUILD.json',result)
    c.copy(built/'ps/contract-result.json',release/'PS-CONTRACT.json')
    c.manifest(release)
    rollback=out/'rollback-short';rollback.mkdir()
    for rel in ('build/four_mic_capture.elf','build/memory.map','_ide/bitstream/system_c_adapter.bit',
                '_ide/psinit/ps7_init.tcl','_ide/launch.json','src/main_four_capture.c','src/lscript.ld'):
        c.copy(c.safe.need_file(Path(a.short_app)/rel),rollback/rel)
    c.manifest(rollback)
    # Complete restartable build snapshot (including source, generated BD and DCP).
    histories=[built]+[Path(x) for x in a.history]
    history_dir=out/'history';history_dir.mkdir()
    index=[]
    for folder in histories:
        target=history_dir/(folder.name+'.zip')
        with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for f in folder.rglob('*'):
                if f.is_file():z.write(f,f.relative_to(folder).as_posix())
        with zipfile.ZipFile(target) as z:c.safe.require(z.testzip() is None,'damaged archive')
        index.append({'original_directory':str(folder),'archive':target.relative_to(out).as_posix(),'sha256':c.safe.sha(target)})
    c.write(out/'HISTORY.json',index)
    c.write(out/'RESULT.json',{'status':'PACKAGED_CANDIDATE_NOT_BOARD_OR_B_ACCEPTANCE','build':result,'original_preserved':True})
except Exception as e:c.write(out/'failure.json',{'error':str(e)});raise
finally:c.manifest(out)
