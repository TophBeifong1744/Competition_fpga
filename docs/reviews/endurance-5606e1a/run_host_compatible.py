"""Use native MinGW's ANSI stdio for C99 %llu; retain all warnings/errors."""
import datetime,json,os,subprocess,sys
from pathlib import Path
source=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=False)
record=json.loads((source/'host-compile.command.json').read_text())
argv=record['argv'][:]
argv.insert(1,'-D__USE_MINGW_ANSI_STDIO=1')
argv[-1]=str(out/'test_endurance.exe')
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
env['PATH']=str(Path(argv[0]).parent)+os.pathsep+env['PATH']
results=[]
for name,command in [('host-compile',argv),('host-model',[argv[-1]])]:
    p=subprocess.run(command,cwd=record['cwd'],env=env,capture_output=True,timeout=120)
    (out/(name+'.stdout')).write_bytes(p.stdout);(out/(name+'.stderr')).write_bytes(p.stderr)
    result=dict(argv=command,cwd=record['cwd'],returncode=p.returncode,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    results.append(result)
    print(name,p.returncode,p.stdout.decode(errors='replace')[-600:],p.stderr.decode(errors='replace')[-600:],flush=True)
    if p.returncode:break
(out/'commands.json').write_bytes((json.dumps(results,indent=2)+'\n').encode())
assert len(results)==2 and all(p['returncode']==0 for p in results)
assert b'ENDURANCE_MODEL_PASS' in (out/'host-model.stdout').read_bytes()
