"""Actual Tcl/Python pipe and mandatory locks with mock hardware; no board."""
import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ENTRY=Path(__file__).resolve().parents[1]
TCL=os.environ.get('TF_TCL','F:/AMD/2025.2/tps/win64/git-2.50.0/mingw64/bin/tclsh86.exe')
def tq(s):
    return '[encoding convertfrom utf-8 [binary decode base64 {'+base64.b64encode(str(s).encode()).decode()+'}]]'

class LoaderTests(unittest.TestCase):
    def run_case(self,mode='load',replacement='old',fail='',dry='0'):
        with tempfile.TemporaryDirectory(prefix='tf loader ') as temp:
            root=Path(temp)
            app=root/'four_mic_continuous'
            source=ENTRY/'user-build-20260916-01/app'
            shutil.copytree(source,app)
            ref=ENTRY.parent/'board-run-20260915-02/runtime'
            (app/'_ide/bitstream').mkdir()
            (app/'_ide/psinit').mkdir()
            shutil.copyfile(ref/'system_continuous_20260915.bit',app/'_ide/bitstream/system_continuous_20260915.bit')
            shutil.copyfile(ref/'ps7_init.tcl',app/'_ide/psinit/ps7_init.tcl')
            replacement_file=(ENTRY.parent/'board-run-20260915-01/four_mic_continuous_prefix.elf'
                              if replacement=='old' else ref/'four_mic_continuous.elf')
            if mode=='reject':
                shutil.copyfile(replacement_file,app/'build/four_mic_continuous.elf')
            script='''set events {}
set blocked 0
set observed {}
set mode MODE
set fail FAIL
set app APP
set replacement REPLACEMENT
set fixture FIXTURE
set keepers {}
proc hit {name} {
    lappend ::events $name
    if {$name eq $::fail} {error "injected step failure"}
}
source LOADER
if {$events ne {}} {error "source had side effects"}
rename open actual_open
proc open {args} {
    set first [lindex $args 0]
    if {[string index $first 0] eq "|"} {
        set launch $first
        lset launch 4 $::fixture
        return [actual_open $launch [lindex $args 1]]
    }
    return [actual_open {*}$args]
}
proc readbin {p} {set f [actual_open $p rb];set b [read $f];close $f;return $b}
set initialElf [readbin "$app/build/four_mic_continuous.elf"]
set initialBit [readbin "$app/_ide/bitstream/system_continuous_20260915.bit"]
set initialInit [readbin "$app/_ide/psinit/ps7_init.tcl"]
proc checkfile {name path wanted} {
    hit $name
    if {[string first "sealed" $path] < 0} {error "not a sealed artifact"}
    if {[readbin $path] ne $wanted} {error "download bytes differ from checked input"}
    if {![catch {set f [actual_open $path wb];close $f}]} {error "sealed artifact writable"}
    incr ::blocked
    lappend ::observed $path
}
proc connect {args} {hit connect}
proc targets {args} {hit targets}
proc rst {args} {hit rst}
proc after {args} {
    hit after
    if {$::mode eq "race"} {
        file copy -force $::replacement "$::app/build/pending.elf"
        file rename -force "$::app/build/pending.elf" "$::app/build/four_mic_continuous.elf"
        foreach rel {_ide/bitstream/system_continuous_20260915.bit _ide/psinit/ps7_init.tcl} {
            set f [actual_open "$::app/$rel" wb];puts $f REPLACED;close $f
        }
    }
}
proc fpga {flag path} {
    if {$flag ne "-file"} {error "wrong fpga argument"}
    checkfile fpga $path $::initialBit
}
rename source actual_source
proc source {path} {checkfile source $path $::initialInit}
proc ps7_init {} {hit ps7_init}
proc ps7_post_config {} {hit ps7_post_config}
proc dow {path} {checkfile dow $path $::initialElf}
proc con {} {hit con}
set rejected [catch {c1_timerfixed_load PYTHON $app PLATFORM TOOLS RECORDS CALLSUFFIX} message]
if {$mode eq "reject" || $fail ne ""} {
    if {!$rejected || [lsearch -exact $events con]>=0} {error "failure did not stop load"}
    if {$mode eq "reject" && $events ne {}} {error "gate rejection touched hardware"}
    if {$fail ne "" && ([lindex $events end] ne $fail || [string first "injected step failure" $message]<0)} {
        error "requested failure point was not reached: $message events=$events"
    }
} else {
    if {$rejected} {error $message}
    if {DRY eq "1" && $events ne {}} {error "dry mode touched hardware"}
    if {DRY eq "0" && ($blocked != 3 || [lindex $events end] ne "con")} {error "incomplete sealed sequence"}
}
# The keeper must release its locks on success AND all injected errors.
foreach p $observed {set f [actual_open $p ab];close $f}
puts "SEALED_MOCK_PASS mode=$mode fail=$fail blocked=$blocked events=$events; NO_BOARD"
'''
            for key,value in dict(MODE=tq(mode),FAIL=tq(fail),APP=tq(app),REPLACEMENT=tq(replacement_file),
                FIXTURE=tq(ENTRY/'repair-01/keeper_fixture.py'),LOADER=tq(ENTRY/'load_timerfixed.tcl'),
                PYTHON=tq(sys.executable),PLATFORM=tq(root/'continuous_platform'),TOOLS=tq(root/'tools'),
                RECORDS=tq(root/'records'),CALLSUFFIX='' if dry=='default' else dry,
                DRY='1' if dry=='default' else dry).items():
                script=script.replace(key,value)
            wrapped='if {[catch {\n'+script+'\n} errorMessage]} {puts stderr $errorMessage; exit 1}\nexit 0\n'
            env=dict(os.environ,TF_REPAIR_ENTRY=str(ENTRY),PYTHONDONTWRITEBYTECODE='1')
            p=subprocess.run([TCL],input=wrapped,cwd=root,env=env,capture_output=True,text=True,timeout=40)
            output=os.environ.get('TF_CASE_LOG_ROOT')
            if output:
                dest=Path(output)/(mode+'-'+replacement+'-'+(fail or 'none')+'-'+dry+'.json')
                dest.write_text(json.dumps(dict(argv=[TCL],stdin=wrapped,returncode=p.returncode,
                    stdout=p.stdout,stderr=p.stderr,scope='real file locks/Tcl/ELF; gate prerequisites and hardware mocked'),indent=2),encoding='utf-8')
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            self.assertIn('SEALED_MOCK_PASS',p.stdout)
    def test_default_dry_no_hardware(self):self.run_case(dry='default')
    def test_correct_sealed_load(self):self.run_case()
    def test_replacement_wrong_timer_not_downloaded(self):self.run_case(mode='race')
    def test_replacement_other_valid_elf_not_downloaded(self):self.run_case(mode='race',replacement='fixed')
    def test_rejection_before_hardware(self):self.run_case(mode='reject')
    def test_steps_fail_closed_and_release(self):
        for step in ('connect','targets','rst','after','fpga','source','ps7_init','ps7_post_config','dow'):
            with self.subTest(step=step):self.run_case(fail=step)

if __name__=='__main__':unittest.main()
