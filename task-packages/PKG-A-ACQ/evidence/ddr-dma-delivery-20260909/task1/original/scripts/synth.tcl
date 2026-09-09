set root [file normalize [file join [file dirname [info script]] ..]]
puts "TOOL_VERSION=[version -short]"
read_verilog -sv [list [file join $root rtl test_source.sv]]
synth_design -top test_source -part xc7z020clg400-2 -mode out_of_context
report_utilization -file [file join $root evidence utilization_ooc.rpt]
report_drc -file [file join $root evidence drc_ooc.rpt]
write_checkpoint -force [file join $root evidence test_source_ooc.dcp]
puts "TASK1_OOC_SYNTH_PASS"
