# C-RTL-001 错误统计模块交付 v1.0

状态：**作者侧编译与功能仿真 PASS，待独立复核；未批准、未合入总工程。**

## 1. 提交信息

- 提交人：hsc119（成员 C）。
- 实现方式：Codex 辅助生成 RTL、自动自检测试平台及交付说明；用户在 Vivado GUI 中执行仿真操作。不是独立第三方验收结论。
- 交付版本/整理日期：v1.0 / 2026-09-09。
- 原始编译与仿真日期：2026-09-08；本批引用当日保存的命令行原始日志，不将整理日期写成重新测试日期。
- 工具：Vivado / XSim 2025.2，SW Build 6299465；目标器件 xc7z020clg400-2。
- 工作分支：codex/c-rtl-001-outsourcing-docs。
- 整理前仓库基线：474c62f9976178c4966598025978097811dbb7e8。此提交不包含本次尚未提交的成果。
- 任务依据：[C-RTL-001 说明 v1.0](../instructions/README.md)。本批仅错误统计模块。
- 父包：PKG-A-ACQ；后续独立检查按外包流程执行，父包正式复核及合入仍由指定复核人 B 办理。

## 2. 功能与接口

`stream_error_stats` 为单时钟 SystemVerilog 模块，COUNT_WIDTH 默认 32，规格范围 1～64。overflow_event 与 drop_event 分别驱动无符号饱和计数器和 sticky 标志。事件每持续一个周期计一次，两路互不影响；统计的是事件次数，不是一次事件中实际丢失的样本数。

优先级：时钟上升沿 rst_n=0 时全部归零；否则 clear=1 时清除历史并计入本拍事件，对应 count/sticky 为 0 或 1；否则有事件则计数加一至饱和、sticky 置位，无事件保持。复位同步低有效，clear 同步高有效。没有额外流水级，输入同步由集成方保证。

## 3. 文件清单

| 文件 | 内容 |
|---|---|
| [rtl/stream_error_stats.sv](rtl/stream_error_stats.sv) | 可综合风格的逻辑源码，综合尚未执行 |
| [tb/tb_stream_error_stats.sv](tb/tb_stream_error_stats.sv) | 自动比较全部四个输出，含参数化 checker、四种位宽实例和超时保护 |
| [logs/xvlog.log](logs/xvlog.log) | RTL 和测试平台的原始编译日志 |
| [logs/xelab.log](logs/xelab.log) | 各位宽实例展开及实际仿真选项 |
| [logs/tb_stream_error_stats_xsim.log](logs/tb_stream_error_stats_xsim.log) | XSim 版本、运行时间、各位宽结果及最终 PASS |
| [file-manifest.json](file-manifest.json) | 本交付其他文件的字节数、SHA-256 及五个原始文件的来源 |
| .gitignore / .gitattributes | 仅放行本包三份日志，保留复制源码与日志的原始字节，避免 Git 换行转换造成哈希变化 |

两个源码及三份日志从原 D 盘工程逐字节复制，复制后哈希一致；本次未修改算法或测试激励，未重新运行功能仿真。清单哈希是在本次整理时计算，不是原始仿真时生成的签名。日志中的本机路径和主机信息作为内部原始证据保留；复现不依赖这些路径。

## 4. GUI 复现步骤

1. 将交付目录放在本机英文路径下。使用 Vivado 2025.2 新建独立 RTL Project，选择 xc7z020clg400-2；临时工程放在交付目录之外，不覆盖保存的日志。
2. Add Sources → Add or create design sources，加入本包 rtl/stream_error_stats.sv。
3. Add Sources → Add or create simulation sources，加入本包 tb/tb_stream_error_stats.sv。
4. 设计顶层设为 stream_error_stats；仿真顶层设为 tb_stream_error_stats；两个源文件类型均为 SystemVerilog，仿真器选择 XSim。
5. 在 Tcl Console 执行以下命令，补齐未声明时间单位的 RTL 所需默认时间单位：

```tcl
set_property -dict {xsim.elaborate.xelab.more_options {-timescale 1ns/1ps}} [get_filesets sim_1]
launch_simulation
run all
```

测试平台已同时实例化 COUNT_WIDTH=1、3、32、64，无需改 RTL 默认参数或分四次运行；32 位实例故意不覆盖 DUT 参数，以验证默认值。输出在采样上升沿 1 ns 后检查，避免非阻塞赋值调度竞争。全局超时为 100 us。

正常结束判据：四行位宽 PASS 和一行 ALL TESTS PASS，随后在 5776 ns 调用 $finish；有 FAIL、ERROR、超时或缺少最终标志不能判通过。重新仿真的输出保存为新的日志，不覆盖本包原始日志。

## 5. 命令行复现（可选）

在已配置 Vivado 2025.2 工具环境的命令提示符中，切换到单独的新建临时目录。以下将 `<submission>` 替换为本包的实际绝对路径：

