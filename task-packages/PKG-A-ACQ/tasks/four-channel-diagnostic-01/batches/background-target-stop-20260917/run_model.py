"""Run the portable real C loop; NEVER invokes Vivado, Vitis or hardware."""
from pathlib import Path
import subprocess,sys,time,uuid,json,hashlib
HERE=Path(__file__).resolve().parent
out=HERE/'evidence'/('model_'+time.strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8])
out.mkdir(parents=True)
gcc=Path(sys.argv[1]) if len(sys.argv)>1 else Path('F:/Program/env/mingw64/bin/gcc.exe')
src=HERE/'proposed-src/continuous'
commands=[[str(gcc),'-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',
           '-I'+str(src),str(src/'continuous_core.c'),str(src/'scene_store.c'),
           str(HERE/'tests/test_scene.c'),'-o',str(out/'test_scene.exe')],
          [str(out/'test_scene.exe')]]
results=[]
for i,cmd in enumerate(commands):
    try:
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
        (out/f'{i}.stdout.log').write_text(p.stdout,encoding='utf-8')
        (out/f'{i}.stderr.log').write_text(p.stderr,encoding='utf-8')
        results.append(dict(argv=cmd,returncode=p.returncode))
        if p.returncode:break
    except Exception as e:
        results.append(dict(argv=cmd,error=str(e)));break
files=list(src.glob('*.[ch]'))+list((HERE/'tests').glob('*.c'))
report=dict(kind='HOST_C_MODEL_NOT_BOARD_NOT_ARM_BUILD',commands=results,
            pass_model=len(results)==2 and all(r.get('returncode')==0 for r in results),
            sha256={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
(out/'result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(dict(pass_model=report['pass_model'],evidence=str(out))))
sys.exit(0 if report['pass_model'] else 1)
