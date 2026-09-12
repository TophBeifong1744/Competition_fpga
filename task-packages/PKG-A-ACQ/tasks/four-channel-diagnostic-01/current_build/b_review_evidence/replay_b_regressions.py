import hashlib,json,subprocess,sys
from pathlib import Path
E=Path(__file__).resolve().parent
old=Path('F:/NUEC/review-evidence/a-current-build-050d06f')
newroot=Path('F:/NUEC/review-worktrees/a-ps-repair-d0ce1c2/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01')
replay=E/'b-replay';replay.mkdir(exist_ok=False)
original=(old/'spec/ddr_counterexample.py').read_bytes()
(replay/'original-ddr-counterexample.py.txt').write_bytes(original)
oldrun=original.decode().replace("OUT = Path('F:/NUEC/review-evidence/a-current-build-050d06f/spec')",f'OUT = Path({str(replay)!r})')
(replay/'legacy-replay.py').write_text(oldrun,encoding='utf-8')
r=subprocess.run([sys.executable,'-B',str(replay/'legacy-replay.py')],capture_output=True,text=True)
assert r.returncode==0,r.stderr
(replay/'legacy-replay.stdout.txt').write_text(r.stdout)
legacy=json.loads((replay/'ddr-counterexample-result.json').read_text())
assert legacy['build_validator_result']['status']=='BUILD_PASS_NOT_BOARD_TEST'
tests=(old/'standards/equivalence_probes.py').read_bytes()
(replay/'original-equivalence-probes.py.txt').write_bytes(tests)
repoint=tests.decode().replace('a-current-build-050d06f','a-ps-repair-d0ce1c2')
(replay/'equivalence-replay.py').write_text(repoint,encoding='utf-8')
r=subprocess.run([sys.executable,'-B',str(replay/'equivalence-replay.py')],capture_output=True,text=True)
assert r.returncode==0,r.stderr
(E/'02-b-21-checks.txt').write_text(r.stdout)
sys.path.insert(0,str(newroot/'current_build'))
import build_current as bc
import ps_contract as pc
from test_build_current import SafetyTests
from unittest.mock import patch
f=SafetyTests();f.setUp()
try:
    original_source=(newroot/'source/ps/main_four_capture.c').read_bytes()
    changed=original_source.replace(b'#define BASE ((UINTPTR)0x01000000U)',b'#define BASE ((UINTPTR)0x00100000U)')
    assert changed!=original_source
    (f.ps/'main_four_capture.c').write_bytes(changed)
    (f.ps/'lscript.ld').write_bytes((newroot/'source/ps/lscript.ld').read_bytes())
    plan=f.check()
    legal=json.loads((newroot/'current_build/repair_ps_contract/evidence/legal-ps-02/ps_check/contract-result.json').read_text())
    hw=legal['hardware']
    obj=newroot/'current_build/repair_ps_contract/evidence/compiled-proof/rejected/ps_build_unit.o'
    called=[]
    def command(argv,out,name,cwd=None):
        called.append(name)
        if name=='ps-preprocess':(cwd/'ps_build_unit.i').write_text('B replay placeholder; no compiler executed')
        if name=='ps-compile':(cwd/'ps_build_unit.o').write_bytes(obj.read_bytes())
        if name=='hardware':raise AssertionError('hardware must not run')
        return ''
    with patch.object(bc,'run_command',side_effect=command),patch.object(pc,'hardware_contract',return_value=hw):
        result=bc.build(plan)
    assert result['status']=='BUILD_FAILED' and 'Unsupported changed fixed PS contract' in result['error'],result
    assert 'hardware' not in called
    rejection={'result':result,'tools_simulated':called,'source_sha256':hashlib.sha256(changed).hexdigest(),
      'archived_object_sha256':hashlib.sha256(obj.read_bytes()).hexdigest(),
      'archived_object_BASE':pc.Elf32(obj,1).contract()['BASE'],
      'method':'Original B changed-source stimulus; real new compile_bound_ps + value validator; hardware shape supplied from archived legal report; compiler simulated by archived rejected real object. Not new compilation.'}
    (E/'03-b-counterexample-repair.json').write_text(json.dumps(rejection,indent=2)+'\n')
finally:f.doCleanups()
print('PASS: B original legacy false-positive replay, B 21 equivalence checks, repaired rejection before hardware')
