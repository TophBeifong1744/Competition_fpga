if {[catch {

set events {}
set sealed_paths {}
set fixture [encoding convertfrom utf-8 [binary decode base64 {RjpcTlVFQ1xyZXZpZXctZXZpZGVuY2VcdGltZXJmaXhlZC1yZXBhaXItMTdhZmUzMlxzdGFuZGFyZHNca2VlcGVyX3Byb2JlLnB5}]]
source [encoding convertfrom utf-8 [binary decode base64 {RjpcTlVFQ1xyZXZpZXctd29ya3RyZWVzXHRpbWVyZml4ZWQtcmVwYWlyLTE3YWZlMzJcdGFzay1wYWNrYWdlc1xQS0ctQS1BQ1FcdGFza3NcZm91ci1jaGFubmVsLWRpYWdub3N0aWMtMDFcY29udGludW91cy1wcm90b3R5cGUtMDFcdGltZXJmaXhlZC1lbnRyeS0wMVxsb2FkX3RpbWVyZml4ZWQudGNs}]]
rename open real_open
proc open {args} {
    set first [lindex $args 0]
    if {[string index $first 0] eq "|"} {
        set launch $first
        lset launch 4 $::fixture
        return [real_open $launch [lindex $args 1]]
    }
    return [real_open {*}$args]
}
foreach command {connect targets rst after ps7_init ps7_post_config} {
    proc $command {args} [format {lappend ::events %s} $command]
}
proc check_locked {path} {
    if {![catch {set f [real_open $path r+]; close $f}]} {error "seal writable"}
}
proc fpga {flag path} {lappend ::events fpga; check_locked $path; lappend ::sealed_paths $path}
rename source real_source
proc source {path} {lappend ::events source; check_locked $path; lappend ::sealed_paths $path}
proc dow {path} {lappend ::events dow; check_locked $path; lappend ::sealed_paths $path}
proc con {} {
    lappend ::events con
    foreach path $::sealed_paths {check_locked $path}
    error "injected-con-failure-with-locks-held"
}
set failed [catch {c1_timerfixed_load [encoding convertfrom utf-8 [binary decode base64 {QzpcVXNlcnNcQnJ5YW5aaGVuZ1wuY2FjaGVcY29kZXgtcnVudGltZXNcY29kZXgtcHJpbWFyeS1ydW50aW1lXGRlcGVuZGVuY2llc1xweXRob25ccHl0aG9uLmV4ZQ==}]] [encoding convertfrom utf-8 [binary decode base64 {RjpcTlVFQ1xyZXZpZXctZXZpZGVuY2VcdGltZXJmaXhlZC1yZXBhaXItMTdhZmUzMlxzdGFuZGFyZHNcdGNsLWNvbi1mYWlsdXJlXGZvdXJfbWljX2NvbnRpbnVvdXM=}]] [encoding convertfrom utf-8 [binary decode base64 {RjpcTlVFQ1xyZXZpZXctZXZpZGVuY2VcdGltZXJmaXhlZC1yZXBhaXItMTdhZmUzMlxzdGFuZGFyZHNcdGNsLWNvbi1mYWlsdXJlXGNvbnRpbnVvdXNfcGxhdGZvcm0=}]] [encoding convertfrom utf-8 [binary decode base64 {RjpcTlVFQ1xyZXZpZXctZXZpZGVuY2VcdGltZXJmaXhlZC1yZXBhaXItMTdhZmUzMlxzdGFuZGFyZHNcdGNsLWNvbi1mYWlsdXJlXHRvb2xz}]] [encoding convertfrom utf-8 [binary decode base64 {RjpcTlVFQ1xyZXZpZXctZXZpZGVuY2VcdGltZXJmaXhlZC1yZXBhaXItMTdhZmUzMlxzdGFuZGFyZHNcdGNsLWNvbi1mYWlsdXJlXHJlY29yZHM=}]] 0} message]
if {!$failed || [string first "injected-con-failure-with-locks-held" $message] < 0} {error "unexpected failure: $message"}
if {[lindex $events end] ne "con" || [llength $sealed_paths] != 3} {error "con was not reached"}
foreach path $sealed_paths {set f [real_open $path r+];close $f}
puts "CON_FAILURE_RELEASE_PASS paths=$sealed_paths events=$events; NO_BOARD"

} msg]} {puts stderr $msg; exit 1}
exit 0
