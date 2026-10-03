# 独立双轴测试：50 MHz 板载时钟；不得与占用 T15/W16 的 LCD 约束合用。
create_clock -name sys_clk -period 20.000 -waveform {0.000 10.000} [get_ports sys_clk]
set_property PACKAGE_PIN U18 [get_ports sys_clk]
set_property IOSTANDARD LVCMOS33 [get_ports sys_clk]

# 用户 2026-10-03 确认：T15 水平，W16 垂直。
set_property PACKAGE_PIN T15 [get_ports pwm_horizontal]
set_property PACKAGE_PIN W16 [get_ports pwm_vertical]
set_property IOSTANDARD LVCMOS33 [get_ports {pwm_horizontal pwm_vertical}]
set_property DRIVE 4 [get_ports {pwm_horizontal pwm_vertical}]
set_property SLEW SLOW [get_ports {pwm_horizontal pwm_vertical}]

# 舵机异步测量脉宽，无共享采样时钟或输出 setup/hold 合同。
# 仅排除到这两个外部 PWM 端口的时序检查；内部寄存器路径仍完整检查。
# 不以虚构 output_delay 代替未知外设时序；脉宽正确性由组合仿真检查。
set_false_path -to [get_ports {pwm_horizontal pwm_vertical}]
