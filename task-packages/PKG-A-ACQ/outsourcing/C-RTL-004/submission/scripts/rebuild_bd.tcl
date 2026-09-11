# Run: vivado -mode batch -source <submission>/scripts/rebuild_bd.tcl -tclargs <NEW external project dir>
# Outputs: c004_bd_probe.xpr, imported RTL/TB, bd_probe.bd, evidence/*.txt and *.tcl.
# Next: inspect BD port tables and warnings; independent/B review before integration.
if {$argc != 1} {error "Expected new external project directory"}
set package [file normalize [file join [file dirname [info script]] ..]]
set target [file normalize [lindex $argv 0]]
if {$target eq $package || [string first "$package/" "$target/"] == 0} {error "Project must be outside submission"}
if {[file exists $target]} {error "Use a new target directory"}
create_project c004_bd_probe $target -part xc7z020clg400-2
set_property target_language Verilog [current_project]
import_files -fileset sources_1 [list [file join $package reference stream_error_stats.sv] [file join $package rtl stream_error_stats_bd.v]]
import_files -fileset sim_1 [list [file join $package tb tb_stream_error_stats_bd.sv]]
set_property top stream_error_stats_bd [get_filesets sources_1]
set_property top tb_stream_error_stats_bd [get_filesets sim_1]
set_property -name xsim.elaborate.xelab.more_options -value { -timescale 1ns/1ps} -objects [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
foreach {pattern type} {stream_error_stats.sv SystemVerilog stream_error_stats_bd.v Verilog tb_stream_error_stats_bd.sv SystemVerilog} {
 set f [get_files -all */$pattern]
 if {[llength $f]!=1 || [get_property FILE_TYPE $f] ne $type} {error "Wrong or duplicate source: $pattern"}
 puts "SOURCE_TYPE_PASS $pattern $type $f"
}
create_bd_design bd_probe
create_bd_cell -type module -reference stream_error_stats_bd stats
set evidence [file join $target evidence]
file mkdir $evidence
proc width_of {obj} {
 set l [get_property LEFT $obj]
 set r [get_property RIGHT $obj]
 if {$l eq "" || $r eq ""} {return 1}
 return [expr {abs($l-$r)+1}]
}
proc check_ports {w evidence} {
 set f [open [file join $evidence ports-$w.txt] w]
 puts $f "COUNT_WIDTH=$w"
 if {[llength [get_bd_pins stats/*]] != 9 || [llength [get_bd_ports]] != 9} {error "Unexpected number of ports"}
 foreach {name dir} {clk I rst_n I clear I overflow_event I drop_event I overflow_count O drop_count O overflow_sticky O drop_sticky O} {
  set want 1
  if {$name in {overflow_count drop_count}} {set want $w}
  set pin [get_bd_pins stats/$name]
  set port [get_bd_ports $name]
  foreach obj [list $pin $port] {
   set actual [width_of $obj]
   set direction [get_property DIR $obj]
   puts $f "$obj direction=$direction width=$actual"
   if {$actual!=$want || $direction ne $dir} {error "Port mismatch: $obj"}
  }
 }
 close $f
 puts "PORTS_PASS COUNT_WIDTH=$w"
}
# First validate the untouched default parameter.
if {[get_property CONFIG.COUNT_WIDTH [get_bd_cells stats]] != 32} {error "Default parameter incorrect"}
make_bd_pins_external [get_bd_pins stats/*]
foreach port [get_bd_ports] {
 set old [get_property NAME $port]
 set new [regsub {_0$} $old {}]
 set_property name $new $port
}
check_ports 32 $evidence
validate_bd_design
puts "VALIDATE_PASS COUNT_WIDTH=32"
save_bd_design
write_bd_tcl -force [file join $evidence bd-default32.tcl]
# Exercise parameter edit and module refresh, keeping external widths consistent.
set_property CONFIG.COUNT_WIDTH 3 [get_bd_cells stats]
# CONFIG update synchronously refreshes module pins in Vivado 2025.2; assert the actual pins below.
foreach name {overflow_count drop_count} {set_property -dict [list LEFT 2 RIGHT 0] [get_bd_ports $name]}
if {[get_property CONFIG.COUNT_WIDTH [get_bd_cells stats]] != 3} {error "Parameter edit failed"}
check_ports 3 $evidence
validate_bd_design
puts "VALIDATE_PASS COUNT_WIDTH=3"
save_bd_design
write_bd_tcl -force [file join $evidence bd-width3.tcl]
puts "ALL BD TESTS PASS"
close_project
