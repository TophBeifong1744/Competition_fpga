# Simulation

2026-09-17：新增获准舵机模块，统一清单为7组；下面“6组”是9/10历史结果。只验证本批搬迁入口可运行 `pwsh -File ./sim/run_servo.ps1 -OutputDirectory <全新目录> -ClockHz 1000000`，实际加载 `rtl/servo/`、`tb/servo/`，不加载任务包副本；默认100 MHz。原有6组本轮未重跑。来源与限定范围见[复核](../docs/reviews/servo-b1d51d4/REVIEW.md)。未修改或执行 one/BD。

## 当前可运行入口

Vivado/XSim 2025.2，PowerShell 7，仓库根目录执行，输出必须是仓库外的新目录：

```powershell
./sim/run_regression.ps1 -VivadoBin 'F:/AMD/2025.2/Vivado/bin' -OutputDirectory 'C:/temp/soundsight-regression-new'
```

脚本校验[modules.json](modules.json)中的活动源码哈希，按扩展名分别以Verilog/SystemVerilog编译，运行6组自检。预期6行PASS与输出result.json中的PASS_MODULE_REGRESSION；缺少PASS、错误或工具失败都不算通过。每组保存编译、展开、仿真输出；旧输出目录拒绝覆盖。原批准源码与活动源码仅允许记录过的CRLF→LF规范化。

如需将三件基础RTL加入一个已打开的Vivado工程，在Tcl Console执行 `source /实际路径/sim/add_sources.tcl`。它只加入设计源，不选择系统顶层、不接BD、不修改约束。该脚本不等于可直接下载的整机工程，本轮自动回归不调用它修改one。

本次结果见[9月10日补收尾](../deliverables/phase-2026-09-10/CLOSEOUT.md)。后续阶段按[固定收尾规则](../docs/phase-closeout.md)更新清单及入口，不能只把代码留在任务包。

本目录保存仿真文件列表、统一回归入口和小型确定性测试向量；当前基础模块回归已固定使用上述工具和命令。

仿真层级计划：

1. 模块级：接口、数值和边界条件。
2. 子系统级：四通道吞吐、帧调度、延迟和 backpressure。
3. 位精确联调：与 MATLAB 定点模型逐帧比较。
4. 系统级：AXI 配置、错误注入和长序列回归。

所有随机测试固定种子并记录参数，保证失败可重放。

