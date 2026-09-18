# C 旧任务复核发布收尾（2026-09-18）

## 已执行

- 技术范围与结论见 [REVIEW.md](REVIEW.md)，候选 1731522f80ed0b970c63c8a3b019b9ba281d6ca8；仅发布限定复核及状态记录，未将旧候选整条合入。
- 复核提交 `212c41abdadc346c8e18f9cbeb19f79b16d9f128` 已从复核分支快进到 main 并正常推送；当次实际共享目录 main、origin/main、直接 ls-remote 均为该 SHA，领先/落后 0/0。
- main 最终活动路径运行 `python deliverables/six-mic-acoustic-review-v1/verify_package.py`：24 个包文件、15 个结果、源码/config 对应均通过；Git diff 确认冻结包没有内容变更。
- 审计脚本从最终仓库路径独立复现，见 [reproduce.log](reproduce.log)。先前失败日志 [rel6-active.log](rel6-active.log) 保留，未隐藏失败。
- 8 个本机冻结包文件只恢复已有 Git 原字节，索引刷新后无内容差异。不修改 .gitattributes 或冻结清单。
- 批次遗漏检查发现全局 *.log 忽略了 5 份本轮日志；明确逐文件纳入版本管理，未改忽略规则，随后以本收尾提交发布。
- 已修改/暂存/未跟踪/忽略项按本批路径检查：有用记录均入本批提交，既有冻结原始证据保持原位。未发现无关未提交工作；最终三端核对在推送本收尾提交后执行。

## 保留和清理

- 本轮短期本地分支 `codex/c-legacy-review-20260918` 已完成快进与首次远端确认，按规则安全删除；恢复点为 212c41abdadc346c8e18f9cbeb19f79b16d9f128。
- 旧远端 `codex/toph/pending-review-packages-20260908` 含未批准范围，保留；所有其他成员分支、任务包、原始证据保留。
- 本轮无复核工作树，没有删除用户文件。临时独立导出位于 Codex work/c-review-20260918/committed 和 work/c-review-reproduce-20260918/committed，可由固定 SHA 的 git archive 重建；它们不是活动工程，也无唯一用户数据。
- 待 A 处理：WP-A0 历史清单异常与错误全通过表述；3D-P4 现行依赖/职责/证据边界。WP-S1 已退役，不作为 C 新待办。3D-P2 与 REL6-001 仅在本轮限定范围完成复核。

本收尾提交只补公开复核日志与发布记录，不增加技术批准范围。各成员其他电脑未核查，不能代签同步。
