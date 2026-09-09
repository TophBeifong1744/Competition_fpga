# 使用已保存的one工程；只注册RTL和隔离的任务一仿真文件集。
# 不改PS/BD，不启动综合实现，不下载板卡。
set root [file normalize [file join [file dirname [info script]] ..]]
set project_file {F:/College/verilog_digital_system/AMD/Competiton/one/one.xpr}
if {[llength [get_projects -quiet]] != 0} {
    error "Run this script in a separate batch Vivado process with no project open."
}
open_project $project_file
if {[get_property PART [current_project]] ne "xc7z020clg400-2"} {
    error "Unexpected part."
}
puts "ONE_TOP_BEFORE=[get_property TOP [get_filesets sources_1]]"
set rtl [file join $root rtl test_source.sv]
set tb [file join $root sim tb_test_source.sv]
if {[llength [get_files -quiet $rtl]] == 0} {
    add_files -fileset sources_1 -norecurse [list $rtl]
}
# 保留原来未完成的pl_data_sorce.sv，不删除也不改变其内容。
if {[llength [get_filesets -quiet sim_task1]] == 0} {
    create_fileset -simset sim_task1
}
# 单独添加同一RTL引用，使本仿真集不依赖原有未完成的设计源。
set_property SOURCE_SET {} [get_filesets sim_task1]
foreach f [list $rtl $tb] {
    if {[llength [get_files -quiet -of_objects [get_filesets sim_task1] $f]] == 0} {
        add_files -fileset sim_task1 -norecurse [list $f]
    }
}
set_property TOP tb_test_source [get_filesets sim_task1]
set_property TOP_AUTO_SET false [get_filesets sim_task1]
set_property xsim.simulate.runtime all [get_filesets sim_task1]
# 显式保持原板级顶层，模块尚未接入DMA。
set_property TOP system_wrapper [get_filesets sources_1]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_task1
puts "TASK1_RTL=[get_files -of_objects [get_filesets sources_1] *test_source.sv]"
puts "TASK1_SIM_TOP=[get_property TOP [get_filesets sim_task1]]"
puts "ONE_TOP_AFTER=[get_property TOP [get_filesets sources_1]]"
# 当前sim_1及其顶层保持不动，用户在GUI中可选择sim_task1运行。
close_project
puts "TASK1_ONE_REGISTRATION_PASS"
