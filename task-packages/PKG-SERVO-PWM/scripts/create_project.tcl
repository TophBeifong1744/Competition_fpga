# vivado -mode batch -source <this file> -tclargs 360|220
# 默认360；只创建单路模块仿真工程，不执行综合实现。
set max_angle_deg 360
if {$argc > 1} { error "Expected one argument: 360 or 220" }
if {$argc == 1} { set max_angle_deg [lindex $argv 0] }
if {$max_angle_deg ni {360 220}} { error "Expected 360 or 220" }
set package_root [file normalize [file join [file dirname [info script]] ..]]
set repo_root [file normalize [file join $package_root .. ..]]
set project_dir [file join $repo_root vivado build servo_pwm_$max_angle_deg]
if {[file exists $project_dir]} { error "Project output already exists: $project_dir" }
create_project servo_pwm $project_dir -part xc7z020clg400-2
set_property target_language Verilog [current_project]
set_property simulator_language Mixed [current_project]
add_files -norecurse [file join $package_root rtl motor_drive.v]
add_files -fileset sim_1 -norecurse [file join $package_root tb tb_motor_drive.v]
set reset_angle_deg [expr {$max_angle_deg == 220 ? 130 : 180}]
set_property top motor_drive [get_filesets sources_1]
set_property top tb_motor_drive [get_filesets sim_1]
set_property generic "MAX_ANGLE_DEG=$max_angle_deg RESET_ANGLE_DEG=$reset_angle_deg" [get_filesets sources_1]
set_property generic "MAX_ANGLE_DEG=$max_angle_deg" [get_filesets sim_1]
set_property xsim.simulate.runtime {1000ms} [get_filesets sim_1]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
puts "Created: [file join $project_dir servo_pwm.xpr]"
puts "Next: launch_simulation; run all; check PASS motor_drive."
