# 交给 C 的增量复核提示词（复制正文）

请按 2026-09-17 增量复核规则独立复核 A 返修的 WP-A0 与 3D-P4。不要把作者自检当批准；只在准确范围内给出 PASS / NEEDS_FIX，并按已获授权的发布规则处理获准内容。

仓库：`Competition_fpga`；返修分支：`codex/toph/c-legacy-wpa0-3dp4-rework-20260918`。文档内容提交为 `07d25f72a382780b7c33caca36a212dfa53be779`；**交审最终 HEAD 请从本次交接消息取得完整 SHA，并用 `git ls-remote origin refs/heads/codex/toph/c-legacy-wpa0-3dp4-rework-20260918` 直接核对**。上轮复核发布基线 `bff9369a5c7f166344c02095df61e91e1c2f4681`；上轮旧包候选 `1731522f80ed0b970c63c8a3b019b9ba281d6ca8`。若远端 HEAD 不同、main 前进或共享目录有他人未提交工作，先固定新对照版本，不回退/重置共享目录。

先读 `AGENTS.md`、`docs/team-workflow.md#review-efficiency`、`docs/reviews/c-legacy-20260918/{REVIEW,PUBLICATION}.md`、`task-packages/WP-A0/README.md`、`task-packages/3D-P4/README.md`，只按 C-01/C-04 及受影响依赖做增量审查。

1. **WP-A0 / C-01**：独立核对 `task-packages/WP-A0/ERRATUM-2026-09-18.md` 所记 `f0f397f` 原始归档 Git blob、原 MANIFEST 的 `f0ceb...`、`1e7e091` 合并所改 WP-C1 状态、当前 Git blob `f188...` 以及包内快照 `541e...`；确认按原清单对包内 25 项是 24/25，而不是 25/25。判断活动 `archive/README.md` 是否把异常说明充分、是否保留历史旧包身份。不得改原冻结文件/清单来消除失败；来源或意图无法证实时保留未知。
2. **3D-P4 / C-04**：以基线 main 的现行指南为对照，检查 `docs/three-dimensional-doa-workflow-skill-guide.md` 是否只更新真实依赖和边界。对照 `skill/README.md`、`docs/maintenance/skills-rereview-b-2026-09-14.md`、`docs/member-c-operation-sheet.md`、当前 10/1 日历与 WP-A0 勘误，确认旧 Skill 已退役、新 Skill 仅获限定模块仿真 PASS、C 现负责转台/摄像头方案落实和驱动/效果测试、历史 10/7/旧职责不复活；三维 G0/GA/G1～G3 不获提前通过。
3. 检查相对链接、文档语义、`git diff --check` 以及旧 payload/原清单/审批记录没有改动。原工作包校验器可重用，但 WP-A0 的原路径 drift 不能误写为完整性通过；未受影响的 3D-P2、REL6-001、SKL-001 限定证据引用上轮准确记录，不重跑无关模型/仿真。

本次申请仅：WP-A0 勘误与活动归档索引更正；3D-P4 活动指南依赖/职责/证据边界更正；两个包的交审入口及本提示词。若通过，请明确批准 SHA 与具体路径、未批准的历史异常，再决定是否按现行发布规则合入 main、做相称验证并完成本批本地/远端核对。不要整条合并旧待审分支，不开启退役 WP-S1，也不扩大或重签 3D-P2、REL6-001 的限定批准。三维算法、整机、RTL/时序、实板、采购均不在本轮申请内。
