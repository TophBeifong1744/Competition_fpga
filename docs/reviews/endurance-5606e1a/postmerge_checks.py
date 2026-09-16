"""Verify merged bytes and rerun archive/Python suite at its new location."""
import json,os,subprocess,sys
from pathlib import Path
root=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=False)
rel='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/endurance-test-01'
e1=root/rel
git='C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
prefix=[git,'-c','safe.directory='+root.as_posix(),'-C',str(root)]
assert not subprocess.check_output(prefix+['diff','5606e1a9d9a6183ceff7cffc1bb4f8aac44bb79c','HEAD','--',rel])
assert not (e1.parent/'timerfixed-entry-01').exists()
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=str(root))
env['PATH']=str(Path(git).parent)+os.pathsep+env['PATH']
jobs=[('manifest',[sys.executable,'-B',e1/'publication/package_manifest.py']),
      ('reproduce',[sys.executable,'-B',e1/'publication/reproduce.py','--repo',root,'--out',out/'reproduced'])]
results=[]
for name,args in jobs:
    argv=list(map(str,args));p=subprocess.run(argv,cwd=root,env=env,capture_output=True,timeout=300)
    (out/(name+'.stdout')).write_bytes(p.stdout);(out/(name+'.stderr')).write_bytes(p.stderr)
    results.append(dict(argv=argv,cwd=str(root),returncode=p.returncode))
    print(name,p.returncode,p.stdout.decode(errors='replace')[-400:],flush=True)
(out/'commands.json').write_bytes((json.dumps(results,indent=2)+'\n').encode())
assert all(r['returncode']==0 for r in results)
