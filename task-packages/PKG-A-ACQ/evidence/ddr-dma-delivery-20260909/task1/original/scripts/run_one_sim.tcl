set root [file normalize [file join [file dirname [info script]] ..]]
open_project {F:/College/verilog_digital_system/AMD/Competiton/one/one.xpr}
if {[get_property TOP [get_filesets sources_1]] ne "system_wrapper"} {
    error "Unexpected board top."
}
if {[get_property TOP [get_filesets sim_task1]] ne "tb_test_source"} {
    error "Task1 simulation fileset missing."
}
set original_sim [current_fileset -simset]
launch_simulation -simset sim_task1 -mode behavioral
run all
close_sim
set log_path {F:/College/verilog_digital_system/AMD/Competiton/one/one.sim/sim_task1/behav/xsim/simulate.log}
set log_handle [open $log_path r]
set log_text [read $log_handle]
close $log_handle
if {![string match "*ALL TASK1 TESTS PASS*" $log_text]} {
    error "Task1 did not reach its self-check completion marker."
}
current_fileset -simset $original_sim
close_project
puts "TASK1_ONE_SIMULATION_PASS"
