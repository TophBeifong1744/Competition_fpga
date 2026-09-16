# Deny hardware before even sourcing the author's test.
foreach name {connect targets rst fpga dow con ps7_init ps7_post_config} {
    proc $name {args} {error "FORBIDDEN real hardware action"}
}
source {F:/NUEC/review-worktrees/timerfixed-bbe39c3/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/timerfixed-entry-01/test_load.tcl}
