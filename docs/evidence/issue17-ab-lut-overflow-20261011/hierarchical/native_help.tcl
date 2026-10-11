# 核实本机报告接口；仅打开已有检查点，不打开或修改工程。
puts "VERSION=[version -short]"
puts [help open_checkpoint]
open_checkpoint {D:/vavido_project/i17_live_loop/project/par/i17_live_loop/i17_live_loop.runs/synth_1/i17_vio_board_top.dcp}
foreach cmd {report_utilization get_cells get_property list_property close_design} {
    puts "HELP_BEGIN=$cmd"
    puts [help $cmd]
    puts "HELP_END=$cmd"
}
close_design
exit 0
