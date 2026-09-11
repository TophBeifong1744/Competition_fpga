# Incremental C-adapter integration. The user must close one first.
# vivado -mode batch -source adapt_c_one.tcl -tclargs TASK OUT [integrate|build]
set task [file normalize [lindex $argv 0]]
set out [file normalize [lindex $argv 1]]
set mode [lindex $argv 2]
if {$mode eq ""} {set mode integrate}
if {$mode ni {integrate build}} {error "Unknown mode"}
set project F:/College/verilog_digital_system/AMD/Competiton/one/one.xpr
if {![file exists $task/recovery/before-c-adapter-20260911/one/one.xpr]} {error "Missing recovery backup"}
file mkdir $out
set vf [open $out/tool-version.txt w]; puts $vf [version]; close $vf
open_project $project
if {[get_property PART [current_project]] ne "xc7z020clg400-2"} {error "Unexpected part"}
set bd [get_files */system.bd]
open_bd_design $bd
if {$mode eq "integrate"} {
    # Do not modify PS, clocks, reset, GPIO, AXI fabric, addresses or DMA settings.
    set old [get_bd_cells -quiet single_mic_top_0]
    if {[llength $old]!=1} {error "Expected saved mono BD; inspect current design before adapting"}
    set dest [file dirname $project]/one.srcs/sources_1/imports/c_adapter
    file mkdir $dest
    # Preserve physical old sources; remove only duplicate module references.
    foreach name {four_mic_top.v pcm4_capture_axis.v} {
        set previous [get_files -quiet */$name]
        if {[llength $previous]} {remove_files $previous}
        file copy -force $task/source/rtl/$name $dest/$name
        add_files -norecurse $dest/$name
    }
    update_compile_order -fileset sources_1
    # Delete just the old producer and its streaming net; reconnect explicit endpoints.
    set stream_net [get_bd_intf_nets -of_objects [get_bd_intf_pins single_mic_top_0/m_axis]]
    if {[llength $stream_net]} {delete_bd_objs $stream_net}
    delete_bd_objs $old
    foreach p {pdm_clk pdm_data} {
        set port [get_bd_ports -quiet $p]
        if {[llength $port]} {delete_bd_objs $port}
    }
    create_bd_cell -type module -reference four_mic_top four_mic_top_0
    # This command takes generated IP instances, not BD cell objects.
    puts "FOUR_MODULE_IPS [get_ips -all *four_mic_top*]"
    update_module_reference -verbose [get_ips -all *four_mic_top*]
    if {[llength [get_bd_pins -quiet four_mic_top_0/pdm_clk1]]==0} {
        error "Stale generated mref/four_mic_top metadata: preserve/rename that cache while project is closed, then retry"
    }
    puts "FOUR_MODULE_PINS [get_bd_pins four_mic_top_0/*]"
    puts "FOUR_MODULE_INTERFACES [get_bd_intf_pins four_mic_top_0/*]"
    set_property -dict [list CONFIG.TOTAL_SAMPLES 32000 CONFIG.SAMPLES_PER_PACKET 250 CONFIG.WARMUP_SAMPLES 4096 CONFIG.FIFO_LOG2 10] [get_bd_cells four_mic_top_0]
    foreach {src dst} {
        clk_wiz_0/clk_out1 four_mic_top_0/aclk
        rst_ps7_0_61M/peripheral_aresetn four_mic_top_0/aresetn
        start_pulse_0/start four_mic_top_0/start
        four_mic_top_0/status axi_gpio_0/gpio2_io_i
    } {connect_bd_net [get_bd_pins $src] [get_bd_pins $dst]}
    connect_bd_intf_net [get_bd_intf_pins four_mic_top_0/m_axis] [get_bd_intf_pins axi_dma_0/S_AXIS_S2MM]
    create_bd_port -dir I -from 3 -to 0 pdm_data
    connect_bd_net [get_bd_ports pdm_data] [get_bd_pins four_mic_top_0/pdm_data]
    foreach p {pdm_clk1 pdm_clk2 pdm_clk3 pdm_clk4} {
        create_bd_port -dir O -type clk $p
        set_property CONFIG.FREQ_HZ 3072000 [get_bd_ports $p]
        connect_bd_net [get_bd_ports $p] [get_bd_pins four_mic_top_0/$p]
    }
    foreach pattern {*/single_mic_io.xdc */four_mic_io.xdc} {
        set files [get_files -quiet $pattern]
        if {[llength $files]} {set_property IS_ENABLED false $files}
    }
    file copy -force $task/source/four_mic_io.xdc $dest/c_adapter_io.xdc
    add_files -fileset constrs_1 -norecurse $dest/c_adapter_io.xdc
    validate_bd_design
    save_bd_design
    write_bd_tcl -force $out/system_c_adapter_bd.tcl
    generate_target all $bd
    make_wrapper -files $bd -top
    update_compile_order -fileset sources_1
    set_property top system_wrapper [current_fileset]
    puts "C_ADAPTER_BD_SAVED"
}
if {[llength [get_bd_cells -quiet four_mic_top_0]]!=1} {error "Missing four_mic_top_0"}
validate_bd_design
reset_run synth_1
launch_runs synth_1 -jobs 4
wait_on_run synth_1
if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {error "Synthesis failed"}
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "Implementation failed"}
open_run impl_1
report_timing_summary -delay_type min_max -report_unconstrained -file $out/timing_summary.rpt
report_utilization -hierarchical -file $out/utilization.rpt
report_drc -file $out/drc.rpt
report_methodology -file $out/methodology.rpt
report_clocks -file $out/clocks.rpt
report_io -file $out/io.rpt
set pf [open $out/clock-drivers.txt w]
foreach p {pdm_clk1 pdm_clk2 pdm_clk3 pdm_clk4} {
    set roots [all_fanin -flat -startpoints_only -to [get_ports $p]]
    puts $pf "$p <- $roots"
}
close $pf
write_hw_platform -fixed -include_bit -force $out/system_c_adapter.xsa
file copy -force [file dirname $project]/one.runs/impl_1/system_wrapper.bit $out/system_c_adapter.bit
puts "C_ADAPTER_BUILD_FINISHED_REVIEW_REPORTS_NOT_BOARD_ACCEPTANCE"
close_project
