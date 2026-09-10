# Run from a temporary directory:
# vivado -mode batch -source /path/to/submission/create_project.tcl -tclargs /path/to/new/project
# Output: pcm4_signext_pack.xpr and local copies of RTL/TB under the target.
# Next: open the XPR and run Behavioral Simulation (Run All).
if {$argc != 1} { error "Usage: create_project.tcl <new-project-directory>" }
set package_dir [file dirname [file normalize [info script]]]
set target_dir [file normalize [lindex $argv 0]]
if {[file exists [file join $target_dir pcm4_signext_pack.xpr]]} {
    error "Project already exists; refusing to overwrite it"
}
create_project pcm4_signext_pack $target_dir -part xc7z020clg400-2
set_property target_language Verilog [current_project]
set_property simulator_language Verilog [current_project]
import_files -fileset sources_1 [file join $package_dir rtl pcm4_signext_pack.v]
import_files -fileset sim_1 [file join $package_dir tb tb_pcm4_signext_pack.v]
set_property top pcm4_signext_pack [get_filesets sources_1]
set_property top tb_pcm4_signext_pack [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
foreach f [get_files -all -filter {FILE_TYPE == Verilog}] {
    puts "PROJECT_SOURCE [file normalize $f]"
}
puts "PROJECT_READY [file join $target_dir pcm4_signext_pack.xpr]"
close_project
