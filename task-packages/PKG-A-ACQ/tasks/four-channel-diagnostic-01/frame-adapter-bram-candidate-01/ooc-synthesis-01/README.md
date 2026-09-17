# OOC 综合操作单（等待拓芙执行）

目标：只对 `pcm4_overlap_framer_bram` 做 Vivado 2025.2 Non-Project/OOC 综合，判断主缓存是否真正映射到 Block RAM，并取得 Zynq-7020、100 MHz 下的资源和综合后时序估算。拓芙已完成 `bram_ooc_20260918_01`；判读见 [RESULTS.md](RESULTS.md)。本入口不会修改 `one`，不会执行实现、比特流或上板。

## 一次运行

关闭其他正在构建的 Vivado 任务，在 PowerShell 中执行：

```powershell
Set-Location 'E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/frame-adapter-bram-candidate-01/ooc-synthesis-01'
./run_ooc.ps1 -RunName <新的运行名>
```

默认使用 `F:/AMD/2025.2/Vivado/bin/vivado.bat`。安装位置不同时追加 `-VivadoBat '<实际 vivado.bat>'`。运行名只能含字母、数字、下划线和短横线，且必须是新名称；脚本拒绝覆盖已有运行或启动日志。

脚本先绑定两项基线提交、旧/新 RTL SHA-256 和三项 XSim PASS 标记，再读取唯一 RTL。约束中只有 `clk=10.000 ns`；没有假路径、多周期路径或虚构 I/O delay。

## 完成标志

终端最后应同时出现：

```text
BRAM_OOC_SYNTH_COMPLETE_NOT_IMPL_NOT_BOARD ...
BRAM_OOC_RUN_COMPLETE_NOT_ANALYZED ...
```

只出现 `BRAM_OOC_PRECHECK_PASS` 不算完成。失败时保留对应的 `launcher-logs/<RunName>/` 和可能存在的 `runs/<RunName>/`，换新运行名复测，不删除首错。

本次原始证据已保留；复跑完成后也应保留下列内容：

- `runs/bram_ooc_20260918_01/STATUS.txt`、`source-binding.txt`、`tool-version.txt`；
- `checkpoint/post_synth.dcp`；
- `reports/utilization*.rpt`、`ram_utilization.rpt`、`storage_primitive_inventory.rpt`；
- `timing_summary.rpt`、`critical_paths.rpt`、`check_timing.rpt`；
- `drc.rpt`、`methodology.rpt`、`high_fanout_nets.rpt`；
- `launcher-logs/bram_ooc_20260918_01/vivado-transcript.txt`、`vivado.jou`、真实命令和退出码。

## 易错点和判读边界

1. 必须运行本目录的 `run_ooc.ps1`，不要把候选 RTL 加进 `one`，也不要在 GUI 中替换旧分帧器。
2. 路径包含空格，Tcl 已用 list 封装；不要把参数顺序改成 `-tclargs` 后再放 `-log/-journal`。
3. 重点看 RAMB18/RAMB36、LUT as Memory、`RAM64M/RAM64X1D` 和 `storage_primitive_inventory.rpt`。`ram_style="block"` 只是提示，只有综合报告出现实际 RAMB 原语才算主缓存进入 BRAM。
4. 理论容量约为 6 个 RAMB36 等效块，但实际拆分、奇偶校验位和控制开销以 Vivado 报告为准；不要预填结论。
5. WNS/TNS 是 OOC 综合估算，外部端口没有系统级 I/O 延迟合同，也未执行布局布线；非负 WNS 不能写成接入后时序通过。
6. 功能仿真测得持续 `m_ready=1` 时输出握手跨度为 1024 周期，单缓冲从填满到恢复输入共暂停 1027 周期。下游背压可以无限延长暂停，因此真实不可暂停采集源之前仍需外部 FIFO/DDR、最坏服务时间预算和溢出可观测路径。
