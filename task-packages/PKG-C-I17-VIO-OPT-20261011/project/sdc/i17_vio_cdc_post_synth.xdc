# 中文用途：综合后四个 PDM 输入至各自首级同步器 D 的精确路径例外。
# USED_IN_SYNTHESIS=false，USED_IN_IMPLEMENTATION=true；不含 Tcl 过程控制。
# 数量/ASYNC_REG 守卫已移出 XDC，完整工程综合后必须核验四个唯一对象、
# ASYNC_REG=true、唯一 D pin 和实际例外覆盖；缺失不可继续或放宽匹配。
set_false_path -from [get_ports {mic_data[0]}] -to [get_pins -of_objects [get_cells -hier -filter {NAME == u_core/source/pdm_meta_reg[0]}] -filter {REF_PIN_NAME == D}]
set_false_path -from [get_ports {mic_data[1]}] -to [get_pins -of_objects [get_cells -hier -filter {NAME == u_core/source/pdm_meta_reg[1]}] -filter {REF_PIN_NAME == D}]
set_false_path -from [get_ports {mic_data[2]}] -to [get_pins -of_objects [get_cells -hier -filter {NAME == u_core/source/pdm_meta_reg[2]}] -filter {REF_PIN_NAME == D}]
set_false_path -from [get_ports {mic_data[3]}] -to [get_pins -of_objects [get_cells -hier -filter {NAME == u_core/source/pdm_meta_reg[3]}] -filter {REF_PIN_NAME == D}]
# 下游 pdm_meta -> pdm_sync -> CIC 正常计时；不切 PDM 输出、不造 input_delay=0。
# 外部有效窗、实际 LR/PCB 延迟仍未实板验收。
