# 中文用途：冻结旧/新单模块同选项资源对比；不打开原工程、不执行整机或实现。
# Command: vivado -mode batch -source diagnostic_synth.tcl -log diagnostic_synth.log -journal diagnostic_synth.jou
# Outputs: synth_before/utilization.rpt, synth_after/utilization.rpt and matching hierarchy/primitive tables.
# Next: independent review; standalone counts are not full-project fit or timing sign-off.
set root [file dirname [file normalize [info script]]]
set candidate [file normalize [file join $root ../../project/rtl/c_board/i17_vio_evidence.sv]]
set baseline [file join $root baseline/i17_vio_evidence.sv]
puts [version]
foreach label {before after} source [list $baseline $candidate] {
    set folder [file join $root synth_$label]
    if {[file exists $folder]} {error "Refuse to overwrite diagnostic $folder"}
    file mkdir $folder
    cd $folder
    create_project -in_memory -part xc7z020clg400-1
    read_verilog -sv $source
    read_xdc [file join $root diagnostic_clock.xdc]
    synth_design -top i17_vio_evidence -part xc7z020clg400-1 -mode out_of_context -flatten_hierarchy rebuilt
    report_utilization -file utilization.rpt
    # 合成网表时延仅作组合深度诊断，不代表布局布线或完整I/O约束的STA。
    report_timing_summary -file synthesis_timing.rpt
    report_utilization -hierarchical -hierarchical_depth 0 -hierarchical_min_primitive_count 0 -file hierarchy.rpt
    set counts [dict create]
    foreach cell [get_cells -hierarchical -filter {IS_PRIMITIVE}] {
        dict incr counts [get_property REF_NAME $cell]
    }
    set stream [open primitive-counts.tsv w]
    puts $stream "primitive\tcount"
    foreach key [lsort [dict keys $counts]] {puts $stream "$key\t[dict get $counts $key]"}
    close $stream
    puts "SINGLE_MODULE_DIAGNOSTIC_COMPLETE $label source=$source"
    close_project
}
exit 0
