"""B independent execution ledger; fresh external output only."""
import datetime,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(sys.argv[1]).resolve()
OUT=Path(sys.argv[2]).resolve()
OUT.mkdir(parents=True,exist_ok=False)
E1=ROOT/'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/endurance-test-01'
GIT='C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd'
GCC='F:/STUDY/IT/C/develop/mingw64/bin/gcc.exe'
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='Never',GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=str(ROOT))
env['PATH']=GIT+os.pathsep+str(Path(GCC).parent)+os.pathsep+env['PATH']
jobs=[('publication-manifest',[sys.executable,'-B',E1/'publication/package_manifest.py']),
      ('original-manifest',[sys.executable,'-B',E1/'board-run-20260916-01/record_checks.py','verify']),
      ('log-tests',[sys.executable,'-B',E1/'board-run-20260916-01/test_verify_log.py']),
      ('reproduce',[sys.executable,'-B',E1/'publication/reproduce.py','--repo',ROOT,'--out',OUT/'reproduced','--gcc',GCC])]
results=[]
for name,argv in jobs:
    argv=list(map(str,argv))
    start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    p=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True,timeout=300)
    (OUT/(name+'.stdout')).write_bytes(p.stdout)
    (OUT/(name+'.stderr')).write_bytes(p.stderr)
    record=dict(name=name,argv=argv,cwd=str(ROOT),started_utc=start,returncode=p.returncode)
    results.append(record)
    (OUT/(name+'.command.json')).write_bytes((json.dumps(record,indent=2)+'\n').encode())
    print(name,p.returncode,p.stdout.decode('utf-8','replace')[-500:],p.stderr.decode('utf-8','replace')[-500:],flush=True)
(OUT/'commands.json').write_bytes((json.dumps(results,indent=2)+'\n').encode())
raise SystemExit(any(r['returncode'] for r in results))
