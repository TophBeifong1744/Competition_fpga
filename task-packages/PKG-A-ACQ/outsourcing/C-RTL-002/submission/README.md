# C-RTL-002 错误统计快照交付 v1.0

状态：**作者侧编译、展开、功能仿真 PASS；待独立验收与 B 正式复核，未合入总工程。**

## 提交信息与用户调整

- 作者：Codex，按成员 C 的请求辅助实现并执行自动仿真；不代签 B 的复核结论。
- 交付版本：v1.0；实现和测试日期：2026-09-09。
- 唯一交付分支：`codex/c-rtl-001-outsourcing-docs`。
- 工作起点提交：`896ce7ad983e3c4781af4fcdf7092cca5cad37f0`，不是本次交付提交。
- 本交付准确内容由 `file-manifest.json` 的相对路径、字节数和 SHA-256 标识。交付提交可在仓库根目录执行下列命令定位，避免在同一提交内容中循环嵌入自身哈希：
  `git log -1 --format=%H -- task-packages/PKG-A-ACQ/outsourcing/C-RTL-002/submission`
- 实际工具：Vivado Simulator / XSim 2025.2，SW Build 6299465、IP Build 6300035、SharedData Build 6298862。
- 任务指定器件：xc7z020clg400-2；行为仿真不需要建立器件工程。
- 原任务依据：[instructions/README.md](../instructions/README.md)。
- 用户后续明确要求当前新文件使用 `.v`：本交付新 RTL、独立 TB 和联合 TB 均为 Verilog `.v`，实际使用 **不带 --sv 的 xvlog** 编译。替代操作单原定的新建 `.sv` 文件名；接口与逐拍行为保持操作单定义。
- 仅固定依赖的 001 原始文件保留 `.sv`，单独以 --sv 编译；没有更改原 001 交付。
- 后续编码约定：简单功能模块使用 Verilog .v；复杂模块可以使用 SystemVerilog .sv 内核加 Verilog .v 包装。本次没有 BD/系统集成验收。

## 文件

