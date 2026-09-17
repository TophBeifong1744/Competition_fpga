# Vivado 2025.2 non-project/OOC synthesis for the frozen frame adapter candidate.
# Run through run_ooc.ps1, or directly with one simple run name in -tclargs.

set expected_commit "a7d944a2268fff6215b2c619d2d6440235ff5752"
set expected_branch "codex/toph/frame-adapter-candidate-20260917"
set expected_sha256 "f0da9259a2c5407f003e527dc097fb57ef514a2335c20a528655427294f77585"
set expected_blob "f4091c77e0f9b5f5bb163735a750b13b4d6db8eb"
set expected_xsim_line "PASS frame_adapter RTL: frames=7 events=9"
set part "xc7z020clg400-2"
set top "pcm4_overlap_framer"
set period_ns 10.000

proc fail {message} {
    puts stderr "OOC_SYNTH_REJECTED: $message"
    exit 2
}

proc write_text {path text} {
    set f [open $path w]
    puts -nonewline $f $text
    close $f
}

proc sha256_file {path} {
    if {[catch {exec certutil -hashfile $path SHA256} output]} {
        fail "certutil SHA-256 failed for $path: $output"
    }
    if {![regexp -nocase {(^|\n)[ \t]*([0-9a-f]{64})[ \t]*(\r?\n|$)} $output -> _ hash]} {
        fail "cannot parse SHA-256 for $path"
    }
    return [string tolower $hash]
}

if {[llength $argv] != 1} {
    fail "usage: -tclargs <new_run_name>; received argc=[llength $argv] argv=$argv"
}
set run_name [lindex $argv 0]
if {![regexp {^[A-Za-z0-9_-]+$} $run_name]} {
    fail "run name must match ^[A-Za-z0-9_-]+$"
}

set script_dir [file dirname [file normalize [info script]]]
set candidate_dir [file dirname $script_dir]
set rtl [file normalize [file join $candidate_dir rtl pcm4_overlap_framer.v]]
set xdc [file normalize [file join $script_dir constraints.xdc]]
set xsim_log [file normalize [file join $candidate_dir evidence run-20260917-03 xsim.log]]
set run_dir [file normalize [file join $script_dir runs $run_name]]
set reports_dir [file join $run_dir reports]
set checkpoint_dir [file join $run_dir checkpoint]

if {[file exists $run_dir]} {
    fail "output directory already exists: $run_dir"
}
foreach required [list $rtl $xdc $xsim_log] {
    if {![file isfile $required]} { fail "missing dependency: $required" }
}

if {[catch {exec git -C $candidate_dir rev-parse --show-toplevel} repo_root]} {
    fail "candidate is not inside the expected Git worktree: $repo_root"
}
set repo_root [string trim $repo_root]
foreach ref [list "refs/heads/$expected_branch" "refs/remotes/origin/$expected_branch"] {
    if {[catch {exec git -C $repo_root rev-parse --verify $ref} actual]} {
        fail "missing fixed candidate ref $ref"
    }
    if {[string trim $actual] ne $expected_commit} {
        fail "$ref points to [string trim $actual], expected $expected_commit"
    }
}
if {[catch {exec git -C $repo_root cat-file -e "$expected_commit^{commit}"} err]} {
    fail "fixed candidate commit is unavailable: $err"
}

set source_hash [sha256_file $rtl]
if {$source_hash ne $expected_sha256} {
    fail "RTL SHA-256 $source_hash does not match frozen candidate $expected_sha256"
}
if {[catch {exec git -C $repo_root hash-object $rtl} source_blob]} {
    fail "git hash-object failed: $source_blob"
}
if {[string trim $source_blob] ne $expected_blob} {
    fail "working RTL Git blob [string trim $source_blob] differs from frozen blob $expected_blob"
}
set xsim_text [read [set xf [open $xsim_log r]]]
close $xf
if {[string first $expected_xsim_line $xsim_text] < 0} {
    fail "frozen XSim PASS marker missing from $xsim_log"
}

