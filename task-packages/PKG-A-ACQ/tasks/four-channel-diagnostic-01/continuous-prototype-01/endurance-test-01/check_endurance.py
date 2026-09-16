"""E1 profile adapter for the existing timer-fixed verifier; never builds/loads.

Fixed candidate only: source/config pins plus real object/ELF contracts and schedule.
"""
import argparse
import json
from pathlib import Path
import re
import struct
import sys
import time
import uuid

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'timerfixed-entry-01'))
import check_entry as base
import timer_layout
need=base.need
POLICY=json.loads((HERE/'POLICY.json').read_text(encoding='utf-8'))
APP_NAME='four_mic_endurance'
PROFILE=(0x454e4431,1,300000000,14400000,10000000,480000,10,11,1000000,2000000)
SCHEDULE=(300000000,14400000)+(10000000,480000)*10

def text_hash(path):
    import hashlib
    return hashlib.sha256(Path(path).read_text(encoding='utf-8').replace('\r\n','\n').encode()).hexdigest()

def expected_cmake():
    text=(base.REFERENCE/'ps/CMakeLists.txt').read_text(encoding='utf-8').strip()
    return text.replace('set(APP_NAME four_mic_continuous)','set(APP_NAME '+APP_NAME+')')+'\n\n'+hook()

def hook():
    return '# BEGIN E1 ENDURANCE ENTRY\ninclude("'+HERE.as_posix()+'/vitis_gate.cmake")\n# END E1 ENDURANCE ENTRY'

def source_check(src):
    result={}
    for name,sha in POLICY['source_text_sha256'].items():
        need(text_hash(src/name)==sha,'Unsupported source/config: '+name)
        result[name]=base.digest(src/name)
    found={p.relative_to(src).as_posix() for p in src.rglob('*') if p.is_file()
           and p.suffix.lower() in ('.c','.h','.s','.asm','.cpp','.cxx','.cc','.hpp','.inc')}
    need(found=={'main.c','continuous/continuous_core.c','continuous/continuous_core.h','continuous/main_continuous.c'},
         'Unexpected compiled source/header')
    need((src/'CMakeLists.txt').read_text(encoding='utf-8').strip()==expected_cmake(),'Missing/modified E1 CMake hook or body')
    result['CMakeLists.txt']=base.digest(src/'CMakeLists.txt')
    return result

def check_contract_bytes(contract,schedule):
    need(contract==struct.pack('<10I',*PROFILE),'Compiled E1 profile mismatch')
    need(schedule==struct.pack('<22I',*SCHEDULE),'Compiled actual session schedule mismatch')

def compiled(obj,elf):
    result=timer_layout.verify(obj,elf) # same arithmetic/RX checks; validate pool alignment and real calls
    for path,kind in ((obj,1),(elf,2)):
        parsed=base.Elf32(path,kind)
        check_contract_bytes(base.symbol(parsed,'endurance_contract')[1],base.symbol(parsed,'endurance_schedule')[1])
    result.update(profile=list(PROFILE),schedule=list(SCHEDULE))
    return result

