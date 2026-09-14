import concurrent.futures,hashlib,json,pathlib,shutil,subprocess,sys,time
ROOT=pathlib.Path(__file__).parent
OLD=pathlib.Path('F:/NUEC/review-worktrees/b-skills-main-20260914/results/skill-review/b-20260914')
W=pathlib.Path('F:/NUEC/review-worktrees/b-skl001-a7e1ea9')
SHA='a7e1ea976da91ba735af5c0a79fffdc7d10c121f'
assert subprocess.check_output(['git','-C',str(W),'rev-parse','HEAD'],text=True).strip()==SHA
OUT=ROOT/'s-independent';OUT.mkdir(exist_ok=False)
src=W/'skill/fpga-module-verification/examples/elastic'
def copy_case(label,base):
    d=OUT/'fixtures'/label;shutil.copytree(base,d);return d
cases=[]
d=copy_case('b-two-stage-new-tb',OLD/'latency-mutant');shutil.copyfile(src/'tb_elastic.sv',d/'tb_elastic.sv');cases.append((d,False,'one_edge_valid'))
for label,old in [('b-witness-correct','b-latency-original'),('b-witness-two-stage','b-latency-two-stage')]:
    d=copy_case(label,OLD/old)
    if old.endswith('original'):shutil.copyfile(src/'elastic_stage.v',d/'elastic_stage.v')
    cases.append((d,old.endswith('original'),None if old.endswith('original') else 'one-edge latency'))
rtl=(src/'elastic_stage.v').read_text()
for label,old,new,ok,failure in [
 ('reset-ready-low','!out_valid || out_ready','rst_n && (!out_valid || out_ready)',True,None),
 ('full-slot-ready','!out_valid || out_ready',"1'b1",False,'slot_ready'),
 ('payload-x','out_data <= in_data;',"out_data <= {WIDTH{1'bx}};",False,'one_edge_data'),
 ('payload-z','out_data <= in_data;',"out_data <= {WIDTH{1'bz}};",False,'one_edge_data'),
 ('valid-x','out_valid <= in_valid;',"out_valid <= 1'bx;",False,'one_edge_valid'),
]:
    assert rtl.count(old)==1,(label,old)
    d=copy_case(label,src);(d/'elastic_stage.v').write_text(rtl.replace(old,new),encoding='utf-8');cases.append((d,ok,failure))
def run(item):
    d,ok,failure=item;out=OUT/d.name;out.mkdir()
    cmd=[sys.executable,'-B',str(W/'skill/fpga-module-verification/scripts/run_xsim.py'),'--case',str(d/'case.json'),'--vivado-bin','D:/AMD/2025.2/Vivado/bin','--output',str(out/'run')]
    t=time.time();r=subprocess.run(cmd,cwd=W,capture_output=True)
    (out/'stdout.log').write_bytes(r.stdout);(out/'stderr.log').write_bytes(r.stderr)
    (out/'command.json').write_text(json.dumps(dict(command=cmd,cwd=str(W),exit_code=r.returncode,started_unix=t),indent=2)+'\n')
    result=json.loads((out/'run/result.json').read_text())
    passed=r.returncode==(0 if ok else 1) and result['stage']=='simulate' and result['status']==('PASS_SIMULATION' if ok else 'FAIL_SIMULATION') and all(c['returncode']==0 and not c['timed_out'] for c in result['commands'] if c['stage']!='simulate')
    if failure:passed=passed and failure in (result.get('first_failure') or '')
    return dict(name=d.name,passed=passed,exit_code=r.returncode,status=result['status'],checks=result.get('checks'),first_failure=result.get('first_failure'))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,cases))
(OUT/'checks.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2));sys.exit(any(not r['passed'] for r in results))
