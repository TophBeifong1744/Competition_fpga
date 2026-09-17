# 四路重叠分帧器 BRAM 友好独立候选

结论：已完成单缓冲、同步读版本及功能验证；模型、三套 XSim 检查均通过，合法输入下与冻结旧候选逐握手等价。拓芙运行的首次 OOC 综合也确认主缓存映射为 **5 个 RAMB36E1 + 1 个 RAMB18E1、LUTRAM=0**；完整判读见 [OOC 结果](ooc-synthesis-01/RESULTS.md)。本批没有修改实际 `one`、BD、XDC、Vitis、FFT或算法链。

## 1. 固定来源与旧结果

| 项目 | 固定值 |
|---|---|
| 功能候选 | `codex/toph/frame-adapter-candidate-20260917` / `a7d944a2268fff6215b2c619d2d6440235ff5752` |
| OOC证据 | `codex/toph/frame-adapter-ooc-20260918` / `08759a2817929d9c4d7d7345a7afca155fd30130` |
| 冻结旧RTL SHA-256 | `f0da9259a2c5407f003e527dc097fb57ef514a2335c20a528655427294f77585` |
| 冻结旧OOC结果 | 5629 LUT、4364 LUTRAM、RAMB18/36=0、WNS=+2.612 ns；仅OOC综合估算 |
| 新RTL | [pcm4_overlap_framer_bram.v](rtl/pcm4_overlap_framer_bram.v) |
| 新RTL SHA-256 | `389c8792fc73f2aee798564c6ea30a71eedb7dea8c4fa9ad88d86da0b8f2e52e` |

共享工作区没有切换分支；上述本地和 `origin` 引用在本批开始时均精确指向给定 SHA。旧候选、旧 OOC 证据和实际工程均未修改。

## 2. 架构与接口合同

- 帧长1024组、步长512组；每组为 `mic0..3` 四个 signed24→int32 PCM、uint64原始编号和4位clip。Verilog总线仍为 `{mic3,mic2,mic1,mic0}`，因此 `m_pcm[31:0]` 是mic0。
- 保留 `session_id/frame_index/interval_index/sample_index/first_id/last_id/reset_before`、停止事件和五类错误事件。非法组截断当前区间，不补样、不重编号。
- 输入仍使用 `s_valid/s_ready`，必须来自可背压的数据源，例如DDR读取器。**本候选不能直接承接不可暂停的PDM/CIC。**
- 主缓存为 `1024×196 bit`，不在复位或会话重启时清零。有效计数、会话状态和首拍同步读取隔离旧内容。
- RTL 每周期最多发起一次写或一次同步读；输出期间暂停输入，写入和读取分时发生。Vivado 最终映射为 simple dual-port BRAM，不能将此描述为物理单端口。没有 `groups[frame_start]` 等第二动态异步读。
- 同步读延迟显式进入状态机。首个有效读出组锁存 `frame_first_id`；输出保持寄存器在 `m_valid && !m_ready` 时保持所有 `m_*` 字段稳定。持续ready后每周期完成一个输出握手，`m_last` 只在第1024个实际握手样本为1。
- 恰好1024组后立即stop时，先输出完整一帧，再产生停止事件；尾部不足帧不补零。

`(* ram_style="block" *)` 只是综合提示；本批确认映射依靠实际 RAM 利用报告和原语清单，不靠属性本身。

## 3. 功能验证

在本目录执行：

```powershell
./reproduce.ps1 -VivadoBin F:/AMD/2025.2/Vivado/bin -RecordName <新的记录名>
```

脚本拒绝覆盖已有证据，依次运行Python模型、XSim编译、边界/协议自检和新旧RTL等价检查。当前完整证据为 [final_run_20260917](evidence/final_run_20260917)；日志使用 `.txt`，避免被仓库全局 `*.log` 规则忽略。

| 检查 | 当前结果 |
|---|---|
| Python模型 | 5个测试方法PASS；覆盖精确长度、250组包界、全部错误类、停止/重启和旧模型等价 |
| RTL协议/异常自检 | `PASS BRAM_FRAMER frames=5 events=10` |
| RTL精确边界 | `PASS BRAM_BOUNDARIES cases=6 groups=0,1023,1024,1535,1536,2048` |
| 冻结旧RTL逐握手等价 | `PASS BRAM_EQUIVALENCE outputs=3072 events=1` |
| 性能观测 | 持续 `m_ready=1` 时，一帧1024个连续握手；从填满到恢复输入暂停1027周期 |

