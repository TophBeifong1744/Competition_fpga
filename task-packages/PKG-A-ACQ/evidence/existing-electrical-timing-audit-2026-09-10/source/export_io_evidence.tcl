# Read-only diagnostic: no implementation, XDC edits, bitstream or hardware access.
# vivado 2025.2 -mode batch -source export_io_evidence.tcl -tclargs <routed.dcp> <new-out-dir>
if {$argc != 2} { error "Expected routed DCP and new output directory" }
if {![string match "2025.2*" [version -short]]} { error "Vivado 2025.2 required" }
set dcp [file normalize [lindex $argv 0]]
set out [file normalize [lindex $argv 1]]
if {![file isfile $dcp]} { error "DCP missing" }
if {[file exists $out]} { error "Output exists; preserve previous evidence" }
file mkdir $out
open_checkpoint $dcp
if {[get_property PART [current_design]] ne "xc7z020clg400-2"} { error "Unexpected target" }
foreach name {pdm_clk pdm_data} {
    if {[llength [get_ports -quiet $name]] != 1} { error "Missing expected port $name" }
}
set sample [get_pins -hier -filter {NAME =~ */pdm_meta_reg/D}]
if {[llength $sample] != 1} { error "Expected exactly one archived mono sample register" }
report_timing_summary -delay_type min_max -report_unconstrained -max_paths 10 -file $out/timing-summary.rpt
report_io -file $out/io.rpt
report_clocks -file $out/clocks.rpt
check_timing -verbose -file $out/check-timing.txt
foreach delay {max min} {
    report_timing -fall_to [get_ports pdm_clk] -delay_type $delay -max_paths 2 -path_type full_clock_expanded -file $out/clock-fall-$delay.rpt
    report_timing -rise_to [get_ports pdm_clk] -delay_type $delay -max_paths 2 -path_type full_clock_expanded -file $out/clock-rise-$delay.rpt
    report_timing -from [get_ports pdm_data] -to $sample -delay_type $delay -max_paths 2 -path_type full_clock_expanded -file $out/data-$delay.rpt
}
puts "AUDIT_EXPORT_COMPLETE: unconstrained paths remain diagnostic, NOT external STA PASS"
close_design
