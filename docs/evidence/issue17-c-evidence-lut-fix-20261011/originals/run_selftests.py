"""Run native XSim author self-tests in new directories, with real command/exit/log provenance.
Command: python run_selftests.py
Outputs: sim_*/run.json and native logs. Next: independent review of exact frozen source.
"""
import hashlib,json,os,pathlib,subprocess,time,sys
ROOT=pathlib.Path(__file__).resolve().parent
freeze=json.loads((ROOT/'product-freeze.json').read_text())
product=pathlib.Path(freeze['product_path'])
assert hashlib.sha256(product.read_bytes()).hexdigest()==freeze['product_sha256']
TOOLS=pathlib.Path('C:/AMDDesignTools/2025.2/Vivado')
env=os.environ.copy();env['PROCESSOR_ARCHITECTURE']='AMD64'
env.update(XILINX_VIVADO=str(TOOLS),RDI_APPROOT=str(TOOLS),HDI_APPROOT=str(TOOLS),RDI_OPT_EXT='.o',RDI_DATADIR=str(TOOLS/'data'),RDI_LIBDIR=str(TOOLS/'lib/win64.o'),RDI_BINDIR=str(TOOLS/'bin'),RDI_PLATFORM='win64',TCL_LIBRARY=str(TOOLS.parent/'tps/tcl/tcl8.6'))
env['PATH']=';'.join(str(p) for p in [TOOLS/'lib/win64.o',TOOLS/'lib/win64.o/Default',TOOLS/'bin/unwrapped/win64.o',*[TOOLS.parent/p for p in ['tps/win64/jre21.0.5_11/bin/server','tps/win64/jre21.0.5_11/bin','tps/win64/python-3.13.0','tps/mingw/6.2.0/win64.o/nt/bin']]])+';'+env['PATH']
for name,top,plus in [('words','tb_words',None),('evidence','tb_evidence',None),('canary','tb_evidence','CANARY_DATA')]:
    folder=ROOT/f'sim_{name}';folder.mkdir(exist_ok=False)
    sources=[product,ROOT/'selftest/i17_vio_evidence_before.sv',ROOT/f'selftest/{top}.sv']
    meta={'candidate_sha256':freeze['product_sha256'],'case':name,'tool':'Vivado XSim 2025.2','seed':17010,'sources':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'commands':[],'status':'RUNNING'}
    for tool,args in [('xvlog',['--sv',*sources]),('xelab',[f'work.{top}','--snapshot','test','--debug','off']),('xsim',['test','--runall','--onerror','quit','--onfinish','quit','--sv_seed','17010']+(['--testplusarg',plus] if plus else []))]:
        cmd=[str(TOOLS/'bin/unwrapped/win64.o'/f'{tool}.exe'),*map(str,args)]
        t=time.monotonic();cp=subprocess.run(cmd,cwd=folder,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=300)
        log=cp.stdout.decode('utf8',errors='replace');(folder/f'{tool}-stdout.log').write_text(log,encoding='utf8')
        meta['commands'].append({'argv':cmd,'exit':cp.returncode,'elapsed_s':round(time.monotonic()-t,3)})
        (folder/'run.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
        if cp.returncode:meta['status']='TOOL_OR_COMPILE_FAIL';break
    else:
        if plus:meta['status']='EXPECTED_CANARY_REJECTION' if 'Fatal: DATA_CHECK' in log else 'CANARY_FAILED_TO_DETECT'
        else:meta['status']='AUTHOR_CHECKS_COMPLETE_PENDING_REVIEW' if ('WORD_ORACLE_COMPLETE' if name=='words' else 'PUBLIC_READ_COMPLETE') in log and 'Fatal:' not in log else 'CHECK_FAILED'
    (folder/'run.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
    print(name,meta['status'],log[-700:],flush=True)
    if meta['status'] not in ('EXPECTED_CANARY_REJECTION','AUTHOR_CHECKS_COMPLETE_PENDING_REVIEW'):sys.exit(1)
