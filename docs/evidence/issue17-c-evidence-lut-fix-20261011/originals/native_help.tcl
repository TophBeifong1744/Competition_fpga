# 仅查询本机同版本命令；不打开或改变用户工程。
# Run: vivado -mode batch -source native_help.tcl -log native_help.log -journal native_help.jou
# Output: native_help.log. Next: same-options isolated old/new module diagnostics.
puts [version]
help read_verilog
synth_design -help
help report_utilization
help create_clock
exit 0
