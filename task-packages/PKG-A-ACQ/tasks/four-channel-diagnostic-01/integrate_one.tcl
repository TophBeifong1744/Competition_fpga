# Run only with one closed and recovery backup already verified.
set task [file normalize [lindex $argv 0]]
set out [file normalize [lindex $argv 1]]
set project F:/College/verilog_digital_system/AMD/Competiton/one/one.xpr
if {![file exists $task/recovery/mono-before-integration/one/one.xpr]} {error "Missing recovery backup"}
file mkdir $out
set vf [open $out/tool-version.txt w]; puts $vf [version]; close $vf
open_project $project
set bd [get_files */system.bd]
open_bd_design $bd
if {[llength [get_bd_cells -quiet single_mic_top_0]] != 1} {error "Expected original single_mic_top_0; refuse duplicate integration"}
set dest [file dirname $project]/one.srcs/sources_1/imports/four_mic
file mkdir $dest
foreach name {four_mic_top.v pcm4_capture_axis.v} {
    if {![file exists $dest/$name]} {file copy $task/source/rtl/$name $dest/$name}
    add_files -norecurse $dest/$name
}
# Reuse original pdm_cic3; caller verifies its hash against the candidate.
update_compile_order -fileset sources_1
create_bd_cell -type module -reference four_mic_top four_mic_top_0
set_property -dict [list CONFIG.TOTAL_SAMPLES 32000 CONFIG.SAMPLES_PER_PACKET 250 CONFIG.WARMUP_SAMPLES 4096 CONFIG.FIFO_LOG2 10] [get_bd_cells four_mic_top_0]
foreach pin {aclk aresetn start status pdm_clk} {
    set net [get_bd_nets -of_objects [get_bd_pins single_mic_top_0/$pin]]
    if {[llength $net]!=1} {error "Missing $pin net"}
    disconnect_bd_net $net [get_bd_pins single_mic_top_0/$pin]
    connect_bd_net -net $net [get_bd_pins four_mic_top_0/$pin]
}
set axis [get_bd_intf_nets -of_objects [get_bd_intf_pins single_mic_top_0/m_axis]]
disconnect_bd_intf_net $axis [get_bd_intf_pins single_mic_top_0/m_axis]
connect_bd_intf_net -intf_net $axis [get_bd_intf_pins four_mic_top_0/m_axis]
set data_net [get_bd_nets -of_objects [get_bd_pins single_mic_top_0/pdm_data]]
delete_bd_objs $data_net
delete_bd_objs [get_bd_ports pdm_data]
create_bd_port -dir I -from 3 -to 0 pdm_data
connect_bd_net [get_bd_ports pdm_data] [get_bd_pins four_mic_top_0/pdm_data]
delete_bd_objs [get_bd_cells single_mic_top_0]
set old_xdc [get_files -quiet */single_mic_io.xdc]
if {[llength $old_xdc]!=1} {error "Old XDC not uniquely found"}
set_property IS_ENABLED false $old_xdc
file copy $task/source/four_mic_io.xdc $dest/four_mic_io.xdc
add_files -fileset constrs_1 -norecurse $dest/four_mic_io.xdc
validate_bd_design
save_bd_design
write_bd_tcl -force $out/system_four_bd.tcl
generate_target all $bd
make_wrapper -files $bd -top
update_compile_order -fileset sources_1
set_property top system_wrapper [current_fileset]
reset_run synth_1
launch_runs synth_1 -jobs 4
wait_on_run synth_1
if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {error "Synthesis failed"}
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "Implementation/bitstream failed"}
open_run impl_1
report_timing_summary -delay_type min_max -report_unconstrained -file $out/timing_summary.rpt
report_utilization -hierarchical -file $out/utilization.rpt
report_drc -file $out/drc.rpt
report_methodology -file $out/methodology.rpt
report_clocks -file $out/clocks.rpt
write_hw_platform -fixed -include_bit -force $out/system_four_mic.xsa
file copy -force [file dirname $project]/one.runs/impl_1/system_wrapper.bit $out/system_four_mic.bit
puts "FOUR_BUILD_FINISHED_REVIEW_REPORTS_NOT_BOARD_ACCEPTANCE"
close_project
