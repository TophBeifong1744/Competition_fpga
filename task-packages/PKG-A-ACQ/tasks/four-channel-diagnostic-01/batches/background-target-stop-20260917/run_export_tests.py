"""Run existing H1 converter cases and new raw/UART cases; append-only evidence."""
from pathlib import Path
import subprocess,sys,json,time,uuid,hashlib
HERE=Path(__file__).resolve().parent
out=HERE/'evidence'/('export_'+time.strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
source=HERE.parents[1]/'source'
commands=[([sys.executable,'-B','-m','unittest','-v','test_export'],source),
          ([sys.executable,'-B',str(HERE/'tests/test_scene_export.py')],HERE)]
records=[]
for i,(cmd,cwd) in enumerate(commands):
    p=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True,encoding='utf-8',timeout=120)
    (out/f'{i}.stdout.log').write_text(p.stdout,encoding='utf-8');(out/f'{i}.stderr.log').write_text(p.stderr,encoding='utf-8')
    records.append(dict(argv=cmd,cwd=str(cwd),returncode=p.returncode))
files=[HERE/'finish_scene.py',HERE/'tests/test_scene_export.py',source/'export_four.py',source/'test_export.py']
report=dict(scope='Offline raw/UART/CSV converter checks, not independent B review',commands=records,
    files={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
(out/'result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
ok=all(r['returncode']==0 for r in records);print(json.dumps(dict(passed=ok,evidence=str(out))));sys.exit(0 if ok else 1)
