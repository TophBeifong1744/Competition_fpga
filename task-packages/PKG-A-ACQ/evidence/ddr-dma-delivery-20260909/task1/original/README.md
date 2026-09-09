# 任务一：可暂停的四通道 PL 测试源

状态：RTL、自检仿真、模块级综合已完成；已向现有 one 工程注册源码和独立仿真集。未接 DMA，未进行板测或时序验收。

文件放在比赛仓库外；one.xpr 通过外部路径引用这里的 RTL/TB，请勿移动或删除本目录。

## 交付文件

| 文件 | 用途 |
| --- | --- |
| rtl/test_source.sv | 可综合 RTL，含中文学习注释 |
| sim/tb_test_source.sv | 独立期望值模型、握手/背压/包尾/复位自检 |
| docs/pattern-and-packing.md | 接口、码型、逐拍格式、边界合同 |
| evidence/acceptance.md | 验收结果与未验证范围 |
| evidence/sim/xsim.log | 独立仿真最终日志 |
| evidence/sim/accepted_beats.csv | 默认首次运行逐拍接收记录 |
| evidence/one_sim.log | 实际 one 工程仿真调用记录 |
| evidence/one_simulate.log | 实际 one 工程完整自检日志副本 |
| evidence/utilization_ooc.rpt | 模块级综合资源报告 |
| evidence/drc_ooc.rpt | 模块级 DRC，注意 PS7 警告及范围限制 |
| evidence/one.before.xpr、system.before.bd | 修改工程前的备份 |

## 如何对照学习

先看 RTL 中四部分：位置寄存器、组合判断、数据通路、时序控制。

组合逻辑和时序逻辑不是程序先后调用，而是同时存在的硬件：当前寄存器决定输出数据；上升沿握手成功后更新寄存器，组合逻辑随之选出下一拍。同一信号只有一个驱动位置。背压时位置寄存器不动，所以有效数据和包尾一起保持。

默认一次 start 发送 2 包，每包 2 组四通道采样；每组 3 拍，共 12 拍、48 字节。done 表示这些拍已被下游接口接收，不表示 DDR 已写完。

## 独立复现

在本目录打开 PowerShell：

```powershell
& .\scripts\run_sim.ps1
& 'F:\AMD\2025.2\Vivado\bin\vivado.bat' -mode batch -source scripts/synth.tcl -log evidence/synth.log -journal evidence/synth.jou
```

仿真脚本默认使用上述 Vivado 2025.2 安装位置，可用 -VivadoBin 指定其他安装目录。最终必须出现 ALL TASK1 TESTS PASS；仅成功启动仿真不算通过。

## 在现有 one 工程中复现

工程：F:/College/verilog_digital_system/AMD/Competiton/one/one.xpr。

已创建独立 Simulation Sources 集 sim_task1，顶层 tb_test_source。选择该仿真集启动行为仿真，再执行 Run All，不要停在默认 1000 ns。也可在本目录运行：

```powershell
& 'F:\AMD\2025.2\Vivado\bin\vivado.bat' -mode batch -source scripts/run_one_sim.tcl -log evidence/one_sim.log -journal evidence/one_sim.jou
```

scripts/register_one.tcl 是本次源码注册脚本，工程已经更新，不必重复注册。工程脚本包含当前机器路径，移机时需先调整路径。

设计顶层仍为 system_wrapper，system.bd 未修改，原有未完成的 pl_data_sorce.sv 未改写。新模块尚未在设计顶层实例化，因此即使重新生成原顶层比特流，也不会自动出现该测试源。后续接入 AXI DMA 时，还需要连接时钟/复位/start、配置接收缓冲区和包长，并验证板上数据；不属于本次已通过范围。

本次未修改 Competition_fpga 仓库，未提交 Git。
