# XSDB operator entry. Sourcing only defines the procedure; DOES NOT touch board.
# First verify release hashes on PC. Then call with explicit release directory.
proc continuous_load {release_dir} {
    set root [file normalize $release_dir]
    foreach rel {system_continuous.bit four_mic_continuous.elf ps7_init.tcl VERIFIED-BUILD.json} {
        if {![file isfile "$root/$rel"]} {error "Missing verified release file $rel"}
    }
    puts "OPERATOR LOAD C1 candidate from $root (PS/PL reset now; no reset between its two sessions)"
    connect -url tcp:127.0.0.1:3121
    targets -set -nocase -filter {name =~ "APU*"}
    rst -system
    after 3000
    targets -set -nocase -filter {name =~ "xc7z020"}
    fpga -file "$root/system_continuous.bit"
    targets -set -nocase -filter {name =~ "APU*"}
    source "$root/ps7_init.tcl"
    ps7_init
    ps7_post_config
    targets -set -nocase -filter {name =~ "*Cortex-A9*#0"}
    rst -processor
    dow "$root/four_mic_continuous.elf"
    con
}
