# Same managed AMD configuration; simulation products ONLY.
# Usage: vivado -mode batch -source generate_simulation.tcl -tclargs <new-output-dir>
if {$argc != 1} { error "expected one exclusive simulation output directory" }
if {[version -short] ne "2025.2"} { error "Vivado 2025.2 required; no implicit upgrade" }
set output_root [file normalize [lindex $argv 0]]
if {[file exists $output_root]} { error "refusing existing output directory" }
file mkdir $output_root
file mkdir [file join $output_root ip]
create_project -in_memory -part xc7z020clg400-2
create_ip -name xfft -vendor xilinx.com -library ip -version 9.1 -module_name ss_ifft25 -dir [file join $output_root ip]
set fft [get_ips ss_ifft25]
if {[get_property CORE_REVISION $fft] != 15} { error "xfft revision 15 required" }
set_property -dict [list \
    CONFIG.channels {1} \
    CONFIG.transform_length {1024} \
    CONFIG.target_clock_frequency {100} \
    CONFIG.implementation_options {radix_2_burst_io} \
    CONFIG.target_data_throughput {50} \
    CONFIG.run_time_configurable_transform_length {false} \
    CONFIG.data_format {fixed_point} \
    CONFIG.input_width {25} \
    CONFIG.phase_factor_width {24} \
    CONFIG.scaling_options {scaled} \
    CONFIG.rounding_modes {convergent_rounding} \
    CONFIG.aclken {false} \
    CONFIG.aresetn {true} \
    CONFIG.ovflo {true} \
    CONFIG.xk_index {true} \
    CONFIG.throttle_scheme {nonrealtime} \
    CONFIG.output_ordering {natural_order} \
    CONFIG.cyclic_prefix_insertion {false} \
    CONFIG.memory_options_data {block_ram} \
    CONFIG.memory_options_phase_factors {block_ram} \
    CONFIG.memory_options_reorder {block_ram} \
    CONFIG.number_of_stages_using_block_ram_for_data_and_phase_factors {0} \
    CONFIG.memory_options_hybrid {false} \
    CONFIG.complex_mult_type {use_mults_resources} \
    CONFIG.butterfly_type {use_luts} \
    CONFIG.super_sample_rates {1} \
    CONFIG.systolicfft_inv {false} \
    CONFIG.blocking_run_time_configuration {false} \
] $fft
set f [open [file join $output_root ip-properties.txt] w]
puts $f [report_property -return_string $fft]
close $f
generate_target simulation $fft
export_simulation -of_objects $fft -simulator xsim -directory [file join $output_root export] -force
close_project
exit 0
