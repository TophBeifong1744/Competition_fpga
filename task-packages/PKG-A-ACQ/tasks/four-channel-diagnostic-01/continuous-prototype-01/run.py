"""Independent candidate: fresh-output-only simulation, C model test and build.
Reuse current_build's safe dependency/snapshot/ELF helpers, NOT its old PS gate.
"""
from pathlib import Path
import argparse, hashlib, json, os, re, shutil, struct, sys, traceback, zipfile
import xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
KNOWN_PS={
    'main_continuous.c':'b9fffdf20c5704d75505890148f0c2b758b77fd94f5848503d4f3080880cf88f',
    'continuous_core.c':'29feb369f255c31dce423f5301996ecb52f95124a9705978a95c2ddd6eb2e9e3',
    'continuous_core.h':'2b2a8e0034970403ea693181950a6cec99b51802579e5693f1fdaa110fddbbc3',
}
sys.path.insert(0,str(HERE.parent/'current_build'))
import build_current as safe
from ps_contract import Elf32

def write(path,obj): safe.write_json(path,obj)
def run(argv,out,name,cwd=None):
    for arg in argv:safe.require(not re.search(r'[\r\n"&|<>^%!]',str(arg)),f'Unsupported command character: {arg}')
    return safe.run_command(argv,out,name,cwd)
