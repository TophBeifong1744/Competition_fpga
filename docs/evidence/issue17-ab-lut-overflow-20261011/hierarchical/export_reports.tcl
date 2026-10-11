# 从已有检查点导出资源层级；不执行综合、优化、布局、布线或任何写检查点命令。
set out [file dirname [file normalize [info script]]]
if {[version -short] ne "2025.2"} {error "Unexpected Vivado version"}
foreach {stage checkpoint} {
    synth {D:/vavido_project/i17_live_loop/project/par/i17_live_loop/i17_live_loop.runs/synth_1/i17_vio_board_top.dcp}
    opt {D:/vavido_project/i17_live_loop/project/par/i17_live_loop/i17_live_loop.runs/impl_1/i17_vio_board_top_opt.dcp}
} {
    puts "REPORT_STAGE_BEGIN=$stage INPUT=$checkpoint"
    open_checkpoint $checkpoint
    if {[get_property PART [current_design]] ne "xc7z020clg400-1"} {error "Unexpected checkpoint part"}
    # depth=0和min_count=0保留全部层级；数字为厂商利用率报告原值。
    report_utilization -hierarchical -hierarchical_depth 0 -hierarchical_min_primitive_count 0 -file [file join $out "${stage}_utilization_hierarchical.rpt"]
    report_utilization -file [file join $out "${stage}_utilization_total.rpt"]
    set fh [open [file join $out "${stage}_blackboxes.tsv"] w]
    puts $fh "instance\treference"
    set blackboxes [get_cells -hierarchical -filter {IS_BLACKBOX == 1}]
    foreach cell $blackboxes {puts $fh "[get_property NAME $cell]\t[get_property REF_NAME $cell]"}
    close $fh
    puts "BLACKBOX_COUNT=$stage [llength $blackboxes]"
    # 叶原语按直接父路径和REF_NAME汇总；原语数量不是打包后LUT站点数量。
    set counts [dict create]
    set leafs [get_cells -hierarchical -filter {IS_PRIMITIVE == 1}]
    set properties [list_property [lindex $leafs 0]]
    set has_parent [expr {[lsearch -exact $properties PARENT] >= 0}]
    foreach cell $leafs {
        set name [get_property NAME $cell]
        set ref [get_property REF_NAME $cell]
        if {$has_parent} {
            set parent [get_property PARENT $cell]
            if {$parent eq ""} {set parent "."}
        } else {
            set slash [string last / $name]
            if {$slash < 0} {set parent "."} else {set parent [string range $name 0 [expr {$slash-1}]]}
        }
        dict incr counts [list $parent $ref]
    }
    set fh [open [file join $out "${stage}_primitive_counts_by_parent.tsv"] w]
    puts $fh "parent\tprimitive_ref\tcount"
    foreach key [lsort [dict keys $counts]] {
        puts $fh "[lindex $key 0]\t[lindex $key 1]\t[dict get $counts $key]"
    }
    close $fh
    puts "PRIMITIVE_COUNT=$stage [llength $leafs] PARENT_PROPERTY_AVAILABLE=$has_parent"
    close_design
    puts "REPORT_STAGE_COMPLETE=$stage"
}
puts "EXISTING_CHECKPOINT_REPORTS_COMPLETE"
exit 0
