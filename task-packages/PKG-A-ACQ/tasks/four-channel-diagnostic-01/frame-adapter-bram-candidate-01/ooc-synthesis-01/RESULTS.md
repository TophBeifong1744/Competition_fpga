# BRAM 友好分帧器：首次 OOC 综合结果

结论：**主 `groups[0:1023]` 缓存确实推断为 Block RAM**，使用 5 个 RAMB36E1 加 1 个 RAMB18E1（5.5 个 RAMB36 等效 tile），LUTRAM 从旧候选的 4364 降为 0。独立 OOC 综合的已约束内部路径在 10 ns 下估算 WNS 为 +2.642 ns；这不是布局布线后的时序结论，也没有验证真实输入/输出接口。

## 运行与绑定

| 项目 | 实际值 |
|---|---|
| 操作人/入口 | 拓芙运行 [run_ooc.ps1](run_ooc.ps1)，`-RunName bram_ooc_20260918_01` |
| 真实命令、退出码 | [command.txt](launcher-logs/bram_ooc_20260918_01/command.txt)，[exit-code.txt](launcher-logs/bram_ooc_20260918_01/exit-code.txt) 为 `0` |
| 工具/器件 | Vivado 2025.2 Build 6299465；`xc7z020clg400-2` |
| 时钟/流程 | `clk` 10.000 ns；Non-Project `synth_design -mode out_of_context` |
| 源码 | [pcm4_overlap_framer_bram.v](../rtl/pcm4_overlap_framer_bram.v)，SHA-256 `389c8792fc73f2aee798564c6ea30a71eedb7dea8c4fa9ad88d86da0b8f2e52e` |
| 基线 | 功能候选 `a7d944a2268fff6215b2c619d2d6440235ff5752`；旧 OOC `08759a2817929d9c4d7d7345a7afca155fd30130` |
| 完成标记 | `BRAM_OOC_SYNTH_COMPLETE_NOT_IMPL_NOT_BOARD`，见 [STATUS.txt](runs/bram_ooc_20260918_01/STATUS.txt) |

原始 [Vivado transcript](launcher-logs/bram_ooc_20260918_01/vivado-transcript.txt)、[journal](launcher-logs/bram_ooc_20260918_01/vivado.jou)、[DCP](runs/bram_ooc_20260918_01/checkpoint/post_synth.dcp) 和所有报告保持原样。源绑定见 [source-binding.txt](runs/bram_ooc_20260918_01/source-binding.txt)；各文件 SHA-256 见 [OOC-MANIFEST.sha256](OOC-MANIFEST.sha256)。没有重新运行仿真，也没有修改本候选 RTL。

## 资源与存储推断

| 综合后资源 | 冻结异步读候选 | 本次同步读候选 |
|---|---:|---:|
| Slice LUT | 5629 | 261 |
| LUT as Memory | 4364 | 0 |
| Slice FF | 783 | 608 |
| RAMB36E1 | 0 | 5 |
| RAMB18E1 | 0 | 1 |
| DSP | 0 | 0 |

本次 Block RAM tile 占器件 140 个可用 tile 中的 5.5 个（3.93%）。[RAM 利用报告](runs/bram_ooc_20260918_01/reports/ram_utilization.rpt) 将 `groups` 列为 `1024×196`、`RAM_SDP`，一个写端口、一个同步读端口；[实际原语清单](runs/bram_ooc_20260918_01/reports/storage_primitive_inventory.rpt) 对应 `groups_reg_0..4` 五个 RAMB36E1、`groups_reg_5` 一个 RAMB18E1，没有 `RAM64M/RAM64X1D`。RTL 虽然分时发起写/读，综合器实际映射为 simple dual-port BRAM；因此不要把“每周期最多一次访问”误写成物理单端口。

BRAM 中有 6 条 `SYNTH-6` 提示：可选输出寄存器未合并进 RAM 原语，可能影响后续时序。这不改变已完成的 BRAM 推断，但在正式接入、布局布线时仍要检查。[资源原报告](runs/bram_ooc_20260918_01/reports/utilization.rpt) 与 [分层报告](runs/bram_ooc_20260918_01/reports/utilization_hierarchical.rpt) 是上述数字的原始依据。

## 综合时序与约束边界

| 指标 | 本次结果 |
|---|---:|
| 目标周期 | 10.000 ns（100 MHz） |
| OOC 综合 WNS / TNS | +2.642 ns / 0.000 ns |
| Setup 失败端点 / 总端点 | 0 / 1366 |
| 最差内部路径 | `last_input_id_reg[4]` → `fill_count_reg[0]/R`；21级逻辑，17级 CARRY4；数据路径约 6.860 ns |
| 未指定输入/输出 delay | 303 / 683 个端口，共 986 项 `TIMING-18` |
| 实现后 setup/hold | 未执行 |

最差内部路径仍是原始 ID 连续性判断影响计数器复位，不是 BRAM 读数据路径。旧候选 OOC WNS 为 +2.612 ns，本次为 +2.642 ns；两者相差 0.030 ns，**不能据此宣称集成后时序改善**。Vivado 未布局布线，关键路径报告仍含约 3.203 ns 估算布线延迟。[时序摘要](runs/bram_ooc_20260918_01/reports/timing_summary.rpt)、[关键路径](runs/bram_ooc_20260918_01/reports/critical_paths.rpt)、[check_timing](runs/bram_ooc_20260918_01/reports/check_timing.rpt) 可复查。

本次刻意只约束 `clk`，没有编造板级输入/输出延迟，也没有添加假路径或多周期路径。`HD.CLK_SRC` 未设的 OOC 警告说明时钟源位置未知；303 个输入和 683 个输出无 I/O delay，因此内部 WNS 不覆盖真实上游/下游接口。DRC 的 `ZPS7-1`（缺 PS7）是纯 PL OOC 顶层的预期边界；OOC 连接性 DRC 也不完整。日志有 4 条普通 `WARNING`、无 `ERROR` 或 `CRITICAL WARNING`；[方法学报告](runs/bram_ooc_20260918_01/reports/methodology.rpt) 另列 6 条 `SYNTH-6` 与 986 条 `TIMING-18`，不能用“综合完成”抹去这些边界。

## 功能吞吐与未解决的系统问题

前一轮新 RTL XSim 功能证据仍适用：模型 5 项、RTL 协议/异常 5 帧 10 事件、六个精确组数边界，以及与冻结旧 RTL 在合法输入下的 3072 个样本握手/1 个事件逐字段等价。`m_ready=1` 时每帧输出 1024 个连续握手，从帧填满到 `s_ready` 恢复，输入暂停 1027 个时钟；下游背压可无限延长暂停。候选只接受可背压源，不能直接连不可暂停的 PDM/CIC。未来实时链仍需外部 FIFO/DDR、最坏服务时间预算和可观测溢出路径，本次 OOC 未验证这些条件。

## 分层结论与停止点

| 层级 | 状态 |
|---|---|
| 独立模型和 XSim 功能检查 | 已通过，引用 [final_run_20260917](../evidence/final_run_20260917)；非本次重跑 |
| 本次 OOC 综合、实际 BRAM 原语、内部 max-delay 估算 | 已完成，结果如上 |
| 布局布线、实现后 setup/hold、板级 I/O 时序 | 未执行 |
| `one` 接入、CDC、DMA/PDM/CIC/FFT、实板 | 未执行 |
| M1、H3、实时闭环 | 未通过/不在本任务范围 |

本轮至此停止：不因 OOC 结果直接修改 `one` 或接入正式算法链；交工作执行核查材料，再决定是否安排后续实际工程集成。
