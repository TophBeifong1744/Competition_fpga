# 任务一补充交付：四通道可暂停测试源

2026-09-09，追加到 codex/toph/ddr-dma-delivery，供 B 与任务二、三一并复核，不自行合入。

## 文件与来源

original/ 保存原始 RTL、TB、码型/打包合同、README、全部原 evidence/ 顶层文件，以及 evidence/sim/ 的日志和 CSV；共 34 文件逐字节核对一致。来源为 C:/Users/Toph Beifong/.codex/visualizations/2026/09/05/01a06ff9-0287-7e00-b73d-abf12e6b3035/one_task1/。未包含 .Xil、仿真缓存、波形等可再生文件。历史 backup/失败尝试日志保留，不当作最终通过记录。

recheck/ 保存本次独立副本重新编译、展开、运行的四份文件：xvlog.log、xelab.log、xsim.log、accepted_beats.csv。不是覆盖原运行日志。源文件/日志的 SHA-256 见 files.json。

## 复现入口

先复制 original/ 到自己的可写临时目录，再从副本根目录运行：

```powershell
./scripts/run_sim.ps1 -VivadoBin '<Vivado2025.2>/bin'
& '<Vivado2025.2>/bin/vivado.bat' -mode batch -source scripts/synth.tcl -log evidence/synth.log -journal evidence/synth.jou
```

仿真预期 ALL TASK1 TESTS PASS；模块级综合预期 TASK1_OOC_SYNTH_PASS。脚本会写副本 evidence/，不应对冻结原件运行。register_one.tcl 和 run_one_sim.tcl 含原机器工程路径，只作历史记录；不要盲目执行或把 one.before.xpr/system.before.bd 覆盖到运行工程。

## 核查结果与范围

本次原脚本在独立目录复跑四组 S/P 参数：2/2、1/1、3/3、257/257，全部通过；每组含三次完整运行、三次复位中止，检查采样编号、逐拍数据、背压保持、包尾、忙时 start 和 done。>=4 组样本用例逐通道检查首次运行正/负/零覆盖。长例跨过低 16 位码型周期，不代表完整 32 位编号回绕已测。

本轮只重新执行功能仿真；综合结果来自原始 synth.log、utilization_ooc.rpt、drc_ooc.rpt，非本轮新综合。原报告记录 193 LUT、38 FF；原 OOC 警告和未做布局布线/时序验收的限制保留，不因任务二板测通过而抹去。

本次无新增 RTL 修改。原 README 的“尚未接 DMA、仓库外引用”等属于任务一完成时的历史状态；后续 DMA 集成与导出状态见同批任务二、三，不改写历史原件。done 只表明流被接收，不保证 DDR 写完；本测试源可暂停，不能代表真实固定速率音频无丢样。