def verify(args,out):
    for name,sha in POLICY['checker_dependencies'].items():
        base.pinned(HERE.parent/name,sha)
    app=base.safe.no_links(args.app);platform=base.safe.no_links(args.platform)
    need(app.name==APP_NAME and platform.name=='continuous_platform','Wrong app/platform')
    inputs=source_check(app/'src')
    component=json.loads((app/'vitis-comp.json').read_text(encoding='utf-8'))
    need(component['name']==APP_NAME and component['platform']==platform.name and
         component['domain']=='standalone_ps7_cortexa9_0' and component['cpuInstance']=='ps7_cortexa9_0'
         and component['os']=='standalone','Wrong domain')
    bsp=platform/'export/continuous_platform/sw/standalone_ps7_cortexa9_0'
    for name,sha in base.POLICY['bsp_sha256'].items():base.pinned(bsp/name,sha)
    config=json.loads((platform/'vitis-comp.json').read_text(encoding='utf-8'))
    xsa_sha=base.POLICY['hardware_sha256']['system_continuous_20260915.xsa']
    for path in (Path(config['configuration']['xsa']),platform/'hw/system_continuous_20260915.xsa',
                 platform/'export/continuous_platform/hw/system_continuous_20260915.xsa'):
        base.pinned(path,xsa_sha)
    tools=Path(args.tools_bin).resolve(strict=True)
    for name in ('arm-none-eabi-gcc.exe','arm-none-eabi-objdump.exe'):base.safe.need_tool(tools/name)
    report=dict(stage=args.stage,app=str(app),platform=str(platform),source_sha256=inputs,
                policy_sha256=base.digest(HERE/'POLICY.json'),board_test='NOT_RUN',
                xsa_sha256=xsa_sha,bsp_files=len(base.POLICY['bsp_sha256']),
                verifier_sha256={name:base.digest(HERE/name) for name in
                                 ('check_endurance.py','timer_layout.py','vitis_gate.cmake')})
    obj=app/'build/CMakeFiles/four_mic_endurance.elf.dir/main.c.obj'
    elf=app/'build/four_mic_endurance.elf'
    if args.stage=='pre':
        report.update(prechecked_at_ns=time.time_ns(),object_mtime_before_ns=obj.stat().st_mtime_ns if obj.exists() else None)
        return report
    entries=json.loads((app/'build/compile_commands.json').read_text(encoding='utf-8'))
    need(len(entries)==1 and Path(entries[0]['file']).resolve()==app/'src/main.c','Wrong compiled units')
    reference=base.normalize_command(base.POLICY['compile_command'],Path(base.POLICY['reference_app']),Path(base.POLICY['reference_bsp']))
    reference=reference.replace('four_mic_continuous.elf','four_mic_endurance.elf')
    need(base.normalize_command(entries[0]['command'],app,bsp)==reference,'Compiler flags/includes/specs mismatch')
    need(Path(entries[0]['command'].split(' ')[0]).resolve()==(tools/'arm-none-eabi-gcc.exe').resolve(),'Compiler path mismatch')
    report['compiler']=base.safe.run_command([tools/'arm-none-eabi-gcc.exe','--version'],out,'compiler',app)
    report['compiled']=compiled(obj,elf)
    mapping=(app/'build/memory.map').read_text(encoding='utf-8')
    ends=re.findall(r'0x([0-9a-fA-F]+)\s+end\s*=\s*\.',mapping)
    need(len(ends)==1 and int(ends[0],16)==report['compiled']['program_end'],'Map/end mismatch')
    need(re.search(r'ps7_ddr_0_memory_0\s+0x00100000\s+0x00f00000',mapping),'Program region mismatch')
    for lib in ('libxil.a','libxilstandalone.a','libxiltimer.a'):
        paths=[Path(s[5:].strip()).resolve() for s in mapping.splitlines() if s.startswith('LOAD ') and s.replace('\\','/').endswith('/'+lib)]
        need(paths==[(bsp/'lib'/lib).resolve()],'BSP link mismatch: '+lib)
    report['disassembly']=base.safe.run_command([tools/'arm-none-eabi-objdump.exe','-d','--disassemble=now_us',elf],out,'timer',app)
    previous=[]
    for path in Path(args.record_root).glob('*/result.json'):
        item=json.loads(path.read_text(encoding='utf-8'))
        if item.get('app')==str(app) and item.get('policy_sha256')==report['policy_sha256']:
            previous.append((path.stat().st_mtime_ns,path,item))
    stage='pre' if args.stage=='post' else 'post'
    prior=sorted((v for v in previous if v[2].get('stage')==stage),key=lambda v:v[0])
    need(prior,'Missing prior guarded '+stage+' record')
    before=prior[-1][2];report['prior_record']=str(prior[-1][1])
    need(before['source_sha256']==inputs,'Sources changed since previous stage')
    need(before.get('verifier_sha256')==report['verifier_sha256'],
         'Verifier changed since previous stage; re-run guarded pre/build, do not reuse old receipt')
    if args.stage=='post':
        report['fresh_compilation_observed']=obj.stat().st_mtime_ns>=before['prechecked_at_ns']
        report['load_config']='NOT_CHECKED_USE_LOAD_STAGE'
    else:
        need(before['compiled']['elf_sha256']==report['compiled']['elf_sha256'] and
             before['compiled']['object_sha256']==report['compiled']['object_sha256'],'Different artifact since guarded build')
        report['load_paths']=base.launch_paths(app,app.parent)
        for key,name in (('bit','system_continuous_20260915.bit'),('init','ps7_init.tcl')):
            base.pinned(report['load_paths'][key],base.POLICY['hardware_sha256'][name])
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',choices=('pre','post','load'),required=True)
    for name in ('app','platform','tools-bin','record-root'):p.add_argument('--'+name,required=True)
    args=p.parse_args()
    # Evidence restricted to this increment or app/e1_checks, never src/build/old packages.
    root=base.safe.no_links(args.record_root)
    need(root.is_absolute(),'Output must be absolute')
    app=base.safe.no_links(args.app)
    allowed=(HERE/'evidence').resolve(),(app/'e1_checks').resolve()
    need(any(base.safe.under(root,r) for r in allowed),'Evidence root must be increment/evidence or app/e1_checks')
    need(not root.is_symlink(),'Linked evidence path')
    root.mkdir(parents=True,exist_ok=True)
    out=root/(time.strftime('%Y%m%d_%H%M%S')+'_'+args.stage+'_'+uuid.uuid4().hex[:10]);out.mkdir()
    base.safe.write_json(out/'request.json',vars(args))
    try:
        report=verify(args,out)
        report['status']={'pre':'E1_PRECHECK_ONLY','post':'E1_ARTIFACT_PASS_NOT_LOAD_NOT_BOARD','load':'E1_LOAD_PREFLIGHT_PASS_NOT_BOARD'}[args.stage]
        base.safe.write_json(out/'result.json',report);print(report['status']+' '+str(out));return 0
    except Exception as exc:
        base.safe.write_json(out/'failure.json',dict(status='REJECTED',error=str(exc)))
        print('REJECTED '+str(exc)+' EVIDENCE='+str(out),file=sys.stderr);return 1

if __name__=='__main__':sys.exit(main())
