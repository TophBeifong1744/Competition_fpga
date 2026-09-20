"""Host syntax-only check of the complete translation unit, NOT an ARM/BSP build."""
from pathlib import Path
import subprocess,json,sys,time,uuid,hashlib
HERE=Path(__file__).resolve().parent
out=HERE/'evidence'/('syntax_'+time.strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8])
out.mkdir(parents=True);inc=out/'stub_includes';inc.mkdir()
for name in ('xparameters','xaxidma','xaxidma_hw','xgpio','xil_cache','xil_printf','xiltimer','sleep'):
    (inc/(name+'.h')).write_text('#include "firmware_stubs.h"\n',encoding='ascii')
gcc=Path('F:/Program/env/mingw64/bin/gcc.exe')
cmd=[str(gcc),'-std=c11','-O2','-Wall','-Wextra','-Werror','-fsyntax-only',
     '-I'+str(inc),'-I'+str(HERE/'tests'),str(HERE/'proposed-src/main.c')]
p=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
(out/'stdout.log').write_text(p.stdout,encoding='utf-8');(out/'stderr.log').write_text(p.stderr,encoding='utf-8')
files=list((HERE/'proposed-src').rglob('*.[ch]'))+[HERE/'tests/firmware_stubs.h']
(out/'result.json').write_text(json.dumps(dict(kind='HOST_STUB_SYNTAX_NOT_ARM_BSP_BUILD',
    argv=cmd,returncode=p.returncode,sha256={str(f.relative_to(HERE)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}),indent=2),encoding='utf-8')
print(json.dumps(dict(returncode=p.returncode,evidence=str(out))));sys.exit(p.returncode)
