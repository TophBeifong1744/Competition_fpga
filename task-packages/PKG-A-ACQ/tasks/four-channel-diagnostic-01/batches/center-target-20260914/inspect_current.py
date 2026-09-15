"""Read-only hardware/software inspection; writes a fresh evidence directory only."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import traceback
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent
TASK = ROOT.parents[1]
REPO = TASK.parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--vitis-workspace', type=Path, required=True)
    p.add_argument('--vivado', type=Path, required=True)
    p.add_argument('--gcc', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    if not out.is_relative_to(ROOT) or out == ROOT:
        p.error('Output must be a new child of this batch')
    out.mkdir(parents=True, exist_ok=False)
    report = {'created_utc':datetime.now(timezone.utc).isoformat(), 'scope':'disk checks only, not new build or board result',
              'sources':{}, 'loading':{}, 'active_project_files':[]}
    try:
        (out/'snapshot').mkdir()
        old = json.loads((TASK/'batches/c-adapter-first-20260913/delivery-01/versions/loading-record.json').read_text(encoding='utf-8'))
        app = a.vitis_workspace/'four_mic_capture'
        platform = a.vitis_workspace/'c_adapter_platform/export/c_adapter_platform'
        loading = {'system_c_adapter.bit':app/'_ide/bitstream/system_c_adapter.bit',
                   'four_mic_capture.elf':app/'build/four_mic_capture.elf',
                   'ps7_init.tcl':app/'_ide/psinit/ps7_init.tcl',
                   'system_c_adapter.xsa':platform/'hw/system_c_adapter.xsa',
                   'launch.json':app/'_ide/launch.json',
                   'main_four_capture.c':app/'src/main_four_capture.c',
                   'lscript.ld':app/'src/lscript.ld', 'memory.map':app/'build/memory.map'}
        for name,path in loading.items():
            digest = sha(path)
            report['loading'][name] = {'path':str(path), 'sha256':digest,
                'same_as_previous_checked_capture':digest == old['files'][name]['sha256']}
            if digest != old['files'][name]['sha256']:
                raise ValueError(f'Loading input changed; do not assume prior pairing: {name}')
        with zipfile.ZipFile(loading['system_c_adapter.xsa']) as z:
            for ending,key in [('.bit','system_c_adapter.bit'),('ps7_init.tcl','ps7_init.tcl')]:
                entries = [n for n in z.namelist() if n.endswith(ending)]
                if len(entries) != 1 or hashlib.sha256(z.read(entries[0])).hexdigest() != report['loading'][key]['sha256']:
                    raise ValueError('XSA and loading files mismatch')
        registered = ET.parse(a.project).getroot().findall('.//FileSet[@Name="sources_1"]/File')
        project_sources = {}
        for item in registered:
            raw = item.get('Path')
            path = Path(raw.replace('$PSRCDIR',str(a.project.parent/'one.srcs')).replace('$PPRDIR',str(a.project.parent)))
            if path.name in ('four_mic_top.v','pcm4_capture_axis.v','pdm_cic3.v','system.bd'):
                if path.name in project_sources:
                    raise ValueError('Ambiguous active file: '+path.name)
                project_sources[path.name] = path
                report['active_project_files'].append(str(path))
        if set(project_sources) != {'four_mic_top.v','pcm4_capture_axis.v','pdm_cic3.v','system.bd'}:
            raise ValueError('Missing current project files')
        project_sources['effective_c_adapter_io.xdc'] = a.project.parent/'one.srcs/constrs_1/imports/c_adapter/c_adapter_io.xdc'
        sources = {**project_sources,'one.xpr':a.project,
                   **{k:v for k,v in loading.items() if k.endswith(('.c','.ld','.map','.json','.tcl'))},
                   'export_four.py':TASK/'source/export_four.py',
                   'export_c_capture.py':TASK/'source/export_c_capture.py'}
        for name,path in sources.items():
            digest = sha(path)
            shutil.copyfile(path,out/'snapshot'/name)
            if sha(out/'snapshot'/name) != digest:
                raise ValueError('Input changed while copying')
            report['sources'][name] = {'path':str(path),'sha256':digest}
        cmd = [sys.executable,'-B',str(TASK/'current_build/build_current.py'),'check',
               '--project',str(a.project),'--vivado',str(a.vivado),'--gcc',str(a.gcc),
               '--bsp',str(platform/'sw/standalone_ps7_cortexa9_0'),
               '--bsp-xsa',str(loading['system_c_adapter.xsa']), '--ps-source',str(app/'src'),
               '--output',str(out/'unused-build-target')]
        with (out/'current-build-check.log').open('x',encoding='utf-8') as f:
            result = subprocess.run(cmd,cwd=REPO,stdout=f,stderr=subprocess.STDOUT,shell=False)
        report['approved_check_command'] = cmd
        report['approved_check_returncode'] = result.returncode
        if result.returncode:
            raise ValueError('Existing current_build check rejected current inputs')
        check = json.loads((out/'current-build-check.log').read_text(encoding='utf-8'))
        report['approved_check_status'] = check.get('status')
        if report['approved_check_status'] != 'CHECK_PASS_NOT_BUILD' or (out/'unused-build-target').exists():
            raise ValueError('Unexpected check-mode behavior')
        for name,row in report['sources'].items():
            if sha(Path(row['path'])) != row['sha256']:
                raise ValueError('Original changed during inspection: '+name)
        report['ps_contract_scope'] = 'No new compile/link proof; read-only check plus identical previously used ELF/source/map hashes'
        report['status'] = 'DISK_PRECHECK_PASS_NOT_BOARD_TEST'
    except Exception:
        report['status'] = 'DISK_PRECHECK_FAILED'
        (out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf-8')
        raise
    finally:
        (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        hashes = {q.relative_to(out).as_posix():sha(q) for q in sorted(out.rglob('*')) if q.is_file()}
        (out/'SHA256.json').write_text(json.dumps(hashes,indent=2)+'\n',encoding='utf-8')
    print(report['status'])


if __name__ == '__main__':
    main()