| 文件 | 内容 |
|---|---|
| rtl/stream_error_snapshot.v | 同步快照模块，参数默认 32，支持 1～64 |
| tb/tb_stream_error_snapshot.v | 四个位宽的独立参考模型、自检和超时 |
| tb/tb_stream_error_snapshot_integration.v | COUNT_WIDTH=3，连接固定 001 的联合自检 |
| reference/stream_error_stats.sv | 从固定 Git 提交导出的原始字节 |
| run_tests.ps1 | 在交付包外的新临时目录执行编译、展开、两组仿真 |
| logs/*.log | 最终完整运行的六份原始日志 |
| logs/attempt-01/*.log | 第一次运行的四份原始工具日志；独立测试已通过，脚本误报后未执行联合测试 |
| .gitignore / .gitattributes | 局部放行列出的日志，并保留包内文件字节，避免换行转换影响哈希 |
| file-manifest.json | 包内其他全部文件的字节数、SHA-256 和参考来源，不包含清单自身 |

001 参考依赖来源提交：
`ac8a7bb60d94c069f5f1b61e9fc38658b0742962`

来源仓库相对路径：
`task-packages/PKG-A-ACQ/outsourcing/C-RTL-001/submission/rtl/stream_error_stats.sv`

参考文件 SHA-256：
`333dc4d193169982a6609c886a48968e87ef2631496d0c90137d24f228a94afe`

## 行为

每个 clk 上升沿，rst_n=0 时所有输出清零，优先于请求。正常工作时 snapshot_valid 更新为 snapshot_req；请求为 1 时同时保存两项计数和两项 sticky，否则数据保持。请求可以连续有效；请求停止后的第一个上升沿 valid 清零，快照数据继续保持。

不进行计数、饱和或 count/sticky 一致性推断。复位是同步低有效。所有输入须由集成方同步到 clk。001 同沿计数变化或 clear 不会提前进入快照：002 保存沿前值，后续一拍请求才能读取更新值。

## 一键复现

需要 Windows PowerShell 7 和 Vivado/XSim 2025.2。在本 submission 目录打开 PowerShell：

```powershell
& .\run_tests.ps1 -VivadoBin 'C:\AMDDesignTools\2025.2\Vivado\bin'
```

将 VivadoBin 改为实际安装位置即可。脚本从自身目录定位全部源码，不依赖日志中的历史路径。默认在系统临时目录创建唯一的新目录；也可以加 `-RunDirectory 'C:\temp\snapshot-check-new'` 指定**尚不存在且在交付包外**的目录。

预期产物：compile_verilog.log、compile_reference.log、两个 *-elaborate.log、两个 *-simulate.log，以及仅留在临时目录的 XSim 缓存。脚本每步检查退出状态，仿真还检查 ALL TESTS PASS 和行首失败标志。运行结束打印 VERIFIED BOTH TEST TOPS 和输出目录。下一步核对日志和下面的覆盖表，交给 B 正式复核。重新运行不覆盖本交付保存的原始日志。

测试平台使用 Verilog 语法；按任务要求使用 XSim 支持的 $fatal 终止失败。时钟周期 10 ns，下降沿驱动，独立测试在上升沿后 1 ns 检查，联合测试也在上升沿后 1 ns 检查，两组均有 100 us 超时。

## 等效逐条命令

在配置好 Vivado 2025.2 环境的命令提示符中进入一个新的独立临时目录，将 `<submission>` 替换为本包绝对路径：

```text
xvlog "<submission>/rtl/stream_error_snapshot.v" "<submission>/tb/tb_stream_error_snapshot.v" "<submission>/tb/tb_stream_error_snapshot_integration.v" -log compile_verilog.log
xvlog --sv "<submission>/reference/stream_error_stats.sv" -log compile_reference.log
xelab work.tb_stream_error_snapshot -s tb_stream_error_snapshot -debug typical -timescale 1ns/1ps -log tb_stream_error_snapshot-elaborate.log
xsim tb_stream_error_snapshot -runall -log tb_stream_error_snapshot-simulate.log
xelab work.tb_stream_error_snapshot_integration -s tb_stream_error_snapshot_integration -debug typical -timescale 1ns/1ps -log tb_stream_error_snapshot_integration-elaborate.log
xsim tb_stream_error_snapshot_integration -runall -log tb_stream_error_snapshot_integration-simulate.log
```

每步失败时停止并保存日志。xelab 的默认时间单位用于保持没有 timescale 声明的 001 参考文件原样。

## 实际结果

| 检查 | 状态 | 证据 |
|---|---|---|
| 新 .v 编译、001 参考编译 | PASS | compile_verilog.log、compile_reference.log |
| 两个仿真顶层展开 | PASS | 两份 *-elaborate.log |
| COUNT_WIDTH=1、3、默认32、64 | PASS | tb_stream_error_snapshot-simulate.log；每个位宽 166 次比较，共 664 次 |
| 与 001 同沿事件/clear 联合测试 | PASS | tb_stream_error_snapshot_integration-simulate.log；15 个定向步骤 |
| 综合（可选） | NOT_RUN | 未执行 |
| 实现、资源时序、板测、BD/总工程集成、CDC | NOT_RUN | 本批未执行 |

最终成功标志：

```text
PASS COUNT_WIDTH=3 checks=166
PASS COUNT_WIDTH=1 checks=166
PASS COUNT_WIDTH=32 checks=166
PASS COUNT_WIDTH=64 checks=166
ALL TESTS PASS: COUNT_WIDTH=1,3,default32,64
ALL TESTS PASS: integration COUNT_WIDTH=3 checks=15
```

独立测试在 827 ns 正常 $finish，联合测试在 156 ns 正常 $finish。比较次数不是独立用例数量，也不是形式证明。

## 任务覆盖对应

| 要求 | TB 中的用例或机制 | 范围 |
|---|---|---|
| 复位和请求同拍 | reset wins over request | 四个位宽 |
| 同步复位时机 | prepare nonzero synchronous reset / assert reset between edges；下降沿后检查旧值，上升沿后检查清零 | 四个位宽 |
| 初始无请求、live 变化 | initial idle changing live | 四个位宽，8 拍 |
| 单拍请求、valid 及时撤销 | single request / valid deasserts data holds | 四个位宽 |
| 连续请求四项变化 | consecutive requests | 四个位宽，16 拍 |
| 长时间保持 | long idle changing live | 四个位宽，32 拍 |
| 0、全1、最高位、交替位 | 四类 boundary / bits 用例，计数常量按 W 构造 | 四个位宽；包含64位最高位 |
| sticky 00/01/10/11 | s=0..3，每种组合交叉四种数据形态 | 四个位宽；含计数非零而 sticky 为零及相反情况 |
| 沿间 req/live 不影响输出 | 每次 step 驱动后、下一上升沿前检查全部输出；额外沿间脉冲 | 四个位宽 |
| 复位后恢复 | request after reset / hold after recovery | 四个位宽 |
| 默认参数 | default_width 分支的 DUT 不覆盖参数 | 32 位 |
| event+req 旧值及下一拍新值 | first event plus req / next req sees event；both events plus req / next req sees both | 联合3位 |
| clear+req 旧值及下一拍清零值 | clear plus req old data / next req sees cleared | 联合3位 |
| clear+event+req、复位恢复、保持 | clear event req old 等额外定向步骤 | 联合3位 |
| 自动判错 | !== 检查两个计数、两个标志和 valid，打印位宽/用例/预期/实际后 $fatal；联合测试还检查001实时输出 | 两个顶层 |
| 超时 | 各顶层 100 us 超时 $fatal | 两个顶层 |

## 修正记录与边界

首次运行的 RTL 自检全部通过，但复现脚本最初用未限定位置的 ERROR 正则检查日志，误匹配模块文件名 stream_error_snapshot 中的 error，导致脚本提前停止，联合测试尚未执行。这是脚本判读问题，未改 RTL 或预期值。随后将检测限制为行首错误标志，在全新临时目录重跑，两组均通过。

logs/attempt-01 保存首次运行的四份原始工具日志；PowerShell 抛出的脚本异常见本次对话工具输出，未将人工重写的错误文本冒充原始日志。最终六份日志在 logs 根目录。

自动进程未提供 PROCESSOR_ARCHITECTURE 时，脚本仅在确认操作系统为 X64 后为当前进程补 AMD64，并在退出时恢复；未修改全局环境。没有发生需要重装或重置环境的 TclStore 处理。

尚未逐一仿真其余合法位宽，未进行形式验证、综合或 BD 导入验证。用户要求的 .v 形式已通过 Verilog 模式编译，但功能 PASS 不代表资源时序、跨时钟读取或 PS 协议验收通过。未增加总线、计数或系统接口，也未启动第三项任务。
