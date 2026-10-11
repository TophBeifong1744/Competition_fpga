# C-XDC-003：XDC 读取兼容修复

2026-10-11，BUILD_FLOW。用户原生 GUI 报 Designutils 20-1307：`i17_vio_pins.xdc:4 foreach` 不受支持。原文件留存 `xdc-repair3-check/pins-before.xdc`、`cdc-before.xdc`，原快照亦保存。

修复：pins 展开为 11 组直接 PACKAGE_PIN/IOSTANDARD 命令；20 ns 时钟及六个输出 DRIVE=4、SLEW=SLOW 完全不变。CDC 展开为四条输入至同下标 `u_core/source/pdm_meta_reg[i]/D` 的直接 set_false_path；精确 NAME 查询，不加通配、不扩大例外。无 RTL、引脚、时钟、周期、CDC 结构变化。

XDC 内原数量/ASYNC_REG 检查已移出，**不再有原来的自动 error 守卫**。完整工程综合后必须由 Codex 读取原生网表/报告核验：四个输入各一个、四个指定 cell 各一个、每个 ASYNC_REG=true、每个 D pin 各一个；四条例外确实生效且只到首级 D；meta→sync→CIC 仍计时。未确认这些事实不签时序/CDC 通过。用户手动导入，CDC 文件仍 synthesis 关、implementation 开、simulation 关。

官方依据：[UG903 About XDC Constraints](https://docs.amd.com/r/2025.2-English/ug903-vivado-using-constraints/About-XDC-Constraints)、[Valid Commands in an XDC File](https://docs.amd.com/r/2025.2-English/ug903-vivado-using-constraints/Valid-Commands-in-an-XDC-File)，及本机 Vivado 2025.2 `doc/eng/man/read_xdc`。条件和循环属 unmanaged Tcl，不把本文件改成 Tcl 类型绕开手动 XDC 接入。

已做：静态比较原/新 11 个 pin、IOSTANDARD、时钟/输出属性和四条明确端点；非作者 CDC reviewer 已只读核查表达式。原生诊断模型和脚本只在 codex_out，**不是产品源**。native 启动未成功：bat exit1 无日志；unwrapped 首先找不到 init.tcl，指定本机 Tcl 库后缺 xv_commontasks.dll 依赖。未到 read_xdc，故 **原生解析 NOT RUN，不能把进程 exit0 当 PASS**；停止环境排障，没有运行正式用户工程或硬件。

当前交付仅两个 XDC；不再使用/修改原工程导入 Tcl。原 IP/BOARD 历史快照所带旧 XDC hash 留作旧版证据，本次准确范围以 `XDC-REPAIR-3-SNAPSHOT.json` 为准。用户若此前勾选复制源，请在 GUI 移除旧约束引用后重新添加这两份准确路径，不删除唯一工程文件。
