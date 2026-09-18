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

## 2026-09-18 C-01 / C-04 增量发布收尾

- 批准：62a252081d52b3aa9d9dc142f7cc2bf298d9c34d 的六份文档，准确路径、独立证据及保留异常见 [INCREMENTAL-REVIEW.md](INCREMENTAL-REVIEW.md)。WP-A0 仅勘误/索引 PASS，历史完整性仍 24/25；3D-P4 仅指南依赖/职责/证据边界 PASS。
- 并发主线：发布前发现 main 前进至 085dbdbb4f369bd40b0459513cbe909e9acf5acc，已检查其五文件阶段更新及受影响依赖，保留后合并候选。合并 eeb1c10ebc6f0d7829cab88136d2dde2fb9e5345；独立证据提交 20baf2a63a01a53caea68f1e8f9cc49ab701d530，已正常推送。未合并旧待审分支。
- 相称验证：最终活动路径 70 个相对链接可达，六份批准文件与候选逐 blob 相同，冻结目录/payload/原清单/旧包审批无差异，git diff --check 通过。详见 incremental-evidence/postmerge.json。依赖更新不改变指南语义，无需重跑模型、Skill、RTL 或板测。
- 三端核对：2026-09-18 本记录补交前，实际共享目录 C:/Users/hsc/Desktop/fpga_clone/Competition_fpga 的 main、origin/main、直接 ls-remote main 均为 20baf2a63a01a53caea68f1e8f9cc49ab701d530，领先/落后 0/0。全工作区修改/暂存/未跟踪为 0，本批路径额外检查忽略项为 0。没有他人未提交工作需要处理；不代签 A/B 设备同步。
- 材料：独立审计 JSON、固定脚本、两个准确字节包日志、共享工作树日志、合并后检查和首次 Windows PowerShell 环境失败均已提交。失败日志尾随空白触发 diff --check，改用 JSON 保存可逆 base64 原字节及可读内容，未删除失败。辅助审计早期 cwd/断言问题及工具边界在复核报告如实说明。无本批有用材料未说明遗漏，不改忽略规则。
- 清理：远端短期 codex/toph/c-legacy-wpa0-3dp4-rework-20260918 已按准确 62a2520 lease 删除；本地无同名分支。准确候选由 main 合并父链恢复。旧 codex/toph/pending-review-packages-20260908 仍为 1731522f80ed0b970c63c8a3b019b9ba281d6ca8，保留，不启动 WP-S1。
- 临时副本：仅删除本轮 Codex work/c-incremental/run3/exact 与 run4/exact 两个可重建 Git 字节导出（非活动工程），先验证绝对路径位于本轮工作目录；原件在候选提交，已发布 audit.py 可重建。未删除用户证据、其他任务或活动工程。
- 本批技术复核与首次发布核对完成；本收尾记录提交后再次查询三端 main、批准文件与短期分支缺席，最终 SHA 在用户回报中给出，避免文件自引用。本记录不增加任何技术批准或阶段验收。
