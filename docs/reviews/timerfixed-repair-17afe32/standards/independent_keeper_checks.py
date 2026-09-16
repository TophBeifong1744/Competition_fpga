"""New keeper lifecycle/lock coverage, no XSDB or hardware."""
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
ENTRY = Path('F:/NUEC/review-worktrees/timerfixed-repair-17afe32/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/timerfixed-entry-01')
TCL = 'F:/STUDY/IT/Anaconda3/Library/bin/tclsh.exe'


def fixture(name):
    case = ROOT / name
    case.mkdir(exist_ok=False)
    app = case / 'four_mic_continuous'
    shutil.copytree(ENTRY/'user-build-20260916-01/app', app)
    ref = ENTRY.parent/'board-run-20260915-02/runtime'
    for relative, source in (('_ide/bitstream/system_continuous_20260915.bit', 'system_continuous_20260915.bit'),
                             ('_ide/psinit/ps7_init.tcl', 'ps7_init.tcl')):
        dest = app/relative
        dest.parent.mkdir(exist_ok=True)
        shutil.copyfile(ref/source, dest)
    return case, app


def safe_rename(source, target):
    assert source.resolve().is_relative_to(ROOT) and target.resolve().is_relative_to(ROOT)
    source.rename(target)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tq(value):
    return '[encoding convertfrom utf-8 [binary decode base64 {' + base64.b64encode(str(value).encode()).decode() + '}]]'


results = []
for mode in ('release', 'eof', 'unknown-command'):
    case, app = fixture('keeper-' + mode)
    argv = [sys.executable, '-u', '-B', str(ROOT/'keeper_probe.py'), '--app', str(app),
            '--platform', str(case/'continuous_platform'), '--tools-bin', str(case/'tools'),
            '--record-root', str(case/'records')]
    child = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             encoding='utf-8', env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    line = child.stdout.readline().strip()
    assert line.startswith('GUARD_READY_V1 '), (line, child.stderr.read())
    paths = [Path(base64.b64decode(p).decode('utf-8')) for p in line.split()[1:]]
    initial = {str(p): digest(p) for p in paths}
    rejected = []
    for path in paths:
        for kind in ('write', 'replace', 'delete'):
            try:
                if kind == 'write':
                    with path.open('r+b'):
                        pass
                elif kind == 'replace':
                    pending = case/'replacement.bin'
                    pending.write_bytes(b'UNVALIDATED')
                    os.replace(pending, path)
                else:
                    assert path.resolve().is_relative_to(ROOT)
                    path.unlink()
            except OSError as exc:
                rejected.append({'op': kind, 'path': str(path), 'error': str(exc)})
            else:
                raise AssertionError('sealed mutation succeeded')
    for directory in (paths[0].parent, paths[0].parent.parent, case/'records'):
        try:
            safe_rename(directory, case/('renamed-' + directory.name))
        except OSError as exc:
            rejected.append({'op': 'ancestor-rename', 'path': str(directory), 'error': str(exc)})
        else:
            raise AssertionError('sealed ancestor renamed')
    safe_rename(app, case/'active-project-renamed-after-ready')
    assert {str(p): digest(p) for p in paths} == initial
    child.stdin.write('PING\n')
    child.stdin.flush()
    assert child.stdout.readline().strip() == 'GUARD_ALIVE'
    if mode == 'release':
        stdout, stderr = child.communicate('RELEASE\n', timeout=15)
        assert child.returncode == 0 and 'GUARD_RELEASED' in stdout
    elif mode == 'eof':
        stdout, stderr = child.communicate('', timeout=15)
        assert child.returncode == 1 and 'without release' in stderr
    else:
        stdout, stderr = child.communicate('INVALID_COMMAND\n', timeout=15)
        assert child.returncode == 1 and 'Unknown guard command' in stderr
    for path in paths:
        with path.open('r+b'):
            pass
    row = dict(mode=mode, argv=argv, ready=line, rejected=rejected, returncode=child.returncode,
               stdout=stdout, stderr=stderr, active_project_rename_after_ready='PASS',
               final_bytes_unchanged=True, all_sealed_locks_released=True, board_test='NOT_RUN')
    results.append(row)
    (ROOT/('keeper-' + mode + '.json')).write_text(json.dumps(row, indent=2), encoding='utf-8')
    print(mode, 'PASS', flush=True)

case, app = fixture('tcl-con-failure')
script = '''
set events {}
set sealed_paths {}
set fixture FIXTURE
source LOADER
rename open real_open
proc open {args} {
    set first [lindex $args 0]
    if {[string index $first 0] eq "|"} {
        set launch $first
        lset launch 4 $::fixture
        return [real_open $launch [lindex $args 1]]
    }
    return [real_open {*}$args]
}
foreach command {connect targets rst after ps7_init ps7_post_config} {
    proc $command {args} [format {lappend ::events %s} $command]
}
proc check_locked {path} {
    if {![catch {set f [real_open $path r+]; close $f}]} {error "seal writable"}
}
proc fpga {flag path} {lappend ::events fpga; check_locked $path; lappend ::sealed_paths $path}
rename source real_source
proc source {path} {lappend ::events source; check_locked $path; lappend ::sealed_paths $path}
proc dow {path} {lappend ::events dow; check_locked $path; lappend ::sealed_paths $path}
proc con {} {
    lappend ::events con
    foreach path $::sealed_paths {check_locked $path}
    error "injected-con-failure-with-locks-held"
}
set failed [catch {c1_timerfixed_load PYTHON APP PLATFORM TOOLS RECORDS 0} message]
if {!$failed || [string first "injected-con-failure-with-locks-held" $message] < 0} {error "unexpected failure: $message"}
if {[lindex $events end] ne "con" || [llength $sealed_paths] != 3} {error "con was not reached"}
foreach path $sealed_paths {set f [real_open $path r+];close $f}
puts "CON_FAILURE_RELEASE_PASS paths=$sealed_paths events=$events; NO_BOARD"
'''
for key, value in dict(FIXTURE=ROOT/'keeper_probe.py', LOADER=ENTRY/'load_timerfixed.tcl',
                       PYTHON=sys.executable, APP=app, PLATFORM=case/'continuous_platform',
                       TOOLS=case/'tools', RECORDS=case/'records').items():
    script = script.replace(key, tq(value))
path = ROOT/'con-failure.tcl'
path.write_text('if {[catch {\n' + script + '\n} msg]} {puts stderr $msg; exit 1}\nexit 0\n', encoding='utf-8')
proc = subprocess.run([TCL, str(path)], capture_output=True, text=True, timeout=35,
                      env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
row = dict(mode='tcl-con-failure', returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr, board_test='NOT_RUN')
(ROOT/'con-failure.json').write_text(json.dumps(row, indent=2), encoding='utf-8')
results.append(row)
print(json.dumps(row, indent=2))
assert proc.returncode == 0 and 'CON_FAILURE_RELEASE_PASS' in proc.stdout
(ROOT/'independent-keeper-results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
