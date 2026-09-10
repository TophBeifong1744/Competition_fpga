# C-RTL-002 独立技术验收

日期：2026-09-09；验收对象：48af34164e24679f4c450380a83d24ab1081eece，分支 codex/c-rtl-001-outsourcing-docs。

结论：**规格检查与功能仿真 PASS，无需 C 返工，可交 B 正式复核。** 本记录不是 B 签字，也不批准总工程合入。下一项独立小模块可并行开始，无需等待 002 集成。

## 版本与原件

本次在隔离副本按准确提交检查，不依赖共享目录的当前 checkout。作者 submission 保持逐字节不变；其 file-manifest.json 中 53 个条目的 SHA-256、字节数全部匹配。参考 001 的 SHA-256 为 333dc4d193169982a6609c886a48968e87ef2631496d0c90137d24f228a94afe，与指定来源一致。

被测 RTL：../.. 下 submission/rtl/stream_error_snapshot.v，SHA-256 为 fe4b8bd5559ca8883044c23406f0dc637d72844bcc767c3320941ba025d6abe6。原件由上述 Git 提交及作者清单固定，本目录只存独立验收源码和日志，不覆盖原件。

原操作单使用 .sv 文件名，作者 README 记载后续要求改用 .v。此次按实际 Verilog 编译验证，端口、行为、参数不变，因此作为等价源码交付接受；不将后缀差异列为功能缺陷。未把作者自查报告当成本聊天独立执行记录。

## 已执行项目

工具为本机 Vivado/XSim 2025.2，SW Build 6299465。未使用 PATH 中的旧版工具。

| 项目 | 结果 | 证据 |
|---|---|---|
| 规格/RTL 静态检查 | PASS | 同步低有效复位、请求捕获、保持、valid 逐拍跟随请求均相符，无额外级或接口扩展 |
| 作者标准四位宽 TB 重跑 | PASS | [日志](logs/author/tb_stream_error_snapshot-simulate.log)，实例完成时合计记录 4676 次比较 |
| 作者全位宽 TB 重跑 | PASS | [日志](logs/author/tb_stream_error_snapshot_all_widths-simulate.log)，64 个实例完成时合计记录 62592 次比较 |
| 作者 001+002 联合 TB 重跑 | PASS | [日志](logs/author/tb_stream_error_snapshot_integration-simulate.log)，32 步 |
| 新独立单模块 TB | PASS | [日志](logs/independent/simulation.log)，1～64 位共 165888 次五输出比较 |
| 新独立联合 TB | PASS | 同上，12289 拍检查快照和实时统计结果 |
| 作者六项错误注入证据 | 已核对，未独立重跑 | 作者 logs/mutations/ 的失败用例和 summary 一致；不是本聊天新增测试成绩 |
| 作者 1/32/64 位综合证据 | 已核对，报告支持可综合性 | 作者报告 FDRE 为 5/67/131，无锁存器/异步触发器；不是本机复现成绩 |
| 本机综合复跑 | BLOCKED_ENV | [原始日志](logs/synthesis-attempt.log)，输出路径创建失败，未执行到综合 |
| 布局布线、时序、板测、CDC、PS 读取、总工程集成 | NOT_RUN | 不在本次已验证范围 |

作者标准与全位宽测试有重复覆盖，不相加冒充独立用例；比较次数均不是形式证明。此次独立仿真结束于 122896 ns，最终标志 REVIEW ALL PASS widths=1..64 and joint。

## 独立测试方法

[tb_independent.sv](tb_independent.sv) 由验收方另写，不引用作者 checker：

- 各位宽按每个数据位 walking-one/complement 与全部四种 sticky 组合捕获，下一拍改变 live 检查保持。
- 每位宽 1000 拍固定种子数据与不同请求/复位序列；包含 64 位高位。
- 采样沿之间改变输入及制造短复位/请求脉冲，输出须保持。
- 联合测试对全部 32×32 种有序两拍控制组合检查；每组先真实计数到饱和，不 force 内部状态。
- 参考模型先生成本沿快照预期，再更新事件计数，独立核对“同沿捕获旧值”语义。

这不是全状态空间穷尽。所有输入以同步为假设，未覆盖亚稳态、非法参数或硬件未知态。

## 复现

从本目录执行，OutputDirectory 使用一个尚不存在的目录：

```powershell
./run_independent.ps1 -VivadoBin '<Vivado2025.2>/bin' -OutputDirectory '<new-run-directory>'
```

脚本按相对路径使用 ../../submission 原件，编译新 RTL 为 Verilog、参考与独立 TB 为 SystemVerilog，检查逐步退出码和最终 PASS。输出为 xvlog.log、xelab.log、simulation.log 及临时仿真缓存。作者三组重跑使用 ../../submission/run_tests.ps1 和独立 RunDirectory；其源码已经静态检查后才执行。

综合尝试使用作者 audit_synthesis.tcl，实际在 file mkdir 阶段报告不能创建 C:/Users/Toph Beifong/visualizations（permission denied），且启动时带 TclStore 告警。没有将此错误归因于 RTL，也没有重置全局环境。未取得本机综合结果，任务书中该项为可选，不否决已通过的功能验收。

## 交给 B 的重点

快照 valid 是本拍更新指示，不是永久有效标志。连续请求会连续覆盖；读取端如果分多拍读取，必须由 A 在集成时安排冻结/握手，不能凭本模块声称 PS 读取原子性或 CDC 安全。同沿事件/clear 请求捕获的是 001 沿前状态。

本次只推送此独立记录、测试与原始日志及下一项操作单；不修改 C 的实现、作者记录或正式分工，不合并 main。
