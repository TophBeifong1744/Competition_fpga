"""Run pinned A review commands without editing the A package. Python always -B."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--a-root', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--mode', choices=['archive','prepare','build','simulate','check'], required=True)
    p.add_argument('--vivado', type=Path, default=Path('D:/AMD/2025.2/Vivado/bin/vivado.bat'))
    a = p.parse_args()
    package = a.a_root/'task-packages/PKG-A-ACQ/tasks/fft29-bitexact-budget-01'
    git = ['git','-c',f'safe.directory={a.a_root.as_posix()}','-C',str(a.a_root)]
    commit = subprocess.check_output(git+['rev-parse','HEAD'], text=True).strip()
    assert commit == 'c0b5f8fb44643e81d8c4e6f0be457dddeae9758e'
    a.out.mkdir(parents=True,exist_ok=True)
    record_path = a.out/f'{a.mode}-commands.json'
    assert not record_path.exists(), 'Refusing to overwrite command record'
    src = package/'source'
    def py(script, *args): return [sys.executable,'-B',str(src/script),*map(str,args)]
    if a.mode=='archive':
        commands = [py('package_manifest.py','check'),py('test_checker.py'),py('check_resources.py'),
            py('check.py','--vectors',package/'evidence/run01/vectors','--simulation',package/'evidence/run01/simulation','--out',a.out/'archive-check.json'),
            py('audit_reference.py','--reference',package/'reference/b-dynamic-range','--out',a.out/'reference-check.json')]
    elif a.mode=='prepare':
        commands = [py('prepare.py','--reference',package/'reference/b-dynamic-range','--out',a.out/'vectors')]
    elif a.mode in ['build','simulate']:
        stem = a.mode
        commands = [[str(a.vivado),'-mode','batch','-notrace','-source',str(src/f'{stem}.tcl'),
            '-log',str(a.out/f'{stem}.log'),'-journal',str(a.out/f'{stem}.jou'),'-tclargs',str(a.out/'project')]]
        if stem=='simulate': commands[0].append(str(a.out/'vectors'))
    else:
        sim = a.out/'project/fft29_budget.sim/sim_1/behav/xsim'
        commands = [py('check.py','--vectors',a.out/'vectors','--simulation',sim,'--out',a.out/'check.json'),
                    py('collect_simulation.py','--simulation',sim,'--out',a.out/'simulation-archive')]
    record = dict(A_commit=commit, mode=a.mode, python=sys.version, platform=platform.platform(),
                  runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), commands=[])
    failed = False
    for index, command in enumerate(commands):
        log = a.out/f'{a.mode}-{index:02d}-console.txt'
        assert not log.exists()
        start = time.time()
        with log.open('wb') as f:
            proc = subprocess.run(command, cwd=a.out, stdout=f, stderr=subprocess.STDOUT)
        record['commands'].append(dict(argv=command,cwd=str(a.out),
            started_utc=datetime.datetime.fromtimestamp(start, datetime.timezone.utc).isoformat(),
            elapsed_seconds=time.time()-start,exit_code=proc.returncode,console=log.name))
        record_path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
        print(f'{a.mode} {index}: exit={proc.returncode}; {log}',flush=True)
        failed |= proc.returncode != 0
        if failed and a.mode != 'archive': break
    raise SystemExit(1 if failed else 0)

if __name__=='__main__': main()
