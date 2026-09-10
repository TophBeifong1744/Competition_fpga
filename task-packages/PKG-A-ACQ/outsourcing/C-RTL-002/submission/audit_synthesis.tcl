# Run: vivado -mode batch -source <submission>/audit_synthesis.tcl -log <external>/synthesis.log -nojournal -tclargs <NEW-output-directory>
# Outputs: utilization-width*.rpt and summary.txt; next: review structure/resources.
# This is out-of-context synthesis, not placement/routing or timing sign-off.
if {[llength $argv] != 1} {error "Provide one new external output directory"}
set package_dir [file normalize [file dirname [info script]]]
set output_dir [file normalize [lindex $argv 0]]
if {[file exists $output_dir]} {error "Use a new output directory"}
if {$output_dir eq $package_dir || [string first "$package_dir/" "$output_dir/"] == 0} {error "Output must be outside submission"}
if {[version -short] ne "2025.2"} {error "Vivado 2025.2 required"}
file mkdir $output_dir
set summary [open [file join $output_dir summary.txt] w]
foreach width {1 32 64} {
    create_project -in_memory -part xc7z020clg400-2
    read_verilog [file join $package_dir rtl stream_error_snapshot.v]
    synth_design -top stream_error_snapshot -part xc7z020clg400-2 -mode out_of_context -generic COUNT_WIDTH=$width
    report_utilization -file [file join $output_dir utilization-width$width.rpt]
    set ff [llength [get_cells -hier -filter {REF_NAME == FDRE}]]
    set latch [llength [get_cells -hier -filter {REF_NAME =~ LD*}]]
    set async_ff [llength [get_cells -hier -filter {REF_NAME == FDCE || REF_NAME == FDPE}]]
    set expected [expr {2*$width+3}]
    if {$ff != $expected || $latch != 0 || $async_ff != 0} {
        error "Unexpected structure width=$width FF=$ff expected=$expected latch=$latch async=$async_ff"
    }
    puts $summary "PASS WIDTH=$width FDRE=$ff EXPECTED=$expected LATCH=$latch ASYNC_FF=$async_ff"
    flush $summary
    close_project
}
puts $summary "ALL SYNTHESIS CHECKS PASS"
close $summary
puts "ALL SYNTHESIS CHECKS PASS: $output_dir"