覆盖内容包括四路码值/顺序、ID、clip、首尾ID、帧/会话/区间、`reset_before`；随机输出和事件背压；首拍同步预取、尾拍；1024组立即停止排空；上游错误位、仅非零错误码、编号中断、非法flags/reserved、signed24越界；异常恢复、新session及旧存储内容不泄漏。250组DMA包界仅作为输入编号边界建模，候选本身不处理DMA TLAST。

等价检查允许同步读候选相对旧RTL增加启动延迟，只比较每次**实际握手**产生的完整输出字段和事件序列；3072个样本输出与1个停止事件逐项相同。

首次运行也完整保留，见 [FAILURE-HISTORY.md](FAILURE-HISTORY.md)。本批没有出现真实RTL失败，不伪造失败记录。

## 4. OOC综合：已由拓芙执行

复跑操作单见 [ooc-synthesis-01/README.md](ooc-synthesis-01/README.md)。本次实际命令为：

```powershell
Set-Location 'E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/frame-adapter-bram-candidate-01/ooc-synthesis-01'
./run_ooc.ps1 -RunName bram_ooc_20260918_01
```

固定条件为 Vivado 2025.2、`xc7z020clg400-2`、顶层 `pcm4_overlap_framer_bram`、100 MHz/10.000 ns、Non-Project OOC。脚本不执行布局布线或比特流，不含假路径、多周期路径和虚构I/O延迟。

完成标志是终端同时出现：

```text
BRAM_OOC_SYNTH_COMPLETE_NOT_IMPL_NOT_BOARD
BRAM_OOC_RUN_COMPLETE_NOT_ANALYZED
```

实际结果：261 LUT、0 LUTRAM、608 FF、5 RAMB36E1、1 RAMB18E1、0 DSP；OOC WNS +2.642 ns、TNS 0。主缓存已进入 BRAM，未见原规模 `RAM64M/RAM64X1D`。理论容量约6个RAMB36等效块，本次为5.5个。303个输入/683个输出未设系统级 I/O delay，且没有布局布线；完整限制和关键路径见 [RESULTS.md](ooc-synthesis-01/RESULTS.md)。

## 5. 当前边界与后续判断

| 层级 | 状态 |
|---|---|
| 独立模型与RTL功能仿真 | 已完成，PASS |
| 与冻结旧候选合法输入等价 | 已完成，按握手序列PASS |
| OOC综合/实际BRAM推断 | 已执行，BRAM 映射确认；仅综合估算时序 |
| 布局布线、实现后setup/hold | 未执行 |
| `one`、PS/BD/DMA/PDM/CIC/FFT接入 | 未执行 |
| CDC、外部FIFO、溢出恢复、实板 | 未验证 |
| M1、H3、实时闭环 | 未通过/不在本批范围 |

单缓冲输出期间固定暂停输入；任意下游背压又可无限延长。因此即使OOC结果理想，接不可暂停采集源前仍必须有外部FIFO/DDR、最坏服务时间预算和可观测溢出路径。本批按架构决定不实现双缓冲，也不以功能PASS替代正式算法接口准入。

## 6. 文件入口

- RTL：[rtl/pcm4_overlap_framer_bram.v](rtl/pcm4_overlap_framer_bram.v)
- 模型与测试：[model/framing_model.py](model/framing_model.py)、[tests/test_framing_model.py](tests/test_framing_model.py)
- RTL自检：[sim/tb_pcm4_overlap_framer_bram.sv](sim/tb_pcm4_overlap_framer_bram.sv)
- 精确边界：[sim/tb_pcm4_overlap_boundaries.sv](sim/tb_pcm4_overlap_boundaries.sv)
- 等价检查：[sim/tb_pcm4_overlap_equivalence.sv](sim/tb_pcm4_overlap_equivalence.sv)
- 复跑入口：[reproduce.ps1](reproduce.ps1)
- OOC入口：[ooc-synthesis-01/run_ooc.ps1](ooc-synthesis-01/run_ooc.ps1)
- 文件哈希：[MANIFEST.sha256](MANIFEST.sha256)
