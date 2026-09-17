# Vivado batch: vivado -mode batch -source <this file>
# 创建独立模块仿真工程，不配置 PS，不生成 bitstream。
set package_root [file normalize [file join [file dirname [info script]] ..]]
set repo_root [file normalize [file join $package_root .. ..]]
set project_dir [file join $repo_root vivado build servo_pwm]
if {[file exists $project_dir]} {
    error "Project output already exists: $project_dir; open it or choose another directory."
}
create_project servo_pwm $project_dir -part xc7z020clg400-2
set_property target_language Verilog [current_project]
set_property simulator_language Mixed [current_project]
add_files -norecurse [file join $package_root rtl motor_drive.v]
add_files -fileset sim_1 -norecurse [file join $package_root tb tb_motor_drive.v]
set_property top motor_drive [get_filesets sources_1]
set_property top tb_motor_drive [get_filesets sim_1]
set_property xsim.simulate.runtime {400ms} [get_filesets sim_1]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
puts "Created: [file join $project_dir servo_pwm.xpr]"
puts "Next: launch_simulation; check PASS motor_drive in simulation output."
