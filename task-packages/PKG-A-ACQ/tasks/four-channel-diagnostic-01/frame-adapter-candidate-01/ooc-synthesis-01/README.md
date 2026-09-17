# OOC 综合可行性检查操作单

目标：只对冻结的 `pcm4_overlap_framer` 做 Vivado 2025.2 Non-Project/OOC 综合，获得 Zynq-7020 在 100 MHz 约束下的资源、综合后时序和存储器推断证据。拓芙已完成 `ooc_20260918_03`；结论与边界见 [RESULTS.md](RESULTS.md)。不打开或修改 `one`，不生成 bit/XSA，不执行布局布线或上板。

## 一次运行

关闭无关 Vivado 构建，打开 PowerShell，执行：

```powershell
Set-Location 'E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/frame-adapter-candidate-01/ooc-synthesis-01'
./run_ooc.ps1 -RunName ooc_20260918_03
```

默认使用 `F:/AMD/2025.2/Vivado/bin/vivado.bat`。若安装位置不同，只追加 `-VivadoBat '<实际 vivado.bat>'`。运行名只能含英文字母、数字、下划线和短横线；`runs/<运行名>` 或 `launcher-logs/<运行名>` 已存在时脚本会拒绝覆盖，失败后也应换新运行名，保留原失败记录。

脚本先绑定固定提交、分支、RTL SHA-256、Git blob 和既有 XSim PASS，再读取唯一 RTL 和 [constraints.xdc](constraints.xdc)，以 `pcm4_overlap_framer`、`xc7z020clg400-2`、10 ns `clk` 运行 `synth_design -mode out_of_context`。没有假路径、多周期约束或输入/输出延迟；因此外部 I/O 路径未建立系统级延迟合同，报告中的 unconstrained/OOC 边界必须保留，不能把综合 WNS当实现后闭合结论。

## 完成标志和返回材料

终端最后应出现：

```text
OOC_SYNTH_RUN_COMPLETE_NOT_ANALYZED .../runs/ooc_20260918_03
```

请把下面两个目录原样保留并把终端末尾输出发回工程实现：

- `runs/ooc_20260918_03/`：`STATUS.txt`、源绑定、工具版本、`checkpoint/post_synth.dcp`，以及资源、分层资源、时序摘要、50 条关键路径、check_timing、RAM利用、存储原语清单、高扇出、methodology 和 DRC 报告。
- `launcher-logs/ooc_20260918_03/`：真实命令、退出码、完整 `vivado.log` 和 journal。综合警告以完整 Vivado 日志为准，不通过过滤或压制美化。

只出现 `OOC_PRECHECK_PASS`、没有最终标记，或退出码非零，都不是完成。不要删除失败目录，也不要改 RTL 后重跑来迎合结果。

## 易错点与后续判读

1. 必须从本目录运行包装脚本；不要在 GUI 中把 RTL 加入 `one`。脚本允许共享目录当前 HEAD 仍是 main，但要求本地及 `origin` 候选引用都准确指向 `a7d944a…`，且实际读取的 RTL 字节与冻结提交完全一致。
2. `groups[0:1023]` 为 196 位宽、异步组合读 `groups[rd_ptr]`。7 系列 BRAM是同步读结构，当前写法可能不能直接推断 BRAM；最终以 `ram_utilization.rpt`、`inferred_memory_cells.txt`、综合日志和资源报告共同判定，不能只看 RTL 数组声明。
3. 重点返回 LUT、LUT as Memory、FF、RAMB18/RAMB36、DSP，以及 timing summary 的 WNS/TNS、未约束端点和关键路径。OOC综合后 WNS≥0 只是初步可行；尚未经过 opt/place/route，不能写成实现时序通过。
4. 当前控制在输出 1024 拍期间令 `s_ready=0`；`m_ready` 拉低还能无限延长暂停。因此即便 OOC 资源/时序可接受，真实连续源前仍需要外部 FIFO/DDR 缓冲、最坏服务时间预算和可观测溢出路径。本检查不会证明实时吞吐。
5. 若报告显示大规模 LUTRAM/寄存器或关键路径风险，先只形成结论。后续最多比较两个最小方向：同步读 BRAM 的乒乓/双缓冲，或按 BRAM 端口宽度分银行并用独立输入/输出缓冲解耦；本轮不改冻结 RTL。

### 已保留的启动失败

- `launcher-logs/ooc_20260918_01/`：包装脚本曾把 `-log/-journal` 放在 `-tclargs` 后，参数数量检查在综合前拒绝。
- `launcher-logs/ooc_20260918_02/` 与部分 `runs/ooc_20260918_02/`：绑定预检通过，但 `read_verilog` 的含空格文件名未封装为 Tcl list，在读取 RTL 时失败，仍未开始综合。

两次失败均保留；修复没有改变冻结 RTL。后续必须使用新运行名 `_03`。

完成后由工程实现读取报告并整理：既有 RTL 仿真、本次 OOC 综合、未做的布局布线/工程接入/CDC/实板/H3 准入必须分别陈述。
