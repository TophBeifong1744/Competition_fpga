set out [file normalize [lindex $argv 0]]
if {[file exists $out]} {error "Output already exists: $out"}
file mkdir $out
cd $out
create_project fft_probe $out -part xc7z020clg400-2
if {[version -short] ne "2025.2"} {error "Vivado 2025.2 required"}
create_ip -name xfft -vendor xilinx.com -library ip -version 9.1 -module_name fft_probe_ip
report_property -all [get_ips fft_probe_ip] -file $out/properties.txt
set fp [open $out/catalog.txt w]
puts $fp [version]
puts $fp [get_property XML_FILE_NAME [get_ipdefs xilinx.com:ip:xfft:9.1]]
close $fp
close_project
