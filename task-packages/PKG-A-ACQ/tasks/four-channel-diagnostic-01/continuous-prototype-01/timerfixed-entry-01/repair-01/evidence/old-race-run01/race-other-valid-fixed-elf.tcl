
set events {}
set app {E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/results/tmp/timer-repair-old-race-01/race-other-valid-fixed-elf/four_mic_continuous}
set replacement {E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/board-run-20260915-02/runtime/four_mic_continuous.elf}
set elf "$app/build/four_mic_continuous.elf"
foreach name {connect targets rst fpga ps7_init ps7_post_config con} {
    proc $name {args} [format {lappend ::events %s} $name]
}
rename exec actual_exec
proc exec {args} {
    lappend ::events verifier
    if {[lindex $args 6] ne $::app} {error "unexpected checked app"}
    return [actual_exec {C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe} {-B} {E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/results/tmp/timer-repair-old-race-01/reproduce_artifact_race.py} {E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/timerfixed-entry-01/user-build-20260916-01/app/build/CMakeFiles/four_mic_continuous.elf.dir/main.c.obj} {E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/results/tmp/timer-repair-old-race-01/race-other-valid-fixed-elf/four_mic_continuous/build/four_mic_continuous.elf}]
}
proc after {args} {
    lappend ::events artifact_replaced_during_after
    file copy -force $::replacement "$::elf.pending"
    file rename -force "$::elf.pending" $::elf
}
proc dow {path} {
    lappend ::events dow
    set f [open $path rb]; set observed [read $f]; close $f
    set f [open $::replacement rb]; set replaced [read $f]; close $f
    if {$observed ne $replaced} {error "race fixture did not swap loaded bytes"}
    puts "MOCK_DOW_READ_UNCHECKED_REPLACEMENT bytes=[string length $observed] path=$path"
}
source {E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/timerfixed-entry-01/load_timerfixed.tcl}
rename source actual_source
proc source {args} {lappend ::events init_source}
c1_timerfixed_load python $app platform tools records 0
if {[lindex $events end] ne "con"} {error "loader did not reach mocked continue"}
puts "RACE_REPRODUCED events=$events; NO_BOARD"
