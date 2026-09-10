open_project D:/vavido_project/c004_bd_probe_v1/c004_bd_probe.xpr
open_bd_design [get_files */bd_probe.bd]
help update_module_reference
set_property CONFIG.COUNT_WIDTH 3 [get_bd_cells stats]
puts "AFTER_CONFIG WIDTH=[get_property LEFT [get_bd_pins stats/overflow_count]]"
if {[catch {update_module_reference [get_bd_cells stats]} msg opts]} {puts "REFRESH_RESULT message=$msg options=$opts"}
puts "AFTER_REFRESH WIDTH=[get_property LEFT [get_bd_pins stats/overflow_count]]"
foreach name {overflow_count drop_count} {set_property -dict [list LEFT 2 RIGHT 0] [get_bd_ports $name]}
validate_bd_design
puts "VALIDATE_DIAGNOSTIC_PASS"
close_project
