set project [file normalize [lindex $argv 0]]
set vectors [file normalize [lindex $argv 1]]
set here [file dirname [file normalize [info script]]]
cd $project
open_project $project/fft29_budget.xpr
add_files -fileset sim_1 [list $here/tb_fft29.sv]
add_files -fileset sim_1 [list $vectors/inputs.mem $vectors/job-count.mem]
set_property top tb_fft29 [get_filesets sim_1]
set_property xsim.simulate.runtime {0ns} [get_filesets sim_1]
launch_simulation
run all
close_sim
close_project
