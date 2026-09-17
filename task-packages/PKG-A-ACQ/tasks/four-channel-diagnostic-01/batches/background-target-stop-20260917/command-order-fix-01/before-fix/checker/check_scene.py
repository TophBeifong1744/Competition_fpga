"""S1 incremental adapter derived from E1: proposed six-second raw archive.
Read-only checks, never compile/load; not B-approved secure loading.
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
DEPENDENCIES=HERE.parents[1]/'continuous-prototype-01'
sys.path.insert(0,str(DEPENDENCIES/'timerfixed-entry-01'))
sys.path.insert(0,str(DEPENDENCIES/'endurance-test-01'))
import check_entry as base
import timer_layout
need=base.need
POLICY=json.loads((HERE/'POLICY.json').read_text(encoding='utf-8'))
APP_NAME='four_mic_endurance'
PROFILE=(0x53434e31,1,6000000,288000,300000,9600000,64,2,32,48000,2000000)
CONTRACT=base.CONTRACT[:-2]+(6000000,288000)
EXPECTED_SOURCES={'main.c','continuous/continuous_core.c','continuous/continuous_core.h',
                  'continuous/main_continuous.c','continuous/scene_store.c','continuous/scene_store.h'}

def text_hash(path):
    import hashlib
    return hashlib.sha256(Path(path).read_text(encoding='utf-8').replace('\r\n','\n').encode()).hexdigest()

def expected_cmake():
    text=(base.REFERENCE/'ps/CMakeLists.txt').read_text(encoding='utf-8').strip()
    return text.replace('set(APP_NAME four_mic_continuous)','set(APP_NAME '+APP_NAME+')')+'\n\n'+hook()

def hook():
    return '# BEGIN S1 SCENE ENTRY\ninclude("'+HERE.as_posix()+'/vitis_gate.cmake")\n# END S1 SCENE ENTRY'

def source_check(src):
    result={}
    for name,sha in POLICY['source_text_sha256'].items():
        need((src/name).is_file(),'Missing required source/config: '+name)
        need(text_hash(src/name)==sha,'Unsupported source/config: '+name)
        result[name]=base.digest(src/name)
    found={p.relative_to(src).as_posix() for p in src.rglob('*') if p.is_file()
           and p.suffix.lower() in ('.c','.h','.s','.asm','.cpp','.cxx','.cc','.hpp','.inc')}
    need(found==EXPECTED_SOURCES,
         'Unexpected compiled source/header')
    need((src/'CMakeLists.txt').read_text(encoding='utf-8').strip()==expected_cmake(),'Missing/modified S1 CMake hook or body')
    result['CMakeLists.txt']=base.digest(src/'CMakeLists.txt')
    return result

def command_tokens(command):
    # Fixed actual app paths. No case-folding, path resolving, comma splitting or
    # removal of linker subarguments: appended --defsym/-e/--wrap MUST stay visible.
    tokens=re.findall(r'(?:[^\s"]|"[^"]*")+',command.strip())
    need(command.count('"')%2==0,'Unbalanced command quoting')
    return [t.replace('"','').replace('\\','/') for t in tokens]

def check_commands(actual_compile,ninja_output):
    need(command_tokens(actual_compile)==command_tokens(POLICY['compile_command']),
         'Compiler options or path differs from the fixed E1 toolchain contract')
    lines=[x for x in ninja_output.splitlines() if x.strip()]
    expected=POLICY['ninja_commands'].splitlines()
    need(len(lines)==len(expected) and all(command_tokens(a)==command_tokens(b)
         for a,b in zip(lines,expected)),'Generated commands/linker subarguments or gate mismatch')

def check_values(contract,scene):
    need(contract==struct.pack('<16I',*CONTRACT),'Object/ELF continuous contract mismatch')
    need(scene==struct.pack('<11I',*PROFILE),'Object/ELF S1 archive contract mismatch')

def check_ranges(exe):
    end=exe.symbol_value('end');ranges=exe.loads+exe.allocated
    need(end<=CONTRACT[1] and all(CONTRACT[10]<=r['start']<r['end']<=end for r in ranges),
         'Program/static archive/heap/stack overlaps RX or leaves program DDR')
    sym=exe.symbols.get('scene_archive')
    need(sym is not None and sym[2]==9600128,'Missing/wrong archive allocation size')
    addr=sym[1];section=exe.sections[sym[5]]
    need(section[1]==8 and section[2]&3==3 and addr%64==0 and
         section[3]<=addr<addr+sym[2]<=section[3]+section[5]<=end,
         'Archive not a distinct aligned writable BSS allocation')
    data=addr+64
    need(data+9600000+64==addr+sym[2]<=end<=0x01000000,'Archive guard/data bounds')
    return dict(program_end=end,ranges=ranges,archive_start=addr,archive_data=data,
                archive_end=addr+sym[2],capacity_bytes=9600000,guard_each=64)

def compiled(obj,elf):
    refs=((base.REFERENCE/'build/main.c.obj',1,'8a376d38a7188af5884ce0e6c7eff868a0878d222634ec360cb35961c7cd11ff'),
          (base.REFERENCE/'runtime/four_mic_continuous.elf',2,base.POLICY['archive_elf_sha256']))
    canonical=[timer_layout.inspect(base.Elf32(base.pinned(p,sha),kind),kind)[0] for p,kind,sha in refs]
    layout={}
    for path,kind in ((obj,1),(elf,2)):
        parsed=base.Elf32(path,kind)
        check_values(base.symbol(parsed,'continuous_contract')[1],base.symbol(parsed,'scene_contract')[1])
        instructions,detail=timer_layout.inspect(parsed,kind)
        need(instructions==canonical[0]==canonical[1],'Wrong timer arithmetic')
        layout[str(kind)]=detail
    result=check_ranges(parsed)
    need(parsed.entry==0x00100000,'ELF entry differs from fixed vector start')
    result.update(divisor=layout['2']['divisor'],contract=list(CONTRACT),scene=list(PROFILE),
                  elf_sha256=base.digest(elf),object_sha256=base.digest(obj),timer_layout=layout)
    return result


def verify(args,out):
    for name,sha in POLICY['checker_dependencies'].items():
        base.pinned(DEPENDENCIES/name,sha)
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
    for path,sha in POLICY['tool_sha256'].items():
        resolved=Path(path).resolve(strict=True)
        need(str(resolved)==POLICY['tool_resolved_paths'][path],'Tool installation target changed')
        # AMD's shipped Vitis/gnu junction is allowed ONLY with pinned target and bytes.
        base.pinned(resolved,sha)
    report=dict(stage=args.stage,app=str(app),platform=str(platform),source_sha256=inputs,
                policy_sha256=base.digest(HERE/'POLICY.json'),board_test='NOT_RUN',
                xsa_sha256=xsa_sha,bsp_files=len(base.POLICY['bsp_sha256']),
                verifier_sha256={name:base.digest(HERE/name) for name in
                                 ('check_scene.py','vitis_gate.cmake')})
    obj=app/'build/CMakeFiles/four_mic_endurance.elf.dir/main.c.obj'
    elf=app/'build/four_mic_endurance.elf'
    if args.stage=='pre':
        report.update(prechecked_at_ns=time.time_ns(),object_mtime_before_ns=obj.stat().st_mtime_ns if obj.exists() else None)
        return report
    entries=json.loads((app/'build/compile_commands.json').read_text(encoding='utf-8'))
    need(len(entries)==1 and Path(entries[0]['file']).resolve()==app/'src/main.c','Wrong compiled units')
    ninja=Path(POLICY['ninja'])
    base.safe.need_tool(ninja)
    import subprocess
    process=subprocess.run([str(ninja),'-t','commands'],cwd=app/'build',
                           capture_output=True,text=True,timeout=30)
    (out/'generated-commands.log').write_text(process.stdout,encoding='utf-8')
    (out/'generated-commands.stderr.log').write_text(process.stderr,encoding='utf-8')
    need(process.returncode==0,'Unable to inspect generated build commands')
    check_commands(entries[0]['command'],process.stdout)
    need(Path(entries[0]['command'].split(' ')[0]).resolve()==(tools/'arm-none-eabi-gcc.exe').resolve(),'Compiler path mismatch')
    report['compiler']=base.safe.run_command([tools/'arm-none-eabi-gcc.exe','--version'],out,'compiler',app)
    report['compiled']=compiled(obj,elf)
    mapping=(app/'build/memory.map').read_text(encoding='utf-8')
    report['map_sha256']=base.digest(app/'build/memory.map')
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
        need(report['fresh_compilation_observed'],'No fresh compilation observed: Clean then Build')
        report['load_config']='NOT_CHECKED_USE_LOAD_STAGE'
    else:
        need(before['compiled']['elf_sha256']==report['compiled']['elf_sha256'] and
             before['compiled']['object_sha256']==report['compiled']['object_sha256'],'Different artifact since guarded build')
        report['load_paths']=base.launch_paths(app,app.parent)
        report['launch_config_sha256']=base.digest(app/'_ide/launch.json')
        for key,name in (('bit','system_continuous_20260915.bit'),('init','ps7_init.tcl')):
            base.pinned(report['load_paths'][key],base.POLICY['hardware_sha256'][name])
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',choices=('pre','post','load'),required=True)
    for name in ('app','platform','tools-bin','record-root'):p.add_argument('--'+name,required=True)
    args=p.parse_args()
    # Evidence restricted to this increment or app/scene_checks, never src/build/old packages.
    root=base.safe.no_links(args.record_root)
    need(root.is_absolute(),'Output must be absolute')
    app=base.safe.no_links(args.app)
    allowed=(HERE/'evidence').resolve(),(app/'scene_checks').resolve()
    need(any(base.safe.under(root,r) for r in allowed),'Evidence root must be increment/evidence or app/scene_checks')
    need(not root.is_symlink(),'Linked evidence path')
    root.mkdir(parents=True,exist_ok=True)
    out=root/(time.strftime('%Y%m%d_%H%M%S')+'_'+args.stage+'_'+uuid.uuid4().hex[:10]);out.mkdir()
    base.safe.write_json(out/'request.json',vars(args))
    try:
        report=verify(args,out)
        report['status']={'pre':'S1_PRECHECK_ONLY','post':'S1_ARTIFACT_PASS_NOT_LOAD_NOT_BOARD','load':'S1_LOAD_PREFLIGHT_PASS_NOT_BOARD'}[args.stage]
        base.safe.write_json(out/'result.json',report);print(report['status']+' '+str(out));return 0
    except Exception as exc:
        base.safe.write_json(out/'failure.json',dict(status='REJECTED',error=str(exc)))
        print('REJECTED '+str(exc)+' EVIDENCE='+str(out),file=sys.stderr);return 1

if __name__=='__main__':sys.exit(main())
