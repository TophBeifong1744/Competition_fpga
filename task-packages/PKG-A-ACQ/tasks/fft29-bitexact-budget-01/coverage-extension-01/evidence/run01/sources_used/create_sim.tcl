# Simulation-only extension; configuration block is reused verbatim from ../source/build.tcl.
# Source this file in an EMPTY Vivado 2025.2 session, then call fft29_coverage_create.
proc fft29_coverage_create {out vectors} {
    if {[version -short] ne "2025.2"} {error "Vivado 2025.2 required"}
    if {[current_project -quiet] ne ""} {error "Close the current project first; do not use one"}
    set out [file normalize $out]
    set vectors [file normalize $vectors]
    if {[file exists $out]} {error "Output already exists; retain it and choose a new run"}
    foreach name {inputs.mem job-count.mem} {
        if {![file isfile $vectors/$name]} {error "Missing prepared vectors: $name"}
    }
    set f [open $vectors/job-count.mem r]
    set jobs [string trim [read $f]]
    close $f
    if {$jobs ne "817"} {error "Expected 817 jobs (136 cases x 6 plus one repeat)"}
    set here $::fft29_coverage_script_dir
    file mkdir $out
    cd $out
    create_project fft29_budget $out -part xc7z020clg400-2
    set_property target_language Verilog [current_project]
    set_property simulator_language Mixed [current_project]
    set_param general.maxThreads 2
    create_ip -name xfft -vendor xilinx.com -library ip -version 9.1 -module_name ss_fft29
    set_property -dict [list \
     CONFIG.transform_length {1024} \
     CONFIG.implementation_options {radix_2_burst_io} \
     CONFIG.data_format {fixed_point} \
     CONFIG.input_width {29} \
     CONFIG.phase_factor_width {24} \
     CONFIG.scaling_options {scaled} \
     CONFIG.rounding_modes {convergent_rounding} \
     CONFIG.output_ordering {natural_order} \
     CONFIG.throttle_scheme {nonrealtime} \
     CONFIG.aresetn {true} CONFIG.ovflo {true} CONFIG.xk_index {true} \
     CONFIG.target_clock_frequency {100} \
     CONFIG.ACLK_INTF.FREQ_HZ {100000000}] [get_ips ss_fft29]
    set f [open $out/tool-version.txt w]
    puts $f [version]
    puts $f "PART=[get_property PART [current_project]]"
    puts $f "IPDEF=[get_property IPDEF [get_ips ss_fft29]]"
    close $f
    report_property -all [get_ips ss_fft29] -file $out/ip-properties.txt
    # Generate IP simulation support only; no launch_runs, synth_design, place or route.
    generate_target simulation [get_ips ss_fft29]
    add_files -fileset sim_1 [list $here/tb_fft29.sv $vectors/inputs.mem $vectors/job-count.mem]
    set_property top tb_fft29 [get_filesets sim_1]
    set_property xsim.simulate.runtime {0ns} [get_filesets sim_1]
    launch_simulation
    puts "FFT29 coverage simulation is open at 0 ns. Execute run all in the Tcl Console."
}
set ::fft29_coverage_script_dir [file dirname [file normalize [info script]]]
