# A 拓芙：把四路短录音交给B

2026-09-12 B 更新：工程整理交付 `2aed019` 已通过限定工程材料/诊断软件复核，[准确范围与复跑入口](../../../task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/b-review-20260912/README.md)。无需重复派发这批文件或原杜邦线录音；后续继续现有诊断准备，实际工程重建环境、外部时序和 C 板实物未获本次批准。

2026-09-12 当前覆盖状态：本批四路杜邦线数据已获 B 独立接收，见[准确回执](../../../task-packages/PKG-A-ACQ/deliveries/dupont-diagnostic-20260911/B-REVIEW.md)。不再重复转交或要求重录。待审工程源码与后续诊断准备另按[发布整理入口](../../maintenance/local-materials-2026-09-12.md)继续；H2 诊断交接完成不代表正式 M1、C 板实物或完整 H3。以下晚间回执未到的描述保留为历史。


2026-09-11晚间进度：杜邦线四路安静/人声各32000组已录得，A交接前格式/原始数据复核通过；拓芙已试听人声清晰。当前任务转为[把完整包交B诊断](https://github.com/TophBeifong1744/Competition_fpga/blob/codex/toph/four-channel-engineering-review-20260912/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/review/dupont-20260911/B-HANDOFF.md)，不是重复扩路或重录。B本人任务不可直接连接，待用户转交及回执；H2四路交接尚未关闭。实际未用C板实物，未知坐标保持null，不改变后续采用C板的决定。下方开工清单保留历史，最新版本见[复核记录](https://github.com/TophBeifong1744/Competition_fpga/blob/codex/toph/four-channel-engineering-review-20260912/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/review/dupont-20260911/REVIEW.md)。

期限：9月16日检查；有可用片段立即交接。主责A，技术复核B。沿用Vivado 2025.2、已确认领航者Zynq-7020与原定麦克风，不改选型。

## 今天先做什么

2026-09-11更新：采用 C 转接板已由拓芙决定，当前执行[四 CLOCK/四 DATA 适配说明](../../../hardware/microphone-adapter-decision.md)。保留同一内部时基，按 C 板更新物理端口/有效约束和通道标签，不重新比较板型或要求 C 回退旧图。读取最新工程后只做剩余适配，不重做已完成实现；[小风险集中暂缓](../../deferred-acquisition-risks.md#c-adapter-risks)，不追加精细补证前置。

1. 继续“SoundSight｜工程实现”已有适配任务，不重新从单麦写四路。15:50核对已见四路RTL/PS、四CLOCK候选/XDC和功能自检；剩余为有效BD/XDC与构建、上板验证，实际状态见决定页。尚无整体验证通过证据，不将接到任务当作完成。
2. 按已知实际接线配置四路；代码保持共同采样时基、固定通道顺序、明确编号和错误标志。实物接线缺失时先写参数化代码/TB，不猜引脚、不凭占位表接板。
3. 对新增通道排列、符号扩展、背压/丢样和停止/重启做相应功能检查。码型用于检查数据链，不代替录音。
4. 录得首批可用四路片段后立即导出给B，随后再完善采集稳定性；不等精细测量或一小时测试。

## 本阶段交付

在既有 `task-packages/PKG-A-ACQ/` 内持续开发；稳定交付集中到 `tasks/four-channel-diagnostic-01/`，包括：

- README：工程/源码入口、操作步骤、实际改动和未完成项。
- source或来源清单：实际修改源码、TB、导出器及可重复的工程恢复入口；不复制整个旧仓库。
- captures：每次采集独立子目录，原始数据、H1格式samples.csv、匹配metadata.json和来源说明；若原始格式不同，提供转换入口。
- evidence：本次实际运行的测试/日志、B回执；未执行项写未执行。

沿用H1 `ss-data-draft-0.3` 的六类约定（不是六列CSV）；CSV按原合同七列，实际通道数必须为4才称四路，不能复制单麦凑四列。sample_id保持原始编号，间断不补零冒充连续。元数据注明 `evidence_level=diagnostic`、实际抓取点、source_kind、配置和未知项。声源方位/摆放条件知道多少记多少；没有坐标依据不报告角度精度。

首轮实际核对已指出：现有1 MiB保留区装不下候选32字节/组格式的48000组。可先按32000组/约0.667秒导出，不要求先扩区；该内部记录布局已有待审RTL/PS候选，不再记为从零待实现，不更改H1文件合同。具体开工位置见[开工单](../../../task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/NEXT-ACTION.md)。

建议至少一段安静背景、一段语音/播放声，先录到一段就交B，不等完整场景库。新的运行记录顺手关联所用构建文件；不为这次任务倒查历史bit/ELF/XSA或补精细电气证据。

## 并行工作与边界

- FFT候选及H3约束已交付，向B提供既有准确版本即可；暂未复核时继续采集，不重做相同预算包。
- 可以在待审任务包中迭代，不能把未获准的算法或C004直接覆盖总工程活动文件。
- PYNQ仍为首选控制/验证层，但镜像迁移不阻塞当前数据出口；PL实时数据面不改成Python处理。
- 工作执行任务负责实际代码/步骤；H2支持任务只帮助检查导出格式，避免两边同时修改同一模块。

9月16日先展示：四路数据在哪里、如何导出、B能否读取、已知故障是什么。正式采集是否通过另列，不用写大报告代替演示。
