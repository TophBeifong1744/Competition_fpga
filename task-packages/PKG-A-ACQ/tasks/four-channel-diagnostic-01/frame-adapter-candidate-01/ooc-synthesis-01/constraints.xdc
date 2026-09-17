# OOC clock only. No false paths, multicycle paths, or fabricated I/O delays.
create_clock -name clk -period 10.000 [get_ports clk]
