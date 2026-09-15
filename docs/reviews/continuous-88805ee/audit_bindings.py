"""B read-only supplement: archived source MD5, BSP macros, XSA init, source identity."""
import hashlib
import json
from pathlib import Path, PureWindowsPath
import sys
import zipfile

root = Path(sys.argv[1]).resolve()
task = root / 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01'
board = task / 'board-run-20260915-02'
entries = json.loads((board / 'build/source-hash-map.json').read_bytes())['rigel.build.dc_embedded.host.project']
matched, missing = [], []
for entry in entries:
    parts = PureWindowsPath(entry['uri']).parts
    relative = '/'.join(parts[parts.index('src') + 1:]) if 'src' in parts else parts[-1]
    local = board / 'ps' / relative
    if not local.is_file():
        missing.append(relative)
        continue
    assert hashlib.md5(local.read_bytes()).hexdigest() == entry['md5'], relative
    matched.append(relative)
assert len(matched) == 7 and set(missing) == {'vitis-comp.json', 'README.txt'}

obj = (board / 'build/main.c.obj').read_bytes()
macros = ['COUNTS_PER_SECOND XSLEEPTIMER_FREQ',
          'XSLEEPTIMER_FREQ XPAR_CPU_CORE_CLOCK_FREQ_HZ/2',
          'XPAR_CPU_CORE_CLOCK_FREQ_HZ 666666687']
for macro in macros:
    assert macro.encode() + b'\0' in obj, macro

with zipfile.ZipFile(board / 'runtime/system_continuous_20260915.xsa') as archive:
    init = [name for name in archive.namelist() if name.endswith('ps7_init.tcl')]
    assert len(init) == 1
    assert archive.read(init[0]) == (board / 'runtime/ps7_init.tcl').read_bytes()

copies = {
    'rtl/four_mic_top.v': 'delivery-01/evidence/simulation/four_mic_top.v',
    'rtl/pcm4_continuous_axis.v': 'delivery-01/evidence/simulation/pcm4_continuous_axis.v',
    'sim/tb_continuous.sv': 'delivery-01/evidence/simulation/tb_continuous.sv',
    'sim/tb_frontend.sv': 'delivery-01/evidence/simulation/tb_frontend.sv',
    'ps/continuous_core.c': 'publication/checks/host/continuous_core.c',
    'tests/test_core.c': 'publication/checks/host/test_core.c',
}
for current, historical in copies.items():
    assert (task / current).read_bytes() == (task / historical).read_bytes(), current
with zipfile.ZipFile(task / 'delivery-01/history/ss-cont-host-01.zip') as archive:
    assert (task / 'ps/continuous_core.c').read_bytes() == archive.read('continuous_core.c')
    early_test = archive.read('test_core.c')
    current_test = (task / 'tests/test_core.c').read_bytes()
    # The early test predates the corrected stop-timeout and extra failure cases.
    assert early_test != current_test
    import difflib
    early_test_diff = ''.join(difflib.unified_diff(early_test.decode().splitlines(True),
                            current_test.decode().splitlines(True), fromfile='ss-cont-host-01.zip!test_core.c',
                            tofile='tests/test_core.c'))

print(json.dumps({'result': 'PASS_ARCHIVED_BINDINGS_WITH_TWO_UNAVAILABLE_MD5_INPUTS',
                  'matched_build_md5': matched, 'not_archived_md5_inputs': missing,
                  'actual_object_macro_strings': macros, 'xsa_ps7_init_equal': True,
                  'unchanged_archived_source_pairs': copies,
                  'early_host_test_diff_not_final_coverage': early_test_diff}, indent=2))
