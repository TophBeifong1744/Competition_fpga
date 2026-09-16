# Keeper holds mandatory Windows locks through all file-consuming calls.
# Sourcing defines procedures only; default remains dry, no board commands.
set c1_source [info script]
if {[file pathtype $c1_source] ne "absolute"} {set c1_source [file join [pwd] $c1_source]}
set ::c1_entry_dir [file dirname $c1_source]
proc c1_guard_ping {channel} {
    puts $channel PING
    flush $channel
    if {[gets $channel reply] < 0 || $reply ne "GUARD_ALIVE"} {
        error "Protected artifact keeper is unavailable: $reply"
    }
}
proc c1_timerfixed_load {python app platform tools_bin record_root {dry_run 1}} {
    if {$dry_run ni {0 1}} {error "dry_run must be 0 or 1"}
    foreach path [list $python $app $platform $tools_bin $record_root] {
        if {[file pathtype $path] ne "absolute"} {error "All load inputs must be absolute paths"}
    }
    set argv [list $python -u -B "$::c1_entry_dir/guarded_load.py" \
        --app $app --platform $platform --tools-bin $tools_bin --record-root $record_root]
    set channel [open [linsert $argv 0 |] r+]
    fconfigure $channel -buffering line -encoding utf-8 -translation {auto lf}
    set ready 0
    try {
        if {[gets $channel line] < 0 || [llength $line] != 4 || [lindex $line 0] ne "GUARD_READY_V1"} {
            error "No protected artifact receipt; no hardware actions permitted"
        }
        set ready 1
        set paths {}
        foreach value [lrange $line 1 3] {
            lappend paths [encoding convertfrom utf-8 [binary decode base64 $value]]
        }
        lassign $paths elf bit init
        c1_guard_ping $channel
        if {$dry_run} {
            puts "DRY_RUN: sealed artifacts checked; no connect/reset/program/download"
        } else {
            connect -url tcp:127.0.0.1:3121
            targets -set -nocase -filter {name =~ "APU*"}
            rst -system
            after 3000
            c1_guard_ping $channel
            targets -set -nocase -filter {name =~ "xc7z020"}
            fpga -file $bit
            c1_guard_ping $channel
            targets -set -nocase -filter {name =~ "APU*"}
            source $init
            ps7_init
            ps7_post_config
            targets -set -nocase -filter {name =~ "*Cortex-A9*#0"}
            rst -processor
            c1_guard_ping $channel
            dow $elf
            c1_guard_ping $channel
            con
        }
    } finally {
        if {$ready} {
            catch {puts $channel RELEASE; flush $channel; gets $channel reply}
        }
        close $channel
    }
}
