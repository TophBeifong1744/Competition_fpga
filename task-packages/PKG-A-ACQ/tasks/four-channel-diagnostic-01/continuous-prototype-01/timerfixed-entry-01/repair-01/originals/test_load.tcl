# Mocked XSDB commands: no real connect/download/compiler is ever invoked.
set test_dir [file dirname [file normalize [info script]]]
set events {}
source "$test_dir/load_timerfixed.tcl"
if {[llength $events] != 0} {error "Sourcing loader touched hardware"}
rename exec original_exec
set reject_check 0
proc exec {args} {
    lappend ::events verifier
    if {$::reject_check} {error "simulated verifier rejection"}
    return ARTIFACT_CHECK_PASS_NOT_BOARD
}
foreach name {connect targets rst after fpga ps7_init ps7_post_config dow con} {
    proc $name {args} "lappend ::events $name; return 1"
}
# Once the loader has been sourced, intercept its later ps7_init sourcing as well.
rename source original_source
proc source {args} {lappend ::events init_source}
set args [list python [file normalize dummy_app] platform tools records]
c1_timerfixed_load {*}$args
if {$events ne {verifier}} {error "Default dry run invoked hardware: $events"}
set events {}
set reject_check 1
if {![catch {c1_timerfixed_load {*}$args 0}]} {error "Rejected checker was ignored"}
if {$events ne {verifier}} {error "Failure path invoked hardware: $events"}
set events {}
set reject_check 0
c1_timerfixed_load {*}$args 0
if {$events ne {verifier connect targets rst after targets fpga targets init_source ps7_init ps7_post_config targets rst dow con}} {
    error "Wrong checked loading sequence: $events"
}
puts "MOCK_LOADER_PASS cases=4 source-only/default-dry/reject-before-connect/checked-sequence; NO_BOARD"
