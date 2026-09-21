# 2026-09-21 本地主线同步与重复副本清理

按用户授权执行；不是新增技术验收。

## 同步与重复文件

共享目录 main 从 `fd1b99c966de1f572bcd080f2b2d6860c0ac5ccd` 安全快进至 `3b18e0fe4925a5638800168a2c1608a94741b2a6`。原先阻挡同步的本地文件最终核对为529项，全部与目标Git blob逐字节一致（包括忽略文件），不同内容0项。保存逐文件SHA256/目标blob清单，逐项二次校验后移除重复未跟踪文件，再由快进恢复为受版本管理的正式文件；没有修改其数据、做换行归一化或覆盖独有内容。

此前动态DAS复核记录的“本地同步待处理”在此关闭。旧报告作为历史原件不改写。

## 已删除且可恢复

五个已完成复核工作树逐个检查modified/staged/untracked/ignored均为空，提交都为main祖先，使用不带force的git worktree remove：

| 工作树 | 恢复提交 |
| --- | --- |
| E:/ss-b-dynamic-publish-268e526 | 3b18e0fe4925a5638800168a2c1608a94741b2a6 |
| E:/ss-b-repair-fe67547 | fe67547635ff254f9f91c7f917e8dedb6daf3363 |
| E:/ss-center-audio-review-0915 | e5621cae92108f480a831b4da679f40fe64631c8 |
| E:/ss-four-track-review-0916 | ad9ca72388fb676946c71b13517ab279c11cfc61 |
| E:/ss-real-audio-review-0915 | 058aa3095fd4df7392645004b164adb4eec52041 |

对应四条本地codex/review短期分支（b-dynamic-268e526、b-center-audio-20260915、b-four-track-20260916、b-real-audio-20260915）已安全删除。没有删除远端成员分支。

四个原字节导出副本在检查全部路径/字节/SHA256、无额外文件并保存EXACT-EXPORT回执后删除：

| 副本 | 固定提交 | 原文件数 |
| --- | --- | ---: |
| E:/ss-b-consolidation-b5913e5-exact | b5913e596e28b30f9e04cf2c9ba365430b8914df | 253 |
| E:/ss-b-dynamic-268e526-exact | 268e52627d091b8909890b43586c70564563132e | 402 |
| E:/ss-b-nodes-349501c-exact | 349501c560f7f9d195ebbf52a4c47f34695bfeae | 341 |
| E:/ss-b-repair-fe67547-exact | fe67547635ff254f9f91c7f917e8dedb6daf3363 | 192 |

恢复方式：工作树用 `git worktree add --detach <NEW_PATH> <SHA>`；导出副本用已批准checkpoint/source/prepare_exact.py，指定原准确SHA和新外部目录。输出/失败记录不在这些源副本中，原位保留。逐文件清理清单及四份导出回执保存在本任务外部审计目录，未新增整仓ZIP或重复工程归档。

## 明确保留

- 全部 E:/ss-b-*-run01、postmerge及旧bb964cb-output等原始运行和失败证据。
- E:/ss-b-checkpoint-bb964cb 的三个准备阶段修改及 E:/ss-b-checkpoint-review-publish 的独立未合入报告分支；不能仅凭“旧”删除。
- continuous-*、A操作单、PS bridge、frame adapter及Skills候选等独有/未完成材料。
- 其他任务拥有的工作树、长期分支和远端成员分支。本轮没有证明其全部完成，不批量删除。

本轮清理目标完成；共享目录仍有其他任务未提交文件，不宣称全仓干净。最终本地main、origin/main、直接远端main及ahead/behind在发布回报核验。
