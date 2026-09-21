# PKG-A-ACQ · 工程与采集/导出包

2026-09-21范围更新：PS语义桥返修准确`ca512a8`、合同与条件预算准确`f08556d`均获B限定PASS入main，见[本轮批准及收尾](../../deliverables/phase-2026-09-18/readiness-closeout-20260921.md)。有效主机C入口为`tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/ps-semantic-bridge-repair-01/src/`；原candidate错误版只保留历史。合同入口为同父目录`PRODUCTION-READINESS-20260921.md`，最新批准以复核报告及收尾覆盖历史待审文字。均未安装到Vitis/one，未批准生产ABI、硬件实时或完整H3，完整包仍进行中。

2026-09-12 当前说明：四路杜邦线诊断已获 B 接收，见 [B-REVIEW](deliveries/dupont-diagnostic-20260911/B-REVIEW.md)。待审工程包另行发布，不将诊断接收扩大为工程整体验收。下面 9 月 9 日旧接线草案已集中到[历史原件](../../archive/2026-09-12-local-materials/README.md)，由已选 C 板方案替代，不再作为当前待接线/待补证任务。

## 2026-09-10 电气与时序补证

[补证包](evidence/existing-electrical-timing-audit-2026-09-10/README.md)包含 DS187 来源、截图、布线检查点、只读报告导出脚本、计算自检与文件清单。内部时序通过，但 DATA 低电平规格边界和外部接口时序尚未闭合。按拓芙最新决定，[这些事项暂缓](../../docs/deferred-acquisition-risks.md)，原处理单只作问题回查资料，不作为采集开发、扩通道或联调的前置任务。继续按已知安全接线依据推进功能，遇到难定位问题再针对性处理；不把暂缓写成已验收。

负责人：A 拓芙。技术复核与合入：B BryanZheng802。完整包状态：进行中。

本包已包含经 B 审核合入的 H1 软件交付与待复核的 DDR 五模式自检交付，不代表完整采集包已验收或 H2/H3 通过。现有 one 工程不重复创建。

## 麦克风接线文档增量（2026-09-09）

[候选接线与现场核验单](../../archive/2026-09-12-local-materials/task-packages/PKG-A-ACQ/payload/hardware/microphone-wiring-candidate.md)已按底板/核心板原理图及模块资料整理，版本 mic-wiring-draft-0.1，待 B 复核。首轮候选为 J4 Bank 13、四路独立 DATA；未生成正式 XDC，未接板、未改 H1、未合入活动 hardware 目录。[资料核验与清单](../../archive/2026-09-12-local-materials/task-packages/PKG-A-ACQ/evidence/microphone-wiring-v0.1/README.md)列出来源与现场缺项。本增量不改变 DDR/H1 历史审核状态。

## DDR 自检交付（2026-09-08）

[DDR 证据入口](evidence/ddr-five-pattern-v1/README.md)：源码、链接脚本、构建描述、当前 ELF/XSA/bit/初始化文件、ELF 检查和用户回传三轮结果。用户确认五模式三次通过，作者侧源码/ELF 检查完成，B 复核待进行。逐轮原始串口文件未提供，不伪造；不扩大为完整 DDR、PYNQ 或采集验收。

## H1 审核与合入状态

2026-09-10：A 已对 B 既有审核的同一 `ss-data-draft-0.3` 清单明确确认，本次复核 7/7 文件哈希与字节数、两个固定样例通过；**H1 软件约定完成**，准确版本及范围见 [REVIEW.md 最新确认](REVIEW.md)。以下历史审核叙述不表示 A 仍待确认；不改变完整包及硬件验收状态。

保留远端交付入口：[单麦诊断发布说明](../PKG-A-H2-MONO-DIAGNOSTIC/PUBLICATION.md)。它记录当时的限定发布，不代表四路H2；四路当前状态以[统一状态页](../../docs/current-status.md)为准。

B 已审核 H1 提交 `5f0dc36`，通过范围及其记录的 112 项回归见 [REVIEW.md](REVIEW.md)；H1 已由 `be74e0a` 合入 main。A 的共同确认仍按独立记录管理，不能据此推定完整包、DDR、H2/H3 通过。

## H1 入口

- [接口候选](payload/docs/minimal-data-interface.md)：ss-data-draft-0.3。
- [固定码型](payload/examples/h1/code-pattern/metadata.json) 与 [CSV](payload/examples/h1/code-pattern/samples.csv)。
- [重启片段](payload/examples/h1/restart/metadata.json) 与 [CSV](payload/examples/h1/restart/samples.csv)。
- [读取器测试预期](payload/examples/h1/reader-test-plan.json)：B 实现读取器时消费；不是已运行测试的成绩单。
- [样例自检](payload/scripts/check_h1_fixtures.py)：只核验这两个样例，不替代 B 的读取器或公共 TB。
- [确认记录](REVIEW.md)、[清单](manifest.md)。

在本包 payload 目录运行 `python scripts/check_h1_fixtures.py`，只需 Python 标准库。预期输出固定码型和重启样例检查通过；不会写文件或连接板卡。

## A/B 交接

A 负责按约定导出；B 负责读取器及完整正/负例测试。双方一次确认格式、编号/错误语义及暂定参数即可开始，不必等全套 M0、接板或一小时长稳。

历史进展：A 曾回传 B 已按 ss-data-draft-0.3 完成读取器、错误检查和连续区间识别，47 项测试通过，覆盖所列 15 项；这是用户转述，作者侧未独立查看 B 源码与测试日志。后续导出沿用 0.3；共同版本确认与完整包审批分别记录，不能由该消息推定 DDR 或完整包已获 B 批准。旧 hsc119 技术复核安排不再适用。

## C 外包说明

[C 外包入口](outsourcing/README.md)与错误统计模块任务说明保留；任务说明存在不代表 C 已提交实现或通过验收。
