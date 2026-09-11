# Read implemented netlist only; does not rebuild or program hardware.
set out [file normalize [lindex $argv 0]]
open_project F:/College/verilog_digital_system/AMD/Competiton/one/one.xpr
open_run impl_1
set f [open $out w]
puts $f "port\tcell\tprimitive\tINIT\tC\tD\tCE\tR\tS"
foreach port {pdm_clk1 pdm_clk2 pdm_clk3 pdm_clk4} {
    set roots [all_fanin -flat -startpoints_only -to [get_ports $port]]
    set cells [get_cells -of_objects $roots]
    if {[llength $cells]!=1} {error "Unexpected clock output startpoint: $port $roots $cells"}
    set cell [lindex $cells 0]
    set row [list $port $cell [get_property REF_NAME $cell] [get_property INIT $cell]]
    foreach pin {C D CE R S} {
        set pp [get_pins -quiet $cell/$pin]
        if {[llength $pp]} {
            lappend row [join [lsort [get_nets -of_objects $pp]] {;}]
        } else {lappend row "-"}
    }
    puts $f [join $row "\t"]
}
close $f
close_project
