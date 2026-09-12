# 第三次隔离构建的 HWH 差异核对

核对日期：2026-09-12。旧平台：
F:/College/verilog_digital_system/Vitis/c_adapter_platform/export/c_adapter_platform/hw/system_c_adapter.xsa。
新产物：F:/College/verilog_digital_system/four_diagnostic_work/current_rebuild_20260912_03/artifacts/hw/system_c_adapter.xsa。

XML 树逐项比较共 9 项差异：
1 项根 TIMESTAMP，8 项 processing_system7_0 的 PCW_FTM_CTI_IN0～3/OUT0～3 的 VALUE，
由 DISABLED 变成 &lt;Select&gt;；无其他属性、文字、节点数量或次序差异。
旧/新 HWH 分别为 324018 / 324042 字节。两份 ps7_init.c 均 360536 字节且 SHA-256 相同，
ps7_init.tcl 均 27896 字节且 SHA-256 相同。

两份 HWH 均为 PCW_USE_CROSS_TRIGGER=0、PCW_P2F_CTI_INTR=0；
processing_system7_0 均无 FTMT/TRIGGER 硬件端口或总线接口。

本机 AMD 2025.2 定义依据：
F:/AMD/2025.2/Vivado/data/ip/xilinx/processing_system7_v5_5/component.xml。
该文件 SHA-256：73afc63c51ffd0eb825ba061cb91f25df9d3263f02ffb6427fab0008c721d91a。
参数使能定义见 28705、28749 等行：PCW_USE_CROSS_TRIGGER = 1 才启用；
接口和端口定义见 7085、7209、24634、24853 等行：CROSS_TRIGGER=1 且该选项非 DISABLED 才启用。
因此本次只把这 8 个明确禁用选项的两种 GUI 哨兵值视为等价，
不删除其他 PS 参数，也不忽略实际地址/中断/时钟/位宽/连线差异。

防回归测试覆盖：
跨触发启用、P2F 中断启用、出现触发端口、哨兵变为其他值、DMA 地址变化、
PS 初始化变化均不允许通过这项等价规则。

这是构建入口的受限兼容性判断，非“新旧 XSA 逐字节相同”的断言。
第三次运行保留 BUILD_FAILED；仅之后使用新入口重新完整构建才可产生新的成功记录。
