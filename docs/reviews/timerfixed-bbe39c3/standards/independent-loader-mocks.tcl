
set events {}
set calls {}
set fail_at ""
set reject_check 0
set cases 0
proc assert {condition message} {
    if {![uplevel 1 [list expr $condition]]} {error $message}
}
proc reset {} {set ::events {}; set ::calls {}; set ::fail_at ""; set ::reject_check 0}
proc passed {name} {incr ::cases; puts "PASS $name"}
foreach name {connect targets rst after fpga ps7_init ps7_post_config dow con} {
    proc $name {args} [format {
        lappend ::events %s
        lappend ::calls [linsert $args 0 %s]
        if {$::fail_at eq "%s"} {error "simulated %s failure"}
    } $name $name $name $name]
}
rename exec real_exec
proc exec {args} {
    lappend ::events verifier
    set ::checker_args $args
    if {$::reject_check} {error "simulated checker failure"}
    return "ARTIFACT_CHECK_PASS_NOT_BOARD"
}
source {F:/NUEC/review-worktrees/timerfixed-bbe39c3/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/timerfixed-entry-01/load_timerfixed.tcl}
assert {$events eq {}} "source invoked side effects"
passed source_no_side_effects
set entry_dir $::c1_entry_dir
set app [file join [pwd] {workspace with spaces;[literal]$dollar} four_mic_continuous]
set invoke [list {Python with spaces.exe} $app {platform with spaces} {tool bin with spaces} {record root with spaces}]
c1_timerfixed_load {*}$invoke
assert {$events eq {verifier}} "default dry touched hardware"
assert {[llength $checker_args] == 13} "wrong number of checker arguments"
assert {[lindex $checker_args 0] eq {Python with spaces.exe}} "python argument split"
assert {[lindex $checker_args 2] eq "$entry_dir/check_entry.py"} "wrong checker path"
assert {[lindex $checker_args 6] eq [file normalize $app]} "wrong app normalization"
assert {[lindex $checker_args 8] eq {platform with spaces}} "platform argument split"
assert {[lindex $checker_args 10] eq {tool bin with spaces}} "tools argument split"
assert {[lindex $checker_args 12] eq {record root with spaces}} "records argument split"
passed spaced_literal_paths_and_default_dry
foreach dry {true false yes no 2 -1 00 01 {} { 0 } 0.0} {
    reset
    assert {[catch {c1_timerfixed_load {*}$invoke $dry}]} "invalid dry accepted: $dry"
    assert {$events eq {}} "invalid dry reached verifier/hardware: $dry"
}
passed eleven_invalid_dry_modes_rejected_before_check
reset
c1_timerfixed_load {*}$invoke 1
assert {$events eq {verifier}} "explicit dry touched hardware"
passed explicit_dry
reset
set reject_check 1
assert {[catch {c1_timerfixed_load {*}$invoke 0}]} "checker rejection ignored"
assert {$events eq {verifier}} "checker rejection reached hardware"
passed rejection_before_hardware
rename source real_source
proc source {args} {
    lappend ::events init_source
    lappend ::calls [linsert $args 0 init_source]
    if {$::fail_at eq "init_source"} {error "simulated init source failure"}
}
reset
set old_pwd [pwd]
cd [file dirname $old_pwd]
c1_timerfixed_load {*}$invoke 0
cd $old_pwd
assert {[lindex $checker_args 2] eq "$entry_dir/check_entry.py"} "checker changed with cwd"
assert {$events eq {verifier connect targets rst after targets fpga targets init_source ps7_init ps7_post_config targets rst dow con}} "wrong sequence"
assert {[lindex $calls 0] eq {connect -url tcp:127.0.0.1:3121}} "connection mismatch"
assert {[lindex $calls 5] eq [list fpga -file "$app/_ide/bitstream/system_continuous_20260915.bit"]} "bit path mismatch"
assert {[lindex $calls 7] eq [list init_source "$app/_ide/psinit/ps7_init.tcl"]} "init path mismatch"
assert {[lindex $calls 12] eq [list dow "$app/build/four_mic_continuous.elf"]} "ELF path mismatch"
passed fixed_checker_after_cd_and_matching_hardware_paths
foreach step {connect targets rst after fpga init_source ps7_init ps7_post_config dow con} {
    reset
    set fail_at $step
    assert {[catch {c1_timerfixed_load {*}$invoke 0}]} "failed step ignored: $step"
    assert {[lindex $events end] eq $step} "commands continued past failed step: $step"
}
passed ten_hardware_step_failures_stop_immediately
puts "INDEPENDENT_LOADER_PASS cases=$cases; NO_BOARD"
