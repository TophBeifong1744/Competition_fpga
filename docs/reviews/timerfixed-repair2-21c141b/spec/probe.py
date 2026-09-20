import sys,json,hashlib
from pathlib import Path
entry=Path(r'F:/NUEC/review-worktrees/timerfixed-repair2-21c141b/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/timerfixed-entry-01')
sys.path.insert(0,str(entry))
import check_entry as gate
app=Path(gate.POLICY['reference_app']); bsp=Path(gate.POLICY['reference_bsp'])
a=json.loads((entry/'user-build-20260916-01/verification-01/ninja-commands.json').read_text())['stdout']
p=app.as_posix()+'/src/lscript.ld'; token='-Wl,"'+p+'"'
assert a.count(token)==1
cases=[]
def run(label,replacement,expected):
 try:
  gate.verify_link_output(a.replace(token,replacement),app,bsp); actual='ACCEPTED'; detail=None
 except ValueError as e:
  actual='REJECTED'; detail=str(e)
 cases.append(dict(label=label,token=replacement,expected=expected,actual=actual,detail=detail))
for extra in ['',',-e,0x01000000',',--defsym,REVIEW_MARKER=1',',--wrap=XAxiDma_SimpleTransfer']:
 run('original B counterexample '+extra,token[:-1]+extra+',-L,/../lscript.ld"','REJECTED')
for extra in [',@response.txt',',--defsym=X=1',',--entry=0',',-L,x',',-T,x',',--end-group',',',',,']:
 for tail in ['', '/../lscript.ld', '/../../src/lscript.ld']:
  for quote in [True,False]:
   payload=p+extra+tail
   run('independent comma mutation', '-Wl,'+('"'+payload+'"' if quote else payload),'REJECTED')
for payload in [p,p.upper(),p.replace('/src/','/src/./'),p.replace('/src/','/src/../src/')]:
 run('known path-only equivalent','-Wl,"'+payload+'"','ACCEPTED')
for replacement in ['-Wl,"'+p+'" -Wl,--end-group','-Wl,"'+p+'" -u__clang__','-Wl,relative.ld','-Wl,F:/other/lscript.ld','-Wl,-T,'+p]:
 run('layout or extra argument',replacement,'REJECTED')
result={'sha':'21c141b223936730c2ce5139624fcedb412adafb','scope':'Independent actual verify_link_output command mutation probes; no compile/link/hardware','cases':cases,'passed':sum(x['actual']==x['expected'] for x in cases),'total':len(cases)}
Path(r'F:/NUEC/review-evidence/timerfixed-repair2-21c141b/spec/probe-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(result['passed'],result['total'])
assert result['passed']==result['total']
