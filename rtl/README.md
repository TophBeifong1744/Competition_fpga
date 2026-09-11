# RTL

本目录现在是已批准基础模块的活动源码入口，不再只有占位说明。2026-09-11归入以下三件，来源及规范化哈希见[清单](../sim/modules.json)：

- common/stream_error_stats.sv：C-001事件计数/sticky；仅统计事件，不推算丢样数。
- common/stream_error_snapshot.v：C-002同域状态快照；不是CDC桥。
- acquisition/pcm4_signext_pack.v：C-003四路符号扩展/组合打包；不是完整采集器或AXIS输出。

已接入模块库与统一仿真，未接入one的BD/PS或板卡。四路采集候选、C004包装和FFT不在本清单。原task-packages快照只读，不双线维护同名源码。运行见[sim](../sim/README.md)，本阶段收尾见[说明](../deliverables/phase-2026-09-10/CLOSEOUT.md)。

约定：

- 本轮保留原件语言：简单模块使用Verilog，已有合格SystemVerilog核心不重写；BD入口包装另按批准状态处理，不能把C004待审包装顺带合入。
- 流接口遵循 ready/valid 语义；任何丢弃策略必须显式计数并进入状态寄存器。
- 复位方式、时钟域、流水延迟、定点 Q 格式和最大增益写在模块头注释中。
- 位宽缩减统一执行已说明的舍入与饱和，禁止依赖隐式截断。
- 核心算法不得调用不可追踪的软件结果替代；允许使用 AMD/Xilinx FFT 等 IP，但其配置必须可复现并纳入版本控制。