```text
xvlog --sv "<submission>/rtl/stream_error_stats.sv" "<submission>/tb/tb_stream_error_stats.sv"
xelab work.tb_stream_error_stats -s tb_stream_error_stats_snapshot -debug typical -timescale 1ns/1ps
xsim tb_stream_error_stats_snapshot -runall -log tb_stream_error_stats_xsim.log
```

逐条检查退出状态，前一步失败时停止。临时目录会产生 xvlog.log、xelab.log、tb_stream_error_stats_xsim.log 及仿真缓存；只对照日志，不回填缓存到交付包。实际历史命令由本机 Vivado bin 下对应 .bat 启动，源码路径不同不影响用例。

## 6. 实际验证记录

下列记录来自 2026-09-08 同一次仿真，各位宽共用上述三份日志，未伪装为四次独立运行。

| 项目 | 状态 | 输出检查次数/证据 |
|---|---|---|
| 源码与测试平台编译 | PASS | logs/xvlog.log |
| 四种位宽展开 | PASS | logs/xelab.log |
| COUNT_WIDTH=1，含饱和 | PASS | 561；logs/tb_stream_error_stats_xsim.log |
| COUNT_WIDTH=3，含饱和 | PASS | 579；同上 |
| 默认 COUNT_WIDTH=32，基本功能 | PASS | 541；同上 |
| COUNT_WIDTH=64，基本功能 | PASS | 541；同上 |
| 综合 | NOT_RUN | 未提供综合报告 |
| 实现、资源/时序验收 | NOT_RUN | 未执行 |
| 板测 | NOT_RUN | 本批不接板或下载 |

共 2222 次输出比较，每次检查两个计数及两个 sticky；不是 2222 个独立用例，也不是全状态空间证明。

```text
PASS COUNT_WIDTH=32 checks=541
PASS COUNT_WIDTH=64 checks=541
PASS COUNT_WIDTH=1 checks=561
PASS COUNT_WIDTH=3 checks=579
ALL TESTS PASS: COUNT_WIDTH=1,3,default32,64
```

## 7. 与任务自测要求的对应

| 要求 | 测试平台中可定位的用例/机制 | 当前覆盖 |
|---|---|---|
| 复位与空闲、同步复位 | initial reset、idle after reset、synchronous reset between edges/at rising edge | 四种位宽 |
| 复位最高优先 | reset wins over all | 四种位宽 |
| 单路事件互不影响 | overflow only、drop only | 四种位宽 |
| 连续事件逐拍累计 | three consecutive overflow/drop events | 四种位宽；1 位按饱和语义处理 |
| 两路同拍 | both events same edge | 四种位宽 |
| 标志保持 | overflow sticky hold、both sticky hold | 四种位宽 |
| 普通清零 | ordinary clear、synchronous clear | 四种位宽 |
| 清零与事件同拍三种组合 | clear plus overflow/drop/both | 四种位宽 |
| 连续清零且事件有效 | continuous clear plus events | 四种位宽 |
| 饱和不回绕 | overflow saturation、both saturation、drop saturation independently | 1、3 位，通过实际输入计数到满，无 force |
| 饱和后清零、复位及恢复 | saturated clear plus overflow、saturated reset priority、recount after reset | 1、3 位 |
| 参数宽度与默认值 | 四个 checker；32 位 DUT 不带参数覆盖 | 1、3、默认32、64 |
| 自动判错与超时 | compare_outputs 使用 !==、打印预期/实际并 $fatal；顶层 100 us 超时 | 已包含机制，成功运行未触发失败分支 |
| 附加控制组合 | 16 种输入控制组合的全部有序两拍配对 | 四种位宽；不是任意状态的穷尽验证 |

## 8. 已知问题、修正记录与边界

- 初次仿真展开因 RTL 未声明 timescale 失败，增加 xelab 的 -timescale 1ns/1ps 后运行通过；本包保存最终成功日志，没有初次失败的独立原始日志，不声称完整保留全部失败日志。
- 本机 GUI 导入辅助脚本曾将以连字符开头的属性值直接传给 set_property 导致 Unknown option；改为 set_property -dict 后，独立内存工程验证该属性设置通过。本包用第 4 节的修正后命令，不依赖本机固定路径辅助脚本。
- 之前自动化进程缺少 PROCESSOR_ARCHITECTURE，工具启动失败；在确认本机为 X64 后，仅在该进程补为 AMD64，随后编译与仿真成功。这是历史环境说明，不要求接收者无条件修改系统环境。
- 已测 1、3、默认32、64；其余规格内宽度未逐个仿真。32/64 未计数至饱和，按任务要求仅做基本功能测试。
- 在所列功能仿真范围内未发现输出不匹配；未进行综合、时序收敛、板测、CDC 或整机集成验证。
- 未新增 AXI/FIFO/麦克风驱动、约束或接口字段。源码保持原件，独立复核人仍须检查可综合性和规格一致性。
- 本页记录作者侧自检。独立技术验收、人类批准和父包合入仍待进行，不代签复核结论。
