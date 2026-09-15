# c-adapter-v1: C connector pin N must mate to J4 pin N, not mirrored.
# Navigator baseboard v3.9 sheet 5; coreboard v2.5 Bank13/34.
# U1/U2 pins 38=3V3, 37/39=GND, 40=5V passthrough (NOT microphone VDD).
# Disconnect any camera/peripheral on the shared CMOS nets before attachment.
# External IO timing/electrical margins remain deferred (CBR-01/02).
set_property PACKAGE_PIN V11 [get_ports pdm_clk1]
set_property PACKAGE_PIN Y13 [get_ports pdm_clk2]
set_property PACKAGE_PIN U14 [get_ports pdm_clk3]
set_property PACKAGE_PIN V12 [get_ports pdm_clk4]
set_property IOSTANDARD LVCMOS33 [get_ports {pdm_clk1 pdm_clk2 pdm_clk3 pdm_clk4}]
set_property PACKAGE_PIN Y9 [get_ports {pdm_data[0]}]
set_property PACKAGE_PIN W10 [get_ports {pdm_data[1]}]
set_property PACKAGE_PIN W14 [get_ports {pdm_data[2]}]
set_property PACKAGE_PIN V15 [get_ports {pdm_data[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {pdm_data[*]}]
