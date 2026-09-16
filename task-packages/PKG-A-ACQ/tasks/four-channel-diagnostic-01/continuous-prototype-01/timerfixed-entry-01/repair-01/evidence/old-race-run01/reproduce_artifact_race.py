"""Evidence-only TOCTOU reproducer: real ELFs, mocked hardware, partial verifier.

The checker boundary validates the real object/ELF through verify_elf. Remaining
load preconditions are simulated satisfied. No full local author Vitis is claimed.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PACKAGE = Path('E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/timerfixed-entry-01')
TCL = 'F:/AMD/2025.2/tps/win64/git-2.50.0/mingw64/bin/tclsh86.exe'
sys.path.insert(0, str(PACKAGE))
import check_entry as gate


def tq(value):
    return '{' + str(value).replace('\\', '/') + '}'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if len(sys.argv) == 3:
    result = gate.verify_elf(Path(sys.argv[1]), Path(sys.argv[2]))
    print('REAL_ELF_CONTRACT_CHECK_PASS sha256=' + result['elf_sha256'])
    raise SystemExit(0)


obj = PACKAGE / 'user-build-20260916-01/app/build/CMakeFiles/four_mic_continuous.elf.dir/main.c.obj'
initial = PACKAGE / 'user-build-20260916-01/app/build/four_mic_continuous.elf'
results = []
for name, replacement in (
    ('old-timer-elf', PACKAGE.parent / 'board-run-20260915-01/four_mic_continuous_prefix.elf'),
    ('other-valid-fixed-elf', gate.REFERENCE / 'runtime/four_mic_continuous.elf'),
):
    app = ROOT / ('race-' + name) / 'four_mic_continuous'
    live = app / 'build/four_mic_continuous.elf'
    live.parent.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(initial, live)
    try:
        gate.verify_elf(obj, replacement)
        replacement_check = 'PASS (different ELF from checked build receipt)'
    except Exception as exc:
        replacement_check = 'REJECTED: ' + str(exc)
    script = '''
set events {}
set app ''' + tq(app) + '''
set replacement ''' + tq(replacement) + '''
set elf "$app/build/four_mic_continuous.elf"
foreach name {connect targets rst fpga ps7_init ps7_post_config con} {
    proc $name {args} [format {lappend ::events %s} $name]
}
rename exec actual_exec
proc exec {args} {
    lappend ::events verifier
    if {[lindex $args 6] ne $::app} {error "unexpected checked app"}
    return [actual_exec ''' + ' '.join(map(tq, [sys.executable, '-B', Path(__file__), obj, live])) + ''']
}
proc after {args} {
    lappend ::events artifact_replaced_during_after
    file copy -force $::replacement "$::elf.pending"
    file rename -force "$::elf.pending" $::elf
}
proc dow {path} {
    lappend ::events dow
    set f [open $path rb]; set observed [read $f]; close $f
    set f [open $::replacement rb]; set replaced [read $f]; close $f
    if {$observed ne $replaced} {error "race fixture did not swap loaded bytes"}
    puts "MOCK_DOW_READ_UNCHECKED_REPLACEMENT bytes=[string length $observed] path=$path"
}
source ''' + tq(PACKAGE / 'load_timerfixed.tcl') + '''
rename source actual_source
proc source {args} {lappend ::events init_source}
c1_timerfixed_load python $app platform tools records 0
if {[lindex $events end] ne "con"} {error "loader did not reach mocked continue"}
puts "RACE_REPRODUCED events=$events; NO_BOARD"
'''
    script_path = ROOT / ('race-' + name + '.tcl')
    script_path.write_text(script, encoding='utf-8')
    proc = subprocess.run([TCL, str(script_path)], capture_output=True, text=True, cwd=ROOT, timeout=30)
    result = dict(case=name, returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr,
                  initial_sha256=sha(initial), replacement_sha256=sha(replacement),
                  final_live_sha256=sha(live), replacement_contract_check=replacement_check,
                  board_test='NOT_RUN', scope='real verify_elf; other verifier preconditions simulated; hardware fully mocked')
    (ROOT / ('race-' + name + '.json')).write_text(json.dumps(result, indent=2), encoding='utf-8')
    results.append(result)
    print(json.dumps(result, indent=2))
    if proc.returncode or result['initial_sha256'] == result['replacement_sha256'] or result['final_live_sha256'] != result['replacement_sha256']:
        raise RuntimeError('race failed to reproduce')
(ROOT / 'artifact-race-results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
