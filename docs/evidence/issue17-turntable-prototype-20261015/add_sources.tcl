# 中文用途：只给既有工程添加准确增量源；不建第三工程、不连接顶层、不运行构建。
set manifest_dir [file dirname [file normalize [info script]]]
set repo_root [file normalize [file join $manifest_dir ../../..]]
if {[llength [get_projects -quiet]] != 1} { error "Open exactly the authorized existing project first" }
set rels {
    task-packages/PKG-C-I17-VIO-OPT-20261011/project/rtl/integration/signed_angle_map.sv
    task-packages/PKG-C-I17-VIO-OPT-20261011/project/rtl/runtime/angle_command_gate.sv
    task-packages/PKG-C-I17-VIO-OPT-20261011/project/rtl/runtime/runtime_servo_slice.sv
    task-packages/PKG-C-I17-VIO-OPT-20261011/project/rtl/c_board/motor_drive.v
    project/rtl/c_board/i17_turntable_known_source.sv
    project/rtl/c_board/i17_turntable_pwm_guard.sv
    project/rtl/c_board/i17_turntable_result_slice.sv
    project/rtl/c_board/i17_turntable_prototype.sv
}
set missing {}
foreach rel $rels {
    set exact [file normalize [file join $repo_root $rel]]
    if {![file isfile $exact]} { error "Missing frozen source $exact" }
    set matches [get_files -quiet */[file tail $exact]]
    foreach match $matches {
        if {[file normalize $match] ne $exact} {
            error "Same-name source already owned by project: $match; reconcile exact identity, do not duplicate"
        }
    }
    puts "TURNTABLE_SOURCE $exact"
    if {[llength $matches] == 0} { lappend missing $exact }
}
if {![info exists I17_TURNTABLE_ADD_SOURCES] || $I17_TURNTABLE_ADD_SOURCES != 1} {
    puts "READ_ONLY_LIST: validate exact source identities and pending STOP/engineering seam before adding"
} elseif {[llength $missing] != 0} {
    add_files -norecurse -fileset sources_1 $missing
    foreach f $missing {
        if {[file extension $f] eq ".sv"} { set_property file_type SystemVerilog [get_files $f] }
    }
    puts "Sources added only: no top/STOP wiring, constraints, synthesis, implementation or programming performed"
}
