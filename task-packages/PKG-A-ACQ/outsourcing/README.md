# C 成员临时外包任务

本目录只管理 A 的采集工程包中的临时外包，不改变项目正式分工。A 保留任务所有权，C 按规格实现；本聊天进行技术检查和独立测试，B 保留父包复核与合入职责。

每批只安排 **1～2 项**。本批唯一新任务为 **C-RTL-005：四通道窗口峰值监测RTL**。004技术验证通过，004-R2清单/说明问题按用户要求[暂缓且不阻塞](review-status/c004-r2-deferred-20260911.md)，不再占用C的开发时间。001～003不重做，正式成员分工不变。

| 编号 | 中文任务说明 | C 成果目录 | 状态 |
|---|---|---|---|
| C-RTL-001 | [错误统计 RTL 外包说明](C-RTL-001/instructions/README.md) | [submission](C-RTL-001/submission/README.md) | ac8a7bb 功能独立复测通过；用户告知 B 已复核；GitHub PR #4 已合入 main，见下方证据边界 |
| C-RTL-002 | [错误统计快照 RTL 外包说明](C-RTL-002/instructions/README.md) | [submission](C-RTL-002/submission/README.md) | 48af341 独立功能 PASS；用户确认 B 技术复核通过，无需返工，待 A 集成；[历史验收](C-RTL-002/review/48af341/README.md)、[B 结论登记](review-status/b-c002003-20260910.md) |
| C-RTL-003 | [PCM 打包 RTL 操作单](C-RTL-003/instructions/README.md) | [submission](C-RTL-003/submission/README.md) | d41ee30 独立功能 PASS；用户确认 B 技术复核通过，无需返工，待 A 集成；[历史验收](C-RTL-003/review/d41ee30/README.md)、[B 结论登记](review-status/b-c002003-20260910.md) |
| C-RTL-004 | [原操作单](C-RTL-004/instructions/README.md)、[R2暂缓决定](review-status/c004-r2-deferred-20260911.md) | [submission](C-RTL-004/submission/README.md) | 69dd471功能及空格路径BD独立技术PASS；清单/说明暂缓，不阻塞005；[复核记录](C-RTL-004/review/69dd471-20260911/README.md) |
| C-RTL-005 | [窗口峰值监测RTL操作单](C-RTL-005/instructions/README.md) | [submission](C-RTL-005/submission/README.md) | 本批唯一新任务，待实现；不要求板测/BD/精细补证 |

说明与成果分目录保存，C 不改 instructions。修订实现沿用同一成果目录和版本记录，不为每个小动作开新任务。文件生成不代表 C 本人已收到通知，更不代表验收通过。

## 上批关闭依据及本批边界

2026-09-09 查询 GitHub：C 分支 head 为 ac8a7bb60d94c069f5f1b61e9fc38658b0742962，[PR #4](https://github.com/TophBeifong1744/Competition_fpga/pull/4) 状态 MERGED，main 合并提交为 1ec105f609ac52d7b97d3245a90dc212591c1cfa。B 已完成复核由用户告知；本次没有取得单独 B 复核记录，不代签其具体检查项。此前独立验收的功能 PASS 不扩展为综合、时序或板测通过。

本次沿用 codex/c-rtl-001-outsourcing-docs 分支发布暂缓决定和005说明，不合并 main。分支名称沿用不代表任务编号仍为 001。A 保留模块用途与集成决策；C只按005固定规格开发小模块和自检TB，正式复核及合入按原职责办理。不操作共享one/PS/DMA，不冻结实际采集或DMA接口，不追加新审批点。004-R2不再是当前任务；旧报告保留其当时状态。
