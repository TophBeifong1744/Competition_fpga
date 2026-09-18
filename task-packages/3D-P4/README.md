# 3D-P4 · 三维工程 Skill 适配指南

## 2026-09-18 返修交审入口（作者提交，C 尚未复核）

- 分支：`codex/toph/c-legacy-wpa0-3dp4-rework-20260918`；返修**内容提交**：`07d25f72a382780b7c33caca36a212dfa53be779`；最终交审 HEAD 包含本入口和提示词，以交审消息中的直接远端 SHA 为准。上次 C 发布基线：`bff9369a5c7f166344c02095df61e91e1c2f4681`；上轮候选：`1731522f80ed0b970c63c8a3b019b9ba281d6ca8`。
- **C-04 逐项回应**：以 main 现行[指南](../../docs/three-dimensional-doa-workflow-skill-guide.md)为底修订，未覆盖 9/8 旧 payload。旧 `soundsight-engineering-workflow` 明示退役；现行 `fpga-module-verification` 按[Skill 索引](../../skill/README.md)与[B 复核](../../docs/maintenance/skills-rereview-b-2026-09-14.md)写为**限定模块仿真 PASS**，非待审、非三维/整机/实板通过。旧 G0～G7 明示历史分类，不用退役模板作活动依赖。C 按[9/17 操作单](../../docs/member-c-operation-sheet.md)负责转台、摄像头方案、驱动和最终效果测试；V1 现行日历 10/1，9/14 只作已发生检查。§5.2 引用[WP-A0 异常勘误](../WP-A0/ERRATUM-2026-09-18.md)及 REL6-001 限定复核，不宣称 25 项全部通过。
- 相对上次的文件变化：仅 `docs/three-dimensional-doa-workflow-skill-guide.md` 的现行依赖、职责、日历与证据措辞，以及本交审入口；旧 payload、清单、自检和审批记录不改。**拟接入 main**：现行指南与本 README；不接入旧 payload，不修改两项 Skill、三维总计划、RTL、板卡或采购文件。
- 本次运行：核对现行 Skill 索引/B 复核、C 操作单、V1 日历及 C 上轮结论；对本轮活动文档做相对链接/空白检查；原 `verify-toph-handoffs.ps1 -PackageId 3D-P4` 退出 0，旧单文件 payload 未动。复用已获限定批准的 SKL-001、3D-P2、REL6-001 既有证据，不重签；未运行六麦模型、RTL/XSim、Vivado、板测或采购核验。
- 未解决：三维 G0/GA/G1～G3 仍受原阶段门限制，外设实际型号/板级效果也未在本指南验证。申请 C 仅批准本次**活动指南的文档语义与依赖对齐**；不得扩大为三维算法、整机或实板 PASS。`REVIEW.md` 的 NEEDS_FIX 是上轮结论，待 C 对新准确 SHA 增量复核。

## 2026-09-18 上轮复核状态（保留历史，不代表返修结论）

**NEEDS_FIX（旧版不接入）**。旧包以已退役 soundsight-engineering-workflow 为活动依赖，并保留旧交期及“25 份原件”表述。现行主线已有替代说明，仍须由 A 对齐当前 Skill 批准状态、C 职责和历史异常后，按新 SHA 申请活动指南复核。

复核归属：C / hsc119；实际执行：Codex，依据 C 本次明确授权代复核并按范围发布。不是补造人工逐项签字或阶段门验收。
候选提交：`1731522f80ed0b970c63c8a3b019b9ba281d6ca8`；主线对照：`5cfa02e51af44bb5c930babf732ddc864a1ab6cd`。
完整范围、实际检查、失败及发布收尾见[本轮复核入口](../../docs/reviews/c-legacy-20260918/REVIEW.md)。

## 原交付与历史记录（原状态不再代表当前结论）

- 负责人：拓芙；指定复核人：hsc119。
- 版本：2026-09-08-r1；状态：待复核（非已通过、非已合入）。
- 整理日期：2026-09-08；保留原工作包期限，不因打包重置。

## 本次交付

现行三维工作流适配指南单文件快照；不是新 Skill，也不修改现有 Skill 实现。

仅文档指南待复核；本轮未运行行为测试、模型或板测，不能签为 Skill 新版行为通过或阶段门通过。

## 如何复核

1. 阅读 [清单](manifest.md)、[自检记录](evidence/self-check.md) 和 [审批记录](REVIEW.md)。
2. 从仓库根目录运行 `powershell -NoProfile -ExecutionPolicy Bypass -File task-packages/verify-toph-handoffs.ps1 -PackageId 3D-P4`，核验包内文件和只读证据副本的哈希；原路径漂移独立报告，不自动修改原文件。
3. payload 保留总工程相对目录；未打包的公共依赖仍按原仓库路径读取。包内原文相对链接可能指向未快照的公共文件，本包不是独立运行工程。
4. hsc119 核查现行阶段门、依赖、失败案例与实际内容，明确批准范围及文件版本，或提出退回项。修改一律先在本包 payload 准备，更新清单后重新复核。

## 合入边界

只批准某份文档不等于批准其描述的硬件功能。推送任务分支也不是合入。由 hsc119 决定是否及如何合入准确版本；助手代执行需有针对该次合入的明确授权。作者及本聊天不自审自合。既有总工程和冻结证据保持原位；已有文件存在不表示此前获人工批准。

共同规则见[本批交接规则快照](../handoff-rules-2026-09-08.md)；新版明确规则优先于 payload 中历史措辞。
