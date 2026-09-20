foreach test_mode {360 220 pair} {
    set argc 1
    set argv [list $test_mode]
    source task-packages/PKG-SERVO-PWM/scripts/create_project.tcl
    set expected_top [expr {$test_mode eq "pair" ? "servo_pair" : "motor_drive"}]
    if {[get_property TOP [get_filesets sources_1]] ne $expected_top} {error "Wrong RTL top"}
    if {[get_property TOP [get_filesets sim_1]] ne "tb_$expected_top"} {error "Wrong TB top"}
    if {$test_mode ne "pair"} {
        set expected_reset [expr {$test_mode == 220 ? 130 : 180}]
        if {![string match "*RESET_ANGLE_DEG=$expected_reset*" [get_property GENERIC [get_filesets sources_1]]]} {error "Wrong reset angle"}
    }
    puts "PASS project mode=$test_mode top=$expected_top"
    close_project
}
