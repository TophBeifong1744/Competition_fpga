# vivado -mode batch -source build.tcl -tclargs E:/ss-fft-build-01
set out [file normalize [lindex $argv 0]]
if {[file exists $out]} {error "Output already exists: $out"}
if {[version -short] ne "2025.2"} {error "Vivado 2025.2 required"}
file mkdir $out
cd $out
create_project fft_budget $out -part xc7z020clg400-2
set_property target_language Verilog [current_project]
set_property simulator_language Mixed [current_project]
set_param general.maxThreads 2
create_ip -name xfft -vendor xilinx.com -library ip -version 9.1 -module_name ss_fft
set_property -dict [list \
 CONFIG.transform_length {1024} \
 CONFIG.implementation_options {radix_2_burst_io} \
 CONFIG.data_format {fixed_point} \
 CONFIG.input_width {25} \
 CONFIG.phase_factor_width {24} \
 CONFIG.scaling_options {scaled} \
 CONFIG.rounding_modes {convergent_rounding} \
 CONFIG.output_ordering {natural_order} \
 CONFIG.throttle_scheme {nonrealtime} \
 CONFIG.aresetn {true} CONFIG.ovflo {true} CONFIG.xk_index {true} \
 CONFIG.target_clock_frequency {100} \
 CONFIG.ACLK_INTF.FREQ_HZ {100000000}] [get_ips ss_fft]
report_property -all [get_ips ss_fft] -file $out/ip-properties.txt
generate_target all [get_ips ss_fft]
create_ip_run [get_ips ss_fft]
launch_runs ss_fft_synth_1 -jobs 2
wait_on_run ss_fft_synth_1
if {[get_property PROGRESS [get_runs ss_fft_synth_1]] ne "100%"} {error "OOC synthesis failed"}
open_run ss_fft_synth_1
report_utilization -file $out/utilization.rpt
report_timing_summary -report_unconstrained -file $out/synth-timing.rpt
close_project
