"""Append-only host-test record. No firmware builds or board access."""
from pathlib import Path
import subprocess,sys,time,uuid,json,hashlib
HERE=Path(__file__).resolve().parent
out=HERE/'evidence'/('gate_'+time.strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8])
out.mkdir(parents=True)
cmd=[sys.executable,'-B',str(HERE/'tests/test_gate.py')]
p=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
(out/'stdout.log').write_text(p.stdout,encoding='utf-8')
(out/'stderr.log').write_text(p.stderr,encoding='utf-8')
files=[HERE/f for f in ('check_scene.py','POLICY.json','tests/test_gate.py','vitis_gate.cmake')]
(out/'result.json').write_text(json.dumps(dict(kind='HOST_GUARD_TESTS_NOT_NEW_ARM_BUILD',
    argv=cmd,returncode=p.returncode,sha256={str(f.relative_to(HERE)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}),indent=2),encoding='utf-8')
print(json.dumps(dict(returncode=p.returncode,evidence=str(out))))
sys.exit(p.returncode)