file mkdir $reports_dir
file mkdir $checkpoint_dir
set tool_short [version -short]
set binding "candidate_commit=$expected_commit\nbranch=$expected_branch\nrtl=$rtl\nrtl_sha256=$source_hash\nrtl_git_blob=$expected_blob\nxsim_marker=$expected_xsim_line\ntop=$top\npart=$part\nclock_name=clk\nperiod_ns=$period_ns\nflow=Vivado_non_project_out_of_context_synthesis\n"
write_text [file join $run_dir source-binding.txt] $binding
write_text [file join $run_dir tool-version.txt] "[version]\n"

puts "OOC_PRECHECK_PASS commit=$expected_commit rtl_sha256=$source_hash tool=$tool_short"
read_verilog [list $rtl]
read_xdc [list $xdc]
synth_design -mode out_of_context -top $top -part $part

if {[sha256_file $rtl] ne $expected_sha256} {
    fail "RTL changed while synthesis was running"
}
set clocks [get_clocks -quiet clk]
if {[llength $clocks] != 1} {
    fail "expected exactly one 10 ns clk constraint after synthesis"
}
set actual_period [get_property PERIOD [lindex $clocks 0]]
if {[expr {abs(double($actual_period) - $period_ns)}] > 0.0001} {
    fail "clock period is $actual_period ns, expected $period_ns ns"
}

write_checkpoint -force [file join $checkpoint_dir post_synth.dcp]
report_utilization -file [file join $reports_dir utilization.rpt]
report_utilization -hierarchical -file [file join $reports_dir utilization_hierarchical.rpt]
report_timing_summary -delay_type max -report_unconstrained -max_paths 20 \
    -file [file join $reports_dir timing_summary.rpt]
report_timing -delay_type max -sort_by slack -max_paths 50 -input_pins \
    -file [file join $reports_dir critical_paths.rpt]
check_timing -verbose -file [file join $reports_dir check_timing.rpt]
report_high_fanout_nets -max_nets 50 -file [file join $reports_dir high_fanout_nets.rpt]
report_methodology -file [file join $reports_dir methodology.rpt]
report_drc -file [file join $reports_dir drc.rpt]

set ram_report [file join $reports_dir ram_utilization.rpt]
if {[llength [info commands report_ram_utilization]] > 0} {
    if {[catch {report_ram_utilization -file $ram_report} ram_error]} {
        write_text $ram_report "report_ram_utilization failed: $ram_error\nSee utilization reports, inferred_memory_cells.txt, and Vivado log.\n"
    }
} else {
    write_text $ram_report "report_ram_utilization is unavailable in this Vivado session.\nSee utilization reports, inferred_memory_cells.txt, and Vivado log.\n"
}

array set memory_refs {}
set group_named 0
foreach cell [get_cells -hierarchical -quiet] {
    set ref [get_property REF_NAME $cell]
    set name [get_property NAME $cell]
    if {[regexp -nocase {groups} $name]} { incr group_named }
    if {[regexp {^(RAM|FIFO|SRL)} $ref]} {
        if {![info exists memory_refs($ref)]} { set memory_refs($ref) 0 }
        incr memory_refs($ref)
    }
}
set memory_text "Post-synthesis memory-related primitive inventory\n"
append memory_text "This inventory complements report_utilization; zero matches do not prove zero registers.\n"
append memory_text "cells_with_groups_in_name=$group_named\n"
foreach ref [lsort [array names memory_refs]] {
    append memory_text "$ref=$memory_refs($ref)\n"
}
write_text [file join $reports_dir inferred_memory_cells.txt] $memory_text

set status "OOC_SYNTH_COMPLETE_NOT_IMPL_NOT_BOARD\ncommit=$expected_commit\nrtl_sha256=$expected_sha256\npart=$part\nperiod_ns=$period_ns\ncheckpoint=checkpoint/post_synth.dcp\n"
write_text [file join $run_dir STATUS.txt] $status
puts "OOC_SYNTH_COMPLETE_NOT_IMPL_NOT_BOARD $run_dir"
exit 0
