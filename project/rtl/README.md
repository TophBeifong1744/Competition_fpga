# RTL

2026-09-28 #19 候选分支：活动 `servo/motor_drive.v` 已接入与任务包 `d63544d` 候选逐字节相同的 v2：新增 `angle_valid_i` 和 `RESET_ANGLE_DEG`，旧调用点必须显式连接 valid。当前改动及补测是 C/助手作者自检，待 A 按准确提交独立复核；下文 b1d51d4 批准仅覆盖旧 v1 快照。参数及当前入口见[仿真说明](../../simulation/README.md)。

2026-09-17：新增 `servo/motor_drive.v`，C候选 b1d51d4 [限定模块PASS](../../docs/reviews/servo-b1d51d4/REVIEW.md)。这是唯一舵机活动源码，原包保留来源快照；运行见 `simulation/run_servo.ps1`，哈希见 `simulation/modules.json`。未接入 one/BD，未综合或板测；下文三模块/六组为历史收尾记录。

本目录现在是已批准基础模块的活动源码入口，不再只有占位说明。2026-09-11归入以下三件，来源及规范化哈希见[清单](../../simulation/modules.json)：

- common/stream_error_stats.sv：C-001事件计数/sticky；仅统计事件，不推算丢样数。
- common/stream_error_snapshot.v：C-002同域状态快照；不是CDC桥。
- acquisition/pcm4_signext_pack.v：C-003四路符号扩展/组合打包；不是完整采集器或AXIS输出。

六组功能回归通过；仅模块库归位，未接入one/BD/PS或板卡，C004、四路候选及FFT不在本轮范围。原任务包作为历史快照保留。运行见[sim](../../simulation/README.md)，[10日补收尾说明](../../deliverables/phase-2026-09-10/CLOSEOUT.md)。

约定：

- 简单功能模块优先使用 Verilog（`.v`）；复杂核心必要时使用 SystemVerilog（`.sv`），通过纯 Verilog `.v` 顶层实例化包装后接入 BD Module Reference。自检 testbench 可继续使用 `.sv`，已有合格 SV 核心不批量重写。文件名与主要模块名一致。统一交付与验证要求见 [RTL 语言与 BD 接入约定](../../task-packages/PKG-A-H3-INTEGRATION/references/policy/rtl-language-and-bd-integration.md)。
- 流接口遵循 ready/valid 语义；任何丢弃策略必须显式计数并进入状态寄存器。
- 复位方式、时钟域、流水延迟、定点 Q 格式和最大增益写在模块头注释中。
- 位宽缩减统一执行已说明的舍入与饱和，禁止依赖隐式截断。
- 核心算法不得调用不可追踪的软件结果替代；允许使用 AMD/Xilinx FFT 等 IP，但其配置必须可复现并纳入版本控制。
