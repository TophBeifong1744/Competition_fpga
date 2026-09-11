"""Snapshot current local build evidence without rebuilding or touching one/Vitis."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--one', type=Path, required=True)
    p.add_argument('--vitis', type=Path, required=True)
    p.add_argument('--task', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    app = a.vitis/'four_mic_capture'
    platform = a.vitis/'c_adapter_platform'
    source = a.one/'one.srcs/sources_1'
    paths = {
        'one/one.xpr':a.one/'one.xpr',
        'one/system.bd':source/'bd/system/system.bd',
        'one/system_c_adapter.xsa':a.one/'system_c_adapter.xsa',
        'one/system_wrapper.bit':a.one/'one.runs/impl_1/system_wrapper.bit',
        'one/timing_summary.rpt':a.one/'one.runs/impl_1/system_wrapper_timing_summary_routed.rpt',
        'one/four_mic_top.v':source/'imports/c_adapter/four_mic_top.v',
        'one/pcm4_capture_axis.v':source/'imports/four_mic/pcm4_capture_axis.v',
        'one/pdm_cic3.v':source/'imports/rtl/pdm_cic3.v',
        'one/effective_c_adapter_io.xdc':a.one/'one.srcs/constrs_1/imports/c_adapter/c_adapter_io.xdc',
        'platform/vitis-comp.json':platform/'vitis-comp.json',
        'platform/system_c_adapter.xsa':platform/'hw/system_c_adapter.xsa',
        'platform/xparameters.h':platform/'ps7_cortexa9_0/standalone_ps7_cortexa9_0/bsp/include/xparameters.h',
        'app/vitis-comp.json':app/'vitis-comp.json',
        'app/launch.json':app/'_ide/launch.json',
        'app/main_four_capture.c':app/'src/main_four_capture.c',
        'app/lscript.ld':app/'src/lscript.ld',
        'app/four_mic_capture.elf':app/'build/four_mic_capture.elf',
        'app/memory.map':app/'build/memory.map',
        'app/compile_commands.json':app/'build/compile_commands.json',
        'app/loaded_path.bit':app/'_ide/bitstream/system_c_adapter.bit',
        'app/ps7_init.tcl':app/'_ide/psinit/ps7_init.tcl',
    }
    manifest = {}
    for name,path in paths.items():
        dest = a.output/name
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,dest)
        assert sha(path) == sha(dest), name
        manifest[name] = {'source_path':str(path), 'sha256':sha(dest), 'bytes':dest.stat().st_size,
                          'source_mtime_ns':path.stat().st_mtime_ns}
    checks = {}
    with zipfile.ZipFile(a.output/'one/system_c_adapter.xsa') as z:
        bits = [n for n in z.namelist() if n.endswith('.bit')]
        assert len(bits) == 1
        bit_sha = hashlib.sha256(z.read(bits[0])).hexdigest()
        checks['xsa_embedded_bit_sha256'] = bit_sha
        checks['xsa_bit_matches_impl_and_launch'] = all(
            manifest[n]['sha256'] == bit_sha for n in ('one/system_wrapper.bit','app/loaded_path.bit'))
        init_sha = hashlib.sha256(z.read('ps7_init.tcl')).hexdigest()
        checks['psinit_matches_xsa'] = init_sha == manifest['app/ps7_init.tcl']['sha256']
        root = ET.fromstring(z.read('system.hwh'))
        checks['hwh_parameters'] = {m.get('INSTANCE'):{v.get('NAME'):v.get('VALUE')
            for v in m.findall('./PARAMETERS/PARAMETER')} for m in root.iter('MODULE')
            if m.get('INSTANCE') in ('axi_dma_0','axi_gpio_0','four_mic_top_0','clk_wiz_0')}
    checks['one_xsa_matches_platform_xsa'] = manifest['one/system_c_adapter.xsa']['sha256'] == manifest['platform/system_c_adapter.xsa']['sha256']
    elf = (a.output/'app/four_mic_capture.elf').read_bytes()
    checks['elf_contains_log_build_stamp'] = b'Sep 11 2026' in elf and b'18:23:59' in elf
    map_text = (a.output/'app/memory.map').read_text()
    end = int(re.search(r'0x([\da-fA-F]+)\s+end = \.',map_text)[1],16)
    checks['program_end_hex'] = f'{end:08X}'
    checks['program_end_matches_serial_and_safe_buffer'] = end == 0x00112630 and end < 0x01000000 and 0x01000000+1024000+64 <= 0x01100000
    checks['source_comparisons'] = {}
    pairs = {'one/four_mic_top.v':'rtl/four_mic_top.v',
             'one/pcm4_capture_axis.v':'rtl/pcm4_capture_axis.v',
             'one/pdm_cic3.v':'rtl/pdm_cic3.v',
             'app/main_four_capture.c':'ps/main_four_capture.c',
             'one/effective_c_adapter_io.xdc':'four_mic_io.xdc'}
    for name,relative in pairs.items():
        original = a.task/'source'/relative
        snapshot = a.output/name
        checks['source_comparisons'][name] = {
            'task_source':str(original), 'task_sha256':sha(original),
            'byte_equal':sha(original) == sha(snapshot),
            'text_equal_normalized_newlines':original.read_text() == snapshot.read_text()}
    checks['scope'] = 'Current disk artifacts and launch configuration, corroborated by operator declaration and matching ELF/UART stamp; not a retrospective cryptographic measurement of FPGA state.'
    checks['status'] = 'CURRENT_BUILD_PROVENANCE_CHECKED'
    (a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (a.output/'checks.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in checks.items() if k != 'hwh_parameters'},indent=2))


if __name__ == '__main__':
    main()
