# Vivado 2025.2 non-project/OOC synthesis for the independent BRAM candidate.
# This script does not run implementation, generate a bitstream, or touch one.

set function_commit "a7d944a2268fff6215b2c619d2d6440235ff5752"
set function_branch "codex/toph/frame-adapter-candidate-20260917"
set ooc_commit "08759a2817929d9c4d7d7345a7afca155fd30130"
set ooc_branch "codex/toph/frame-adapter-ooc-20260918"
set old_rtl_sha256 "f0da9259a2c5407f003e527dc097fb57ef514a2335c20a528655427294f77585"
set new_rtl_sha256 "389c8792fc73f2aee798564c6ea30a71eedb7dea8c4fa9ad88d86da0b8f2e52e"
set self_pass "PASS BRAM_FRAMER frames=5 events=10"
set boundary_pass "PASS BRAM_BOUNDARIES cases=6 groups=0,1023,1024,1535,1536,2048"
set equivalence_pass "PASS BRAM_EQUIVALENCE outputs=3072 events=1"
set part "xc7z020clg400-2"
set top "pcm4_overlap_framer_bram"
set period_ns 10.000

proc fail {message} {
    puts stderr "BRAM_OOC_REJECTED: $message"
    exit 2
}

proc write_text {path body} {
    set f [open $path w]
    puts -nonewline $f $body
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
set task_dir [file dirname $candidate_dir]
set rtl [file normalize [file join $candidate_dir rtl pcm4_overlap_framer_bram.v]]
set old_rtl [file normalize [file join $task_dir frame-adapter-candidate-01 rtl pcm4_overlap_framer.v]]
set xdc [file normalize [file join $script_dir constraints.xdc]]
set evidence_dir [file normalize [file join $candidate_dir evidence final_run_20260917]]
set self_log [file join $evidence_dir xsim-self.txt]
set boundary_log [file join $evidence_dir xsim-boundaries.txt]
set equivalence_log [file join $evidence_dir xsim-equivalence.txt]
set run_dir [file normalize [file join $script_dir runs $run_name]]
set reports_dir [file join $run_dir reports]
set checkpoint_dir [file join $run_dir checkpoint]

if {[file exists $run_dir]} { fail "output directory already exists: $run_dir" }
foreach required [list $rtl $old_rtl $xdc $self_log $boundary_log $equivalence_log] {
    if {![file isfile $required]} { fail "missing dependency: $required" }
}

if {[catch {exec git -C $candidate_dir rev-parse --show-toplevel} repo_root]} {
    fail "candidate is not inside the expected Git worktree: $repo_root"
}
set repo_root [string trim $repo_root]
foreach pair [list \
        [list $function_branch $function_commit] \
        [list $ooc_branch $ooc_commit]] {
    set branch [lindex $pair 0]
    set expected [lindex $pair 1]
    foreach ref [list "refs/heads/$branch" "refs/remotes/origin/$branch"] {
        if {[catch {exec git -C $repo_root rev-parse --verify $ref} actual]} {
            fail "missing fixed reference $ref"
        }
        if {[string trim $actual] ne $expected} {
            fail "$ref points to [string trim $actual], expected $expected"
        }
    }
}

set actual_new_hash [sha256_file $rtl]
set actual_old_hash [sha256_file $old_rtl]
if {$actual_new_hash ne $new_rtl_sha256} {
    fail "BRAM RTL SHA-256 $actual_new_hash differs from $new_rtl_sha256"
}
if {$actual_old_hash ne $old_rtl_sha256} {
    fail "frozen original RTL SHA-256 $actual_old_hash differs from $old_rtl_sha256"
}
foreach check [list \
        [list $self_log $self_pass] \
        [list $boundary_log $boundary_pass] \
        [list $equivalence_log $equivalence_pass]] {
    set path [lindex $check 0]
    set marker [lindex $check 1]
    set f [open $path r]
    set body [read $f]
    close $f
    if {[string first $marker $body] < 0 || [regexp -line {^FAIL } $body]} {
        fail "bound functional evidence is not clean: $path"
    }
}

file mkdir $reports_dir
file mkdir $checkpoint_dir
set binding "function_commit=$function_commit\nfunction_branch=$function_branch\nooc_commit=$ooc_commit\nooc_branch=$ooc_branch\nold_rtl_sha256=$old_rtl_sha256\nnew_rtl=$rtl\nnew_rtl_sha256=$actual_new_hash\nself_marker=$self_pass\nboundary_marker=$boundary_pass\nequivalence_marker=$equivalence_pass\ntop=$top\npart=$part\nclock_name=clk\nperiod_ns=$period_ns\nflow=Vivado_non_project_out_of_context_synthesis\n"
write_text [file join $run_dir source-binding.txt] $binding
write_text [file join $run_dir tool-version.txt] "[version]\n"

puts "BRAM_OOC_PRECHECK_PASS rtl_sha256=$actual_new_hash part=$part tool=[version -short]"
read_verilog [list $rtl]
read_xdc [list $xdc]
synth_design -mode out_of_context -top $top -part $part

if {[sha256_file $rtl] ne $new_rtl_sha256} { fail "BRAM RTL changed during synthesis" }
set clocks [get_clocks -quiet clk]
if {[llength $clocks] != 1} { fail "expected exactly one clk constraint" }
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
        write_text $ram_report "report_ram_utilization failed: $ram_error\nSee utilization and primitive inventory.\n"
    }
} else {
    write_text $ram_report "report_ram_utilization unavailable; see utilization and primitive inventory.\n"
}

array set primitive_counts {}
set detail "Post-synthesis storage primitive inventory\n"
append detail "Use with utilization reports and synthesis log; names are tool generated.\n"
foreach cell [get_cells -hierarchical -quiet] {
    set ref [get_property REF_NAME $cell]
    if {[regexp {^(RAMB18|RAMB36|RAM64M|RAM64X1D|RAM32M|RAM32X1D|RAM128X1D|FIFO)} $ref]} {
        if {![info exists primitive_counts($ref)]} { set primitive_counts($ref) 0 }
        incr primitive_counts($ref)
        append detail "cell=[get_property NAME $cell] ref=$ref\n"
    }
}
append detail "\nCOUNTS\n"
foreach ref [lsort [array names primitive_counts]] {
    append detail "$ref=$primitive_counts($ref)\n"
}
set named_groups [get_cells -hierarchical -quiet -filter {NAME =~ *groups*}]
append detail "cells_with_groups_in_name=[llength $named_groups]\n"
foreach cell $named_groups {
    append detail "groups_cell=[get_property NAME $cell] ref=[get_property REF_NAME $cell]\n"
}
write_text [file join $reports_dir storage_primitive_inventory.rpt] $detail

set status "BRAM_OOC_SYNTH_COMPLETE_NOT_IMPL_NOT_BOARD\nnew_rtl_sha256=$new_rtl_sha256\npart=$part\nperiod_ns=$period_ns\ncheckpoint=checkpoint/post_synth.dcp\n"
write_text [file join $run_dir STATUS.txt] $status
puts "BRAM_OOC_SYNTH_COMPLETE_NOT_IMPL_NOT_BOARD $run_dir"
exit 0
