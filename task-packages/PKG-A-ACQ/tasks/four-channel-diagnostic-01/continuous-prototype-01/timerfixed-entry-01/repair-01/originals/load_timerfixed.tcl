# New checked entry; sourcing only defines a procedure. No hardware action yet.
# All paths explicit. Caller chooses tools/project; verifier rejects a wrong set.
set ::c1_entry_dir [file dirname [file normalize [info script]]]
proc c1_timerfixed_load {python app platform tools_bin record_root {dry_run 1}} {
    set app [file normalize $app]
    if {$dry_run ni {0 1}} {error "dry_run must be 0 or 1"}
    # Check again every time, BEFORE connect/reset/download. Nonzero exit stops here.
    set checked [exec $python -B "$::c1_entry_dir/check_entry.py" --stage load \
        --app $app --platform $platform --tools-bin $tools_bin --record-root $record_root]
    puts $checked
    if {$dry_run} {puts "DRY_RUN: no connect/reset/program/download"; return}
    # Exact relative paths are also enforced against Vitis launch.json by the gate.
    connect -url tcp:127.0.0.1:3121
    targets -set -nocase -filter {name =~ "APU*"}
    rst -system
    after 3000
    targets -set -nocase -filter {name =~ "xc7z020"}
    fpga -file "$app/_ide/bitstream/system_continuous_20260915.bit"
    targets -set -nocase -filter {name =~ "APU*"}
    source "$app/_ide/psinit/ps7_init.tcl"
    ps7_init
    ps7_post_config
    targets -set -nocase -filter {name =~ "*Cortex-A9*#0"}
    rst -processor
    dow "$app/build/four_mic_continuous.elf"
    con
}
