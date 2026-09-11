# In an already-open Vivado 2025.2 project: source /path/to/sim/add_sources.tcl
# Adds the reviewed module library only. Does not wire BD, choose a system top,
# change pins, create clocks or build/download a bitstream.
if {[llength [get_projects -quiet]] != 1} {error "Open one project first"}
set ss_root [file normalize [file join [file dirname [info script]] ..]]
set ss_rtl [list rtl/common/stream_error_stats.sv rtl/common/stream_error_snapshot.v rtl/acquisition/pcm4_signext_pack.v]
foreach ss_rel $ss_rtl {
    set ss_path [file join $ss_root $ss_rel]
    if {![file exists $ss_path]} {error "Missing $ss_path"}
    add_files -norecurse -fileset sources_1 [list $ss_path]
    if {[file extension $ss_path] eq ".sv"} {
        set_property file_type SystemVerilog [get_files [list $ss_path]]
    } else {
        set_property file_type Verilog [get_files [list $ss_path]]
    }
}
update_compile_order -fileset sources_1
puts "SOUNDSIGHT_REVIEWED_LIBRARY_ADDED_NOT_BOARD_INTEGRATED"
