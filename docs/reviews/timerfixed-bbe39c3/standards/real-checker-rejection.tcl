
set events {}
foreach name {connect targets rst after fpga dow con ps7_init ps7_post_config} {
    proc $name {args} [format {lappend ::events %s; error "FORBIDDEN board command"} $name]
}
source {F:/NUEC/review-worktrees/timerfixed-bbe39c3/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/timerfixed-entry-01/load_timerfixed.tcl}
set status [catch {
    c1_timerfixed_load {C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe} {F:/NUEC/review-evidence/timerfixed-bbe39c3/standards/missing/four_mic_continuous} {F:/NUEC/review-evidence/timerfixed-bbe39c3/standards/missing/continuous_platform} {F:/NUEC/review-evidence/timerfixed-bbe39c3/standards/missing/tools} {F:/NUEC/review-evidence/timerfixed-bbe39c3/standards/real-checker-records} 0
} message]
puts "caught=$status events=$events message=$message"
if {!$status || $events ne {} || [string first "REJECTED" $message] < 0} {error "real rejection did not fail closed"}
puts "REAL_PYTHON_REJECTION_PASS; NO_BOARD"