def copy(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    safe.require(not dst.exists(),f'Refuse overwrite: {dst}')
    shutil.copyfile(src,dst)
def fresh(path):
    safe.require(not re.search(r'[\r\n"&|<>^%!]',str(path)),'Unsupported output path character')
    out=safe.output_path(path,[HERE/'rtl',HERE/'ps',HERE/'sim',HERE/'tests',HERE/'run.py'])
    out.mkdir();return out
def manifest(out):
    write(out/'SHA256.json',{p.relative_to(out).as_posix():safe.sha(p) for p in out.rglob('*') if p.is_file() and p.name!='SHA256.json'})
def sim(args):
    for tool in ('xvlog.bat','xelab.bat','xsim.bat'):safe.need_tool(Path(args.vivado_bin)/tool)
    safe.need_file(args.cic)
    out=fresh(args.output)
    for p in (HERE/'rtl').glob('*.v'):copy(p,out/p.name)
    copy(safe.need_file(args.cic),out/'pdm_cic3.v')
    for p in (HERE/'sim').glob('*.sv'):copy(p,out/p.name)
    tools=Path(args.vivado_bin)
    try:
        run([tools/'xvlog.bat','--sv','pcm4_continuous_axis.v','four_mic_top.v','pdm_cic3.v','tb_continuous.sv','tb_frontend.sv'],out,'compile')
        run([tools/'xelab.bat','tb_continuous','-s','tb_continuous_sim','-debug','typical'],out,'elaborate')
        log=run([tools/'xsim.bat','tb_continuous_sim','-runall'],out,'simulate')
        safe.require('RTL_CONTINUOUS_PASS' in log and 'FAIL ' not in log,'RTL test failed')
        run([tools/'xelab.bat','tb_production','-s','tb_production_sim','-debug','typical'],out,'production-elaborate')
        log=run([tools/'xsim.bat','tb_production_sim','-runall'],out,'production-simulate')
        safe.require('RTL_CONTINUOUS_PASS packet=250 fifo=1024' in log and 'FAIL ' not in log,'production packet test failed')
        run([tools/'xelab.bat','tb_frontend','-s','tb_frontend_sim','-debug','typical'],out,'frontend-elaborate')
        log=run([tools/'xsim.bat','tb_frontend_sim','-runall'],out,'frontend-simulate')
        safe.require('FRONTEND_REGRESSION_PASS' in log,'frontend test failed')
        write(out/'result.json',{'status':'RTL_SIM_PASS_NOT_BOARD','checks':'see raw log'})
    except Exception as e:
        write(out/'failure.json',{'error':str(e)});raise
    finally:manifest(out)

def host(args):
    safe.need_tool(args.host_gcc)
    out=fresh(args.output)
    for p in (HERE/'ps').glob('continuous_core.*'):copy(p,out/p.name)
    copy(HERE/'tests/test_core.c',out/'test_core.c')
    try:
        run([safe.need_tool(args.host_gcc),'-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I.','continuous_core.c','test_core.c','-o','test_core.exe'],out,'compile')
        log=run([out/'test_core.exe'],out,'test')
        safe.require('PS_CORE_MODEL_PASS' in log,'Missing host test marker')
        write(out/'result.json',{'status':'PS_MODEL_PASS_NOT_HARDWARE_CACHE_TEST'})
    except Exception as e:write(out/'failure.json',{'error':str(e)});raise
    finally:manifest(out)

def symbol(elf,name):
    s=elf.symbols[name];section=elf.sections[s[5]]
    offset=s[1]-section[3];return elf.section_data(s[5])[offset:offset+s[2]]

def known_ps(folder):
    for name,wanted in KNOWN_PS.items():
        safe.require(safe.sha(folder/name)==wanted,'Unknown PS source body/configuration: '+name)

def compile_ps(plan,out):
    work=out/'ps';work.mkdir()
    for p in (HERE/'ps').glob('*'):copy(p,work/p.name)
    known_ps(work)
    copy(out/'inputs/ps/lscript.ld',work/'lscript.ld')
    # One translation unit: metadata and executed expressions see identical macros.
    (work/'unit.c').write_text('#include "continuous_core.c"\n#include "main_continuous.c"\n',encoding='utf-8')
    common=[plan['gcc'],'-DSDT','-mcpu=cortex-a9','-mfpu=vfpv3','-mfloat-abi=hard','-std=c11','-Wall','-Wextra','-Werror','-O2','-g3','-specs=../inputs/bsp/Xilinx.spec','-I../inputs/bsp/include']
    run(common+['-E','unit.c','-o','unit.i'],out,'ps-preprocess',work)
    run(common+['-x','cpp-output','-c','unit.i','-o','unit.o'],out,'ps-compile',work)
    run(common+['unit.o','-o','four_mic_continuous.elf','-L../inputs/bsp/lib','-Wl,-T,lscript.ld','-Wl,-Map,memory.map,--cref','-Wl,--start-group','-lxilstandalone','-lxiltimer','-lxil','-lgcc','-lc','-Wl,--end-group'],out,'ps-link',work)
    obj=Elf32(work/'unit.o',1);exe=Elf32(work/'four_mic_continuous.elf',2)
    raw=symbol(obj,'continuous_contract')
    safe.require(raw==symbol(exe,'continuous_contract'),'object/ELF contract mismatch')
    c=struct.unpack('<16I',raw)
    safe.require(c[:10]==(0x434f4e31,0x01000000,0x01100000,250,8,8000,64,8064,2,16128),'unsupported compiled contract')
    safe.require(c[14:]==(10000000,480000),'10s duration contract')
    safe.require(c[10]<=c[1] and c[2]-1<=c[11] and c[1]+c[9]<=c[2],'DDR bounds')
    for r in exe.allocated+exe.loads:
        safe.require(r['end']<=c[1] or r['start']>=c[2],f'program/RX overlap {r}')
    safe.require(exe.symbol_value('end')<=c[1],'end overlaps RX')
    bd=json.loads((out/'inputs/project/one.srcs/sources_1/bd/system/system.bd').read_text())['design']
    params=bd['components']['four_mic_top_0']['parameters']
    safe.require(params['SAMPLES_PER_PACKET']['value']==str(c[3]),'BD packet mismatch')
    safe.require(params['FIFO_LOG2']['value']=='10' and params['WARMUP_SAMPLES']['value']=='4096','frontend mismatch')
    report={'status':'COMPILED_PS_CONTRACT_PASS_NOT_BOARD','known_source_sha256':KNOWN_PS,'compiled_values':list(c),'slot_ranges':[
        {'data_start':hex(c[1]+i*c[7]),'data_end':hex(c[1]+i*c[7]+c[5]),'guard_end':hex(c[1]+(i+1)*c[7])} for i in range(2)],
        'allocated_ranges':exe.allocated+exe.loads,'end':hex(exe.symbol_value('end')),'optimization':'-O2','same_preprocessed_TU':True}
    write(work/'contract-result.json',report)
    return report

def driver_binding(xsa):
    with zipfile.ZipFile(xsa) as z:
        root=ET.fromstring(z.read('system.hwh'))
        values={}
        for m in root.findall('./MODULES/MODULE'):
            if m.get('INSTANCE') not in ('processing_system7_0','axi_dma_0','axi_gpio_0','clk_wiz_0'):continue
            par={n.get('NAME'):n.get('VALUE') for n in m.findall('./PARAMETERS/PARAMETER')}
            if par.get('PCW_USE_CROSS_TRIGGER')=='0':
                for k in par:
                    if k.startswith(('PCW_FTM_CTI_IN','PCW_FTM_CTI_OUT')) and par[k] in ('<Select>','DISABLED'):par[k]='DISABLED'
            values[m.get('INSTANCE')]={'vlnv':m.get('VLNV'),'parameters':par,
                'addresses':[dict(n.attrib) for n in m.findall('.//MEMRANGE')]}
        safe.require(len(values)==4,'missing BSP hardware modules')
        return {'modules':values,'ps7_init.c':hashlib.sha256(z.read('ps7_init.c')).hexdigest()}

def build(args):
    # approved original gate only validates/snapshots the UNMODIFIED baseline.
    plan=safe.preflight(args)
    if args.mode=='check':print(json.dumps(plan,indent=2));return
    out=Path(plan['output']);out.mkdir()
    write(out/'preflight.json',plan)
    try:
        project=safe.stage(plan,out)
        # Candidate source snapshots, no modification of original/current_build.
        snap=out/'candidate';snap.mkdir()
        for folder in ('rtl','ps','sim','tests'):
            for p in (HERE/folder).glob('*'):
                if p.is_file():copy(p,snap/folder/p.name)
        copy(HERE/'run.py',snap/'run.py')
        currenttop=project.parent/'one.srcs/sources_1/imports/c_adapter/four_mic_top.v'
        before=currenttop.read_text();after=(snap/'rtl/four_mic_top.v').read_text()
        # Entire divider/synchronizer/warmup/ID/four CIC instantiation block unchanged.
        extract=lambda s:s[s.index('    // C adapter:'):s.index('    pcm4_')]
        safe.require(extract(before)==extract(after),'frontend changed')
        copy(currenttop,out/'baseline_four_mic_top.v')
        shutil.copyfile(snap/'rtl/four_mic_top.v',currenttop)
        copy(snap/'rtl/pcm4_continuous_axis.v',currenttop.parent/'pcm4_continuous_axis.v')
        compile_ps(plan,out)
        if args.mode=='ps-check':
            write(out/'result.json',{'status':'PS_COMPILE_PASS_HW_NOT_BUILT','unchanged':safe.unchanged(plan)})
            return
        template=(HERE.parent/'current_build/build_hw.tcl').read_text()
        insertion='''# C1 adaptation occurs ONLY inside checked copied project.
set old [get_files -quiet */pcm4_capture_axis.v]
if {[llength $old]} {remove_files $old}
add_files -norecurse [list "$root/inputs/project/one.srcs/sources_1/imports/c_adapter/pcm4_continuous_axis.v"]
update_compile_order -fileset sources_1
update_module_reference -verbose [get_ips -all *four_mic_top*]
set startpin [get_bd_pins four_mic_top_0/start]
disconnect_bd_net [get_bd_nets -of_objects $startpin] $startpin
connect_bd_net [get_bd_pins axi_gpio_0/gpio_io_o] $startpin
save_bd_design
'''
        template=template.replace('# Do not change design settings or save BD; generate only products of current inputs.',insertion)
        template=template.replace('system_c_adapter.xsa','system_continuous.xsa').replace('system_c_adapter.bit','system_continuous.bit')
        # Direct project-mode commands avoid Windows Script Host runme.bat.
        # Same generated BD, active XDC, part and default synthesis settings.
        start=template.index('set_property AUTO_INCREMENTAL_CHECKPOINT')
        end=template.index('set blackboxes',start)
        template=template[:start]+'''synth_design -top system_wrapper -part xc7z020clg400-2
write_checkpoint "$root/artifacts/hw/post_synth.dcp"
putfile "$root/reports/synth-status.txt" "DIRECT_SYNTH_FINISHED"
'''+template[end:]
        start=template.index('close_design\n')
        end=template.index('report_timing_summary',start)
        template=template[:start]+'''opt_design
place_design
route_design
write_checkpoint "$root/artifacts/hw/post_route.dcp"
putfile "$root/reports/impl-status.txt" "DIRECT_ROUTE_FINISHED"
'''+template[end:]
        start=template.index('write_hw_platform -fixed')
        end=template.index('close_project',start)
        template=template[:start]+'''write_bitstream "$root/artifacts/hw/system_continuous.bit"
write_hw_platform -fixed "$root/artifacts/hw/system_continuous.xsa"
'''+template[end:]
        # Read-only installation package path, inherited by this process' child
        # Vivado runs only. No change to global TclStore/user initialization.
        support=(Path(plan['vivado']).parent.parent/'data/XilinxTclStore/support').resolve(strict=True)
        paths=sorted({p.parent for p in support.parent.rglob('pkgIndex.tcl')})
        for folder in paths:safe.need_file(folder/'pkgIndex.tcl')
        os.environ['TCLLIBPATH']=' '.join('{'+p.as_posix()+'}' for p in paths)
        write(out/'tool-environment.json',{'TCLLIBPATH':os.environ['TCLLIBPATH'],'scope':'this invocation and children only','package_sha256':{str(p/'pkgIndex.tcl'):safe.sha(p/'pkgIndex.tcl') for p in paths}})
        (out/'build_hw.tcl').write_text(template,encoding='utf-8')
        run([plan['vivado'],'-mode','batch','-source','build_hw.tcl','-log','vivado.log','-nojournal','-tclargs',out.as_posix(),project.as_posix(),args.jobs],out,'vivado')
        timing=safe.timing_summary_values((out/'reports/timing-summary.rpt').read_text())
        safe.require(all(v>=0 for v in timing.values()),'timing violation')
        base=driver_binding(out/'inputs/bsp-reference.xsa');new=driver_binding(out/'artifacts/hw/system_continuous.xsa')
        write(out/'reports/bsp-binding.json',{'baseline':base,'candidate':new,'equal':base==new})
        safe.require(base==new,'BSP-relevant hardware changed')
        with zipfile.ZipFile(out/'artifacts/hw/system_continuous.xsa') as z:
            (out/'artifacts/hw/ps7_init.tcl').write_bytes(z.read('ps7_init.tcl'))
        copy(out/'ps/four_mic_continuous.elf',out/'artifacts/ps/four_mic_continuous.elf')
        copy(out/'ps/memory.map',out/'artifacts/ps/memory.map')
        safe.require(not safe.unchanged(plan),'original inputs changed during build')
        write(out/'result.json',{'status':'CANDIDATE_BUILD_PASS_NOT_BOARD','timing':timing,'original_unchanged':True,'XSA_includes_bit':False,'BSP':'unchanged PS/DMA/GPIO/clock configuration; reused original BSP','board':'NOT_EXECUTED'})
    except Exception as e:
        write(out/'failure.json',{'error':str(e),'traceback':traceback.format_exc()});raise
    finally:
        write(out/'original-integrity.json',{'changed':safe.unchanged(plan)})
        manifest(out)

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['check','ps-check','build','sim','host'])
    p.add_argument('--output',required=True)
    for name in ('project','vivado','gcc','bsp','bsp-xsa','ps-source','vivado-bin','cic','host-gcc'):p.add_argument('--'+name)
    p.add_argument('--jobs',type=int,default=4)
    a=p.parse_args()
    needed={'sim':('vivado_bin','cic'),'host':('host_gcc',)}.get(a.mode,('project','vivado','gcc','bsp','bsp_xsa','ps_source'))
    missing=[n for n in needed if not getattr(a,n)]
    if missing:p.error('missing dependencies: '+', '.join('--'+n.replace('_','-') for n in missing))
    {'sim':sim,'host':host}.get(a.mode,build)(a)
if __name__=='__main__':main()
