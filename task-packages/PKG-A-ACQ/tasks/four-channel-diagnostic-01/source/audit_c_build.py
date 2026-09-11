"""Post-build audit of the actual project, unchanged components and BSP contract."""
import argparse
import csv
import hashlib
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def hardware(xsa):
    with zipfile.ZipFile(xsa) as z:
        names=[n for n in z.namelist() if n.endswith('.hwh')]
        roots=[ET.fromstring(z.read(n)) for n in names]
        roots=[r for r in roots if any(m.get('INSTANCE')=='processing_system7_0' for m in r.iter('MODULE'))]
        assert len(roots)==1, names
        root=roots[0]
    result={}
    for m in root.iter('MODULE'):
        if m.get('INSTANCE') in ('processing_system7_0','axi_dma_0','axi_gpio_0'):
            result[m.get('INSTANCE')]={p.get('NAME'):p.get('VALUE') for p in m.findall('./PARAMETERS/PARAMETER')}
    assert len(result)==3
    return result

def audit(task,one,build,ps,bsp_xsa):
    backup=task/'recovery/before-c-adapter-20260911'
    bd_rel=Path('one.srcs/sources_1/bd/system/system.bd')
    before=json.loads((backup/'one'/bd_rel).read_text())['design']
    after=json.loads((one/bd_rel).read_text())['design']
    checks={}
    preserved=[k for k in before['components'] if k!='single_mic_top_0']
    checks['preserved_components']={k:before['components'][k]==after['components'][k] for k in preserved}
    assert all(checks['preserved_components'].values())
    assert before.get('addressing')==after.get('addressing')
    checks['addressing_unchanged']=True
    assert 'single_mic_top_0' not in after['components'] and 'four_mic_top_0' in after['components']
    assert 'pdm_clk' not in after['ports']
    checks['unchanged_sources']={}
    for relative in ('rtl/pdm_cic3.v','rtl/pcm4_capture_axis.v','export_four.py','test_export.py'):
        checks['unchanged_sources'][relative]=sha(task/'source'/relative)==sha(backup/'source'/relative)
    assert all(checks['unchanged_sources'].values())
    mapping=json.loads((task/'source/c_adapter_mapping.json').read_text())
    xdc=one/'one.srcs/sources_1/imports/c_adapter/c_adapter_io.xdc'
    text=xdc.read_text()
    io=(build/'io.rpt').read_text(errors='replace')
    for ch in mapping['channels']:
        for role in ('clock','data'):
            port,ball=ch[role+'_port'],ch[role+'_ball']
            assert f'PACKAGE_PIN {ball} [get_ports '+('{'+port+'}' if '[' in port else port)+']' in text
            matching=[line for line in io.splitlines() if re.search(r'\|\s*'+re.escape(port)+r'\s*\|',line)]
            assert len(matching)==1 and re.search(r'\|\s*'+ball+r'\s*\|',matching[0]) and 'LVCMOS33' in matching[0],(port,matching)
    checks['implemented_io_matches_mapping']=True
    with (build/'clock-registers.tsv').open() as f:
        drivers=list(csv.DictReader(f,delimiter='\t'))
    assert len(drivers)==4
    assert {r['port'] for r in drivers}=={'pdm_clk1','pdm_clk2','pdm_clk3','pdm_clk4'}
    controls=('primitive','INIT','C','D','CE','R','S')
    assert len({tuple(r[k] for k in controls) for r in drivers})==1,drivers
    checks['clock_registers_same_C_D_CE_reset_INIT']=drivers
    checks['clock_scope']='Vivado replicated output FFs, one logical divider/state. No physical zero-skew claim.'
    xsa=build/'system_c_adapter.xsa'
    oldhw,newhw=hardware(bsp_xsa),hardware(xsa)
    diffs={m:{k:[oldhw[m].get(k),newhw[m].get(k)] for k in oldhw[m].keys()|newhw[m].keys() if oldhw[m].get(k)!=newhw[m].get(k)} for m in oldhw}
    checks['bsp_hardware_parameter_differences']=diffs
    assert not any(diffs.values()),diffs
    map_text=(ps/'four_mic_capture.map').read_text(errors='replace')
    end=int(re.search(r'0x([0-9a-fA-F]+)\s+end = \.',map_text)[1],16)
    assert end<0x01000000 and 0x01000000+1024000+64<=0x01100000
    checks['program_end_hex']=f'{end:08X}'
    checks['rx_data_guard_end_hex']=f'{0x01000000+1024000+64:08X}'
    checks['result']='STRUCTURAL_BSP_IO_AUDIT_PASS_NOT_BOARD_TEST'
    artifacts=[xsa,build/'system_c_adapter.bit',ps/'four_mic_capture.elf',ps/'four_mic_capture.map',one/bd_rel,xdc,bsp_xsa]
    artifacts+=list((task/'source').rglob('*.v'))+[task/'source/ps/main_four_capture.c',task/'source/export_four.py',task/'source/c_adapter_mapping.json']
    checks['sha256']={str(p):sha(p) for p in artifacts}
    return checks

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('task','one','build','ps','bsp_xsa','output'):parser.add_argument(name,type=Path)
    a=parser.parse_args()
    result=audit(a.task,a.one,a.build,a.ps,a.bsp_xsa)
    with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
    print(result['result'])
