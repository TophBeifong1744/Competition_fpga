import sys, json, shutil
from pathlib import Path
from unittest.mock import patch
ROOT = Path('F:/NUEC/review-worktrees/a-current-build-050d06f/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01')
OUT = Path('F:\\NUEC\\review-evidence\\a-ps-repair-d0ce1c2\\b-replay')
sys.path.insert(0, str(ROOT/'current_build'))
import build_current as bc
from test_build_current import SafetyTests
f = SafetyTests()
f.setUp()
try:
    original = (ROOT/'source/ps/main_four_capture.c').read_bytes()
    changed = original.replace(b'#define BASE ((UINTPTR)0x01000000U)', b'#define BASE ((UINTPTR)0x00100000U)')
    assert changed != original
    (f.ps/'main_four_capture.c').write_bytes(changed)
    (f.ps/'lscript.ld').write_bytes((ROOT/'source/ps/lscript.ld').read_bytes())
    plan = f.check()
    # Mock completed Vivado/GCC output contracts only. No tool execution or hardware reproduction.
    def command(argv, out, name, cwd=None):
        if name == 'hardware':
            (out/'reports').mkdir()
            (out/'artifacts/hw').mkdir(parents=True)
            shutil.copyfile(f.xsa, out/'artifacts/hw/system_c_adapter.xsa')
            (out/'reports/timing-values.txt').write_text('setup_slack=4.640\nhold_slack=0.056\n')
            (out/'reports/timing-summary.rpt').write_text('  4.640 0.000 0 8561 0.056 0.000 0 8457 3.000 0.000 0 4592\n')
        if name == 'ps-symbols':
            return '00112630 B end\n'
        return ''
    with patch.object(bc, 'run_command', side_effect=command):
        result = bc.build(plan)
    summary = {'kind':'validator unit counterexample; tools mocked; not actual build',
        'review_sha':'050d06f5dc6fed4fa476e72fa416e9736bc7fef3',
        'input':'frozen real main_four_capture.c; only BASE changed 0x01000000 -> 0x00100000; frozen lscript.ld unchanged',
        'check_status':plan['status'], 'actual_ps_base':'0x00100000',
        'mock_linker_end':'0x00112630', 'program_overlaps_actual_rx':0x00112630>0x00100000,
        'build_validator_result': result}
    (OUT/'ddr-counterexample-result.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
finally:
    f.doCleanups()
