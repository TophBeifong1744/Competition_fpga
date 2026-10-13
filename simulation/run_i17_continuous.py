"""Bounded RTL control/consumer checks and actual-IP continuous entry simulation.

Run: python simulation/run_i17_continuous.py control export full
Outputs: codex_out/i17-continuous-control-20261013/runs/<case>-<attempt>/
Next: hand the exact candidate and native logs to A for existing-project integration.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'docs/evidence/issue19-continuous-control-20261013'
REF = EVIDENCE/'reference'
TOOLS = Path(os.environ.get('I17_VIVADO_ROOT', 'C:/AMDDesignTools/2025.2/Vivado'))
ENV = os.environ.copy()
ENV.update(XILINX_VIVADO=str(TOOLS),RDI_APPROOT=str(TOOLS),HDI_APPROOT=str(TOOLS),
    RDI_OPT_EXT='.o',RDI_DATADIR=str(TOOLS/'data'),RDI_LIBDIR=str(TOOLS/'lib/win64.o'),
    RDI_BINDIR=str(TOOLS/'bin'),RDI_PLATFORM='win64',TCL_LIBRARY=str(TOOLS.parent/'tps/tcl/tcl8.6'),
    PROCESSOR_ARCHITECTURE='AMD64')
ENV['PATH']=';'.join(str(p) for p in [TOOLS/'lib/win64.o',TOOLS/'lib/win64.o/Default',
    TOOLS/'bin/unwrapped/win64.o',TOOLS.parent/'tps/win64/jre21.0.5_11/bin/server',
    TOOLS.parent/'tps/win64/jre21.0.5_11/bin',TOOLS.parent/'tps/mingw/6.2.0/win64.o/nt/bin'])+';'+ENV['PATH']
LIBS=['xil_defaultlib','xbip_utils_v3_0_15','axi_utils_v2_0_11','c_reg_fd_v12_0_11',
    'xbip_dsp48_wrapper_v3_0_7','xbip_pipe_v3_0_11','c_addsub_v12_0_21','c_shift_ram_v12_0_20',
    'mult_gen_v12_0_24','floating_point_v7_1_21','cmpy_v6_0_27','xfft_v9_1_15','secureip','xpm']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def run(case):
    out=ROOT/'codex_out/i17-continuous-control-20261013/runs'
    attempt=1
    while (out/f'{case}-{attempt}').exists():attempt+=1
    folder=out/f'{case}-{attempt}';folder.mkdir(parents=True)
    sources=[ROOT/'project/rtl/c_board/i17_continuous_control.sv',REF/'rtl/signed_angle_map.sv']
    top='tb_i17_continuous_control'
    if case in ('export','canary_export'):
        sources=[ROOT/'project/rtl/c_board/i17_diag_consumer.sv',REF/'rtl/diag_record_bank.sv',REF/'rtl/diag_evidence_store.sv']
        top='tb_i17_diag_consumer'
    elif case=='watchdog':
        sources=[ROOT/'project/rtl/a_frontend/forward_window_manager.sv'];top='tb_i17_progress_watchdog'
    elif case in ('full','full_stop','full_stall','full_probe','full_first','full_noise'):
        top={'full_first':'tb_i17_continuous_first','full_noise':'tb_i17_continuous_noise'}.get(case,'tb_i17_continuous_top')
        sources=sorted((REF/'rtl').glob('*'),key=lambda p:(p.name!='doa_math_pkg.sv',p.name))
        sources += [ROOT/p for p in json.loads((EVIDENCE/'candidate-files.json').read_text())['rtl']]
        (folder/'xsim.ini').write_bytes((REF/'xsim.ini').read_bytes())
        (folder/'official.prj').write_text(''.join(f'vhdl xil_defaultlib "{REF/"official"/n}"\n' for n in ('ss_fft29.vhd','ss_ifft25.vhd'))+'nosort\n')
    sources.append(ROOT/'simulation/tb/c_board'/f'{top}.sv')
    frozen=[]
    for p in sources:
        target=folder/'sources'/p.name;target.parent.mkdir(exist_ok=True);target.write_bytes(p.read_bytes());frozen.append(target)
    manifest={'case':case,'scope':'RTL bounded control evidence; not STA/board/PYNQ acceptance',
              'tool':'Vivado XSim 2025.2','cwd':str(folder),'sources':{str(p):sha(p) for p in sources},'stages':[]}
    (folder/'run.json').write_text(json.dumps(manifest,indent=2))
    def stage(tool,args):
        cmd=[str(TOOLS/'bin/unwrapped/win64.o'/f'{tool}.exe'),*map(str,args)]
        begin=time.monotonic()
        # 文件输出防止超时后遗留子进程持有PIPE；只终止本次启动的进程树。
        timed_out=False
        with (folder/f'{tool}-stdout.log').open('wb') as stream:
            proc=subprocess.Popen(cmd,cwd=folder,env=ENV,stdout=stream,stderr=subprocess.STDOUT)
            try:proc.wait(timeout=1800 if case=='full_probe' else 7200 if case.startswith('full') else 600)
            except subprocess.TimeoutExpired:
                timed_out=True
                subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],stdout=stream,stderr=subprocess.STDOUT)
                proc.wait(timeout=30)
        log=(folder/f'{tool}-stdout.log').read_text(encoding='utf-8',errors='replace')
        bad=timed_out or bool(re.search(r'(?m)^(ERROR:|Fatal:|FATAL_ERROR:)',log))
        manifest['stages'].append({'argv':cmd,'exit':proc.returncode,'fatal':bad,'wall_timeout':timed_out,'elapsed_s':round(time.monotonic()-begin,3)})
        (folder/'run.json').write_text(json.dumps(manifest,indent=2))
        print(case,tool,proc.returncode,'FATAL' if bad else '',flush=True)
        return proc.returncode==0 and not bad,log
    stages=[]
    if case.startswith('full'):stages.append(('xvhdl',['--relax','-prj','official.prj']))
    stages += [('xvlog',['--sv',*frozen]),('xelab',[f'work.{top}','--debug','off','--relax','--mt',str(min(32,max(2,(os.cpu_count() or 4)//2))),
        *([x for lib in LIBS for x in ['-L',lib]] if case.startswith('full') else []),'-s','test'])]
    for tool,args in stages:
        good,log=stage(tool,args)
        if not good:
            manifest['verdict']='COMPILE_ELAB_FAIL';print(log[-5000:]);break
    else:
        args=['test','--runall','--maxdeltaid','10000','--onerror','quit','--onfinish','quit','--sv_seed','1744']
        if case=='canary_export':args+=['--testplusarg','CANARY']
        if case in ('full_stop','full_stall','full_probe'):args+=['--testplusarg',case.upper()]
        good,log=stage('xsim',args)
        expected={'control':'CONTROL_COMPLETE','export':'EXPORT_COMPLETE','watchdog':'WATCHDOG_COMPLETE',
            'full':'CONTINUOUS_TOP_COMPLETE','full_stop':'CONTINUOUS_STOP_COMPLETE','full_stall':'CONTINUOUS_STALL_COMPLETE','full_probe':'PROBE_COMPLETE','full_first':'CONTINUOUS_FIRST_COMPLETE','full_noise':'CONTINUOUS_NOISE_STOP_COMPLETE'}
        if case=='canary_export':
            manifest['verdict']='EXPECTED_CHECKER_REJECTION' if not good and 'EXPORT_CHECK payload canary' in log and 'EXPORT_COMPLETE' not in log else 'CANARY_FAIL'
        else:manifest['verdict']='FUNCTIONAL_SIM_PASS' if good and expected[case] in log else 'SIM_FAIL'
        print(log[-2800:],flush=True)
    manifest['logs']={p.name:sha(p) for p in folder.glob('*.log')}
    manifest['unchanged']=all(sha(Path(p))==h for p,h in manifest['sources'].items())
    (folder/'run.json').write_text(json.dumps(manifest,indent=2))
    print(case,manifest['verdict'],flush=True)
    return manifest['verdict'] in ('FUNCTIONAL_SIM_PASS','EXPECTED_CHECKER_REJECTION')

if __name__=='__main__':
    for case in sys.argv[1:] or ['control','export','watchdog','canary_export']:
        if case not in ('control','export','watchdog','canary_export','full','full_stop','full_stall','full_probe','full_first','full_noise'):raise SystemExit('unknown case')
        if not run(case):raise SystemExit(1)
