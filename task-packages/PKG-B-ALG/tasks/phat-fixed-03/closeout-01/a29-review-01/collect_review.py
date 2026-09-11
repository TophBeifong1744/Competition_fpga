"""Collect B replay evidence only; do not redistribute generated vendor HDL/DCP."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import numpy as np

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def util(text,label):
    return float(re.search(r'\|\s*'+re.escape(label)+r'\*?\s*\|\s*([0-9.]+)',text).group(1))

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True)
    p.add_argument('--a-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args(); assert not a.out.exists()
    pkg=a.a_root/'task-packages/PKG-A-ACQ/tasks/fft29-bitexact-budget-01'
    project=a.run/'project'; a.out.mkdir(parents=True)
    for f in a.run.iterdir():
        if f.is_file(): shutil.copyfile(f,a.out/f.name)
    shutil.copytree(a.run/'vectors',a.out/'vectors')
    shutil.copytree(a.run/'simulation-archive',a.out/'simulation')
    reports=a.out/'reports';reports.mkdir()
    for pattern in ['*.rpt','tool-version.txt','ip-properties.txt']:
        for f in project.glob(pattern): shutil.copyfile(f,reports/f.name)
    xci=project/'fft29_budget.srcs/sources_1/ip/ss_fft29/ss_fft29.xci'
    shutil.copyfile(xci,reports/'ss_fft29.xci')
    shutil.copyfile(project/'fft29_budget.runs/ss_fft29_synth_1/runme.log',reports/'synth-runme.log')
    reference=json.loads((pkg/'evidence/run01/reports/resource-summary.json').read_bytes())
    resource={}
    for stage,key in [('synth','OOC_synthesis'),('route','OOC_placed_and_routed_core')]:
        txt=(reports/f'{stage}-utilization.rpt').read_text()
        assert 'xc7z020clg400-2' in txt and '2025.2' in txt
        rr={k:util(txt,label) for k,label in [('LUT','Slice LUTs'),('FF','Slice Registers'),('DSP48E1','DSPs'),('RAMB18E1','RAMB18'),('RAMB36','RAMB36/FIFO'),('BRAM_tiles','Block RAM Tile')]}
        timing=(reports/f'{stage}-timing.rpt').read_text().splitlines()
        idx=next(i for i,line in enumerate(timing) if 'WNS(ns)' in line)
        numbers=timing[idx+2].split()
        rr.update(WNS_ns=float(numbers[0]),TNS_ns=float(numbers[1]),WHS_ns=float(numbers[4]),THS_ns=float(numbers[5]))
        rr['differences_from_A']={k:dict(A=reference[key][k],B=v) for k,v in list(rr.items()) if k in reference[key] and v!=reference[key][k]}
        resource[stage]=rr
    current=json.loads(xci.read_bytes())['ip_inst']; old=json.loads((pkg/'evidence/run01/reports/ss_fft29.xci').read_bytes())['ip_inst']
    # Machine/path metadata may differ; compare all component configuration values.
    def cfg(j): return {k:[r['value'] for r in v] for k,v in j['parameters']['component_parameters'].items()}
    assert cfg(current)==cfg(old)
    assert current['ip_revision']==old['ip_revision']=='15'
    timing_check=(reports/'route-check-timing.rpt').read_text()
    for flag,count in [('unconstrained_internal_endpoints',0),('no_input_delay',85),('no_output_delay',88)]:
        assert f'checking {flag} ({count})' in timing_check
    route=(reports/'route-status.rpt').read_text()
    assert re.search(r'# of fully routed nets\.+\s*:\s*2701',route)
    assert re.search(r'# of nets with routing errors\.+\s*:\s*0',route)
    clocks=(reports/'synth-clocks.rpt').read_text()
    assert re.search(r'aclk\s+10\.000',clocks)
    compare=json.loads((a.out/'check.json').read_bytes())
    assert compare['pass'] and compare['integer_components']==739328 and compare['mismatched_components']==0
    original=json.loads((pkg/'evidence/run01/check.json').read_bytes())
    assert compare==original, 'Record actual difference before claiming exact replay'
    bytes_checks={}
    numeric_checks={}
    for name in ['outputs.csv','cycles.csv','status.csv']:
        b=gzip.decompress((a.out/'simulation'/f'{name}.gz').read_bytes())
        ar=gzip.decompress((pkg/'evidence/run01/simulation'/f'{name}.gz').read_bytes())
        bytes_checks[name]=dict(A_sha256=hashlib.sha256(ar).hexdigest(),B_sha256=hashlib.sha256(b).hexdigest(),equal=b==ar)
        import io
        aa=np.loadtxt(io.BytesIO(ar),delimiter=',',dtype=np.int64)
        bb=np.loadtxt(io.BytesIO(b),delimiter=',',dtype=np.int64)
        numeric_checks[name]=bool(np.array_equal(aa,bb));assert numeric_checks[name]
    summary=dict(status='B_NEW_SELECTED_FFT29_REPLAY_AND_OOC_CORE_EVIDENCE',
        A_commit='c0b5f8fb44643e81d8c4e6f0be457dddeae9758e',resources=resource,
        XCI_component_parameters_equal=True,integer_and_cycle_records_equal=numeric_checks,
        clock_period_ns=10,fully_routed_nets=2701,internal_unconstrained_endpoints=0,
        ports_without_input_delay=85,ports_without_output_delay=88,
        original_csv_bytes=bytes_checks,check_json_equal=True,covered_frames=60,remaining_frames=136,
        adapter_RTL_tested=False,IFFT29_tested=False,board_tested=False,
        files={f.relative_to(a.out).as_posix():sha(f) for f in sorted(a.out.rglob('*')) if f.is_file()})
    (a.out/'B-replay-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['files','original_csv_bytes']},indent=2))

if __name__=='__main__':main()
