# Current four-mic build ONLY. Invoked by build_current.py on copied inputs.
# No migration, save_bd_design, update_module_reference, source imports or board IO.
proc fail {message} {error $message}
proc inside {path root} {
    set p [string tolower [file normalize $path]]
    set r [string trimright [string tolower [file normalize $root]] /]
    expr {$p eq $r || [string first "$r/" "$p/"] == 0}
}
proc putfile {path text} {
    set f [open $path {WRONLY CREAT EXCL}]
    puts $f $text
    close $f
}
if {$argc != 3} {fail "Use the Python entry: root staged-xpr jobs"}
set root [file normalize [lindex $argv 0]]
set project [file normalize [lindex $argv 1]]
set jobs [lindex $argv 2]
if {![string is integer -strict $jobs] || $jobs < 1 || $jobs > 16} {fail "Invalid jobs"}
if {![file isfile "$root/preflight.json"] ||
    ![inside $project "$root/inputs/project"] ||
    ![file isfile $project]} {fail "Refuse non-snapshot project"}
if {[file normalize [pwd]] ne $root} {fail "Run working directory must equal fresh output root"}
foreach p [list "$root/reports" "$root/artifacts"] {
    if {[file exists $p]} {fail "Output subtree already exists: $p"}
}
file mkdir "$root/reports" "$root/artifacts/hw"
if {[version -short] ne "2025.2"} {fail "Vivado 2025.2 required"}
putfile "$root/reports/tool-version.txt" [version]
open_project $project
if {[get_property PART [current_project]] ne "xc7z020clg400-2"} {fail "Wrong part"}
# The registered inputs and all generated paths must remain inside the snapshot.
foreach f [get_files -all] {
    if {![inside $f "$root/inputs/project"]} {fail "External registered input: $f"}
}
foreach r [get_runs] {
    if {![inside [get_property DIRECTORY $r] "$root/inputs/project"]} {
        fail "External run directory"
    }
}
set bd [get_files -quiet */system.bd]
if {[llength $bd] != 1} {fail "Expected one system.bd"}
open_bd_design $bd
if {[llength [get_bd_cells -quiet four_mic_top_0]] != 1 ||
    [llength [get_bd_cells -quiet single_mic_top_0]] != 0} {fail "Already-adapted four-mic design required"}
foreach p {pdm_data pdm_clk1 pdm_clk2 pdm_clk3 pdm_clk4} {
    if {[llength [get_bd_ports -quiet $p]] != 1} {fail "Missing current four-mic port $p"}
}
foreach {name expected} {TOTAL_SAMPLES 32000 SAMPLES_PER_PACKET 250 WARMUP_SAMPLES 4096 FIFO_LOG2 10} {
    if {[get_property CONFIG.$name [get_bd_cells four_mic_top_0]] ne $expected} {
        fail "Changed capture parameter $name"
    }
}
# C1 adaptation occurs ONLY inside checked copied project.
set old [get_files -quiet */pcm4_capture_axis.v]
if {[llength $old]} {remove_files $old}
add_files -norecurse [list "$root/inputs/project/one.srcs/sources_1/imports/c_adapter/pcm4_continuous_axis.v"]
update_compile_order -fileset sources_1
update_module_reference -verbose [get_ips -all *four_mic_top*]
set startpin [get_bd_pins four_mic_top_0/start]
disconnect_bd_net [get_bd_nets -of_objects $startpin] $startpin
connect_bd_net [get_bd_pins axi_gpio_0/gpio_io_o] $startpin
save_bd_design

validate_bd_design -force
report_ip_status -file "$root/reports/ip-status.rpt"
foreach ip [get_ips -all -quiet] {
    if {[get_property IS_LOCKED $ip]} {fail "Locked IP requires separate review: $ip"}
}
generate_target all $bd -force
update_compile_order -fileset sources_1
synth_design -top system_wrapper -part xc7z020clg400-2
write_checkpoint "$root/artifacts/hw/post_synth.dcp"
putfile "$root/reports/synth-status.txt" "DIRECT_SYNTH_FINISHED"
set blackboxes [get_cells -hierarchical -filter {IS_BLACKBOX == 1}]
putfile "$root/reports/blackboxes.txt" $blackboxes
if {[llength $blackboxes]} {fail "Unresolved black boxes after fresh synthesis: $blackboxes"}
opt_design
place_design
route_design
write_checkpoint "$root/artifacts/hw/post_route.dcp"
putfile "$root/reports/impl-status.txt" "DIRECT_ROUTE_FINISHED"
report_timing_summary -delay_type min_max -report_unconstrained -file "$root/reports/timing-summary.rpt"
report_utilization -hierarchical -file "$root/reports/utilization.rpt"
report_drc -file "$root/reports/drc.rpt"
report_methodology -file "$root/reports/methodology.rpt"
report_io -file "$root/reports/io.rpt"
report_clocks -file "$root/reports/clocks.rpt"
set setup [get_timing_paths -delay_type max -max_paths 1]
set hold [get_timing_paths -delay_type min -max_paths 1]
if {[llength $setup] != 1 || [llength $hold] != 1} {fail "Missing timing paths"}
putfile "$root/reports/timing-values.txt" "setup_slack=[get_property SLACK $setup]\nhold_slack=[get_property SLACK $hold]"
write_bitstream "$root/artifacts/hw/system_continuous.bit"
write_hw_platform -fixed "$root/artifacts/hw/system_continuous.xsa"
close_project
puts "ISOLATED_HW_BUILD_FINISHED_NOT_BOARD_ACCEPTANCE"
