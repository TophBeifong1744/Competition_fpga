# C 旧任务复核与发布入口（2026-09-18）

## 身份、版本及授权

- 作者 A / 拓芙；复核归属 C / hsc119；实际执行 Codex。用户本轮明确要求“帮我复核……根据规则……合并到 main”，据此代执行限定文档/证据复核及发布；不冒称人工逐项签字或硬件阶段门通过。
- 精确远端候选 `codex/toph/pending-review-packages-20260908`：`1731522f80ed0b970c63c8a3b019b9ba281d6ca8`。
- 开始时本地 main、origin/main、直接查询远端 main：`5cfa02e51af44bb5c930babf732ddc864a1ab6cd`，工作区干净。
- 采用 2026-09-17 增量复核规则。5 包 payload/引用快照共 80 项逐一核对候选与 main Git 对象，字节相同且哈希通过；只有 3D-P2 的旧 REVIEW 增加过未绑定 SHA 的签字。历史版本记录保持原状。
- 只评审上述 5 个 A 作者任务，不评审 C 自己的舵机/转台，也不包含分支上其他工作。

## 逐项结论

| 包 | 本轮结果 | 主线处理 |
| --- | --- | --- |
| WP-A0 | NEEDS_FIX：原 25 项清单有 1 项不符；payload 宣称全部一致且状态/日期已旧 | 保留证据，发布退回记录；不覆盖当前计划/台账 |
| WP-S1 | SUPERSEDED：现行规则已明确退役，不批准重新启用 | 保留快照，指向现行 skill/README.md |
| 3D-P2 | PASS，仅历史工程参考的边界、符号、预算与验证说明 | 发布限定复核记录，保留现行 docs/three-dimensional-doa-engineering-guide.md，不覆盖其更新 |
| 3D-P4 | NEEDS_FIX，旧活动依赖已退役，旧版不适合作为现行操作指南 | 保留现行改进，不用旧包回退覆盖；问题交 A |
| REL6-001 | PASS，仅冻结材料及历史复跑产物完整性、失败边界声明 | 沿用 deliverables/six-mic-acoustic-review-v1；修复本机 checkout 换行，Git 内容不变 |

“通过”不包括科学算法正确性、三维实施、RTL/时序/资源/实板、真实 PYNQ、采购或竞赛提交。旧候选不是 main 祖先且仅部分范围获准，因此不整条 merge，不删候选分支；限定内容已存在 main，只提交本轮复核/索引/验证记录。

## 发现与依据

**C-01 / WP-A0 阻断**：独立遍历包内原 MANIFEST.json 的 25 项，24 项匹配；`docs/work-packages-2026-09-06.md` 期望 `f0ceb76c937931238a16644c5ba41f6337910951744267431df4faee4d0971b4`，实际 `541e04d6d7bcd43c8bf838b568844eb227f2430812dcb8d8eb1fd6595ed42f5c`。与作者自报吻合，但不能据此关闭异常。旧 payload/current-status.md 末段及 archive/README.md 的全通过表述不能批准。A 需明确异常来源与可信版本/勘误，不修改原清单掩盖问题。

**C-02 / WP-S1 退役**：AGENTS.md 与 skill/README.md 明确旧工作流已由 fpga-module-verification 取代，现行两项 Skill 已有 B 的限定批准。旧包强调接口冻结前停止下游的工作流，与新版允许暂定合同离线开发的边界不同；不重跑已退役行为测试，不将退役写成 PASS。

**C-03 / 3D-P2 限定通过**：检查 pair 数与独立到达时间的区别、TDOA/方向/因果延迟符号一致性、固定权重与动态掩码的区别、2D 俯仰无效、六路格式拒绝、预算及分层验证。独立重算六麦 15 pair、21 次变换、6.912 Mbit/s、1.152 MB/s、一小时 4.1472 GB、全掩码系数 4.42368 MB，均与文档一致。文档明确 E3D-01 等未关闭，不把预算当实现证据。旧 10/7 日期及职责不批准；采用现行 10/1 日历和 9/17 C 操作单。9/8 签字无法追溯准确版本，本轮不猜测；这是对已绑定 SHA 的新限定复核。完整预算、固定点、RTL、声学及板测均未测。

**C-04 / 3D-P4 阻断活动接入**：旧包第 1 节仍将已删除的 `skill/soundsight-engineering-workflow` 当活动依赖，并保留 10/7；第 5.2 节未揭示 25 项备份异常。main 版已经修过依赖和日期，但还保留旧 C 职责及将新 Skill 写作待审的描述（现行 skill/README.md 已是 B PASS）。需要 A 按当前规则更新候选并只复核这些差异；不要求重做六麦模拟。未改作者指南后自行批准。

**C-05 / REL6-001 通过范围与本机故障**：包内原校验器实际通过 24 个包文件、15 个结果及源码/config 对应；历史独立复跑快照的 15 项也匹配（这只是复核旧产物，本轮未重新生成 2700 帧）。方向 CSV 的 141/300=47%、78/300=26%、有效输出错误率 66.67% 与报告吻合，静态 C 限制保留。独立修改临时副本 REPORT.md 一个附加段，校验器按预期非零退出并指出该文件，随后恢复临时原件。

原引用路径 38 项漂移分类：34 项只有 CRLF/LF 差异，4 项为历史复跑目录缺失 WAV；四份 WAV 在包内快照可用且哈希匹配。工作目录活动材料包首次校验失败 7 个文件；从 main 提取的准确 Git 字节通过原校验器，因此按 Git 原字节恢复本机活动包的 8 个换行漂移文件（包括清单本身），不改哈希、不换证据、不重签。保存修复前失败日志。其他历史归档路径不动，以包内原字节快照核查。

## 实际运行、复用与复现

本次运行：包级 PowerShell 校验、80 项 Git 字节/哈希核对、25 项历史清单独立检查、原材料校验器、旧复跑产物比对、故障注入、文档内容/活动路径差异检查及预算算术。
复用：9/7 VALIDATION.md 和快照中历史 15 产物，仅作为历史复现记录；9/14 B Skill 批准仅用于现行依赖判断，不重新签署其技术结论。
未测：2700 帧模型重跑、Skill 行为、Vivado、RTL、综合、时序及板测。此次范围为文档参考/材料完整性，发现旧依赖阻断后不跑无关工程。

在仓库根目录：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File task-packages/verify-toph-handoffs.ps1
python task-packages/REL6-001/evidence/reference-snapshots/deliverables/six-mic-acoustic-review-v1/verify_package.py --reproduced task-packages/REL6-001/evidence/reference-snapshots/archive/2026-09-07-six-mic-package-verification
python deliverables/six-mic-acoustic-review-v1/verify_package.py
python docs/reviews/c-legacy-20260918/audit.py . C:/Temp/c-legacy-review-fresh
```

最后一条输出目录必须不存在；输出 audit.json、各校验日志和 committed 临时副本。需要 Git、Python 3.9+，本轮 Python 3.13.5，无第三方依赖；审计脚本固定本轮两端 SHA，保留用于历史复现，不作为未来候选的通用批准器。后续由 A 处理 C-01/C-04；已退役包不重新派工。

证据：[audit.json](audit.json)、[审计完整输出](audit-run.log)、[原交付校验](handoffs.log)、[活动包修复前失败](rel6-active.log)、[冻结副本校验](rel6-snapshot.log)。发布后验证与三端核对另见 [PUBLICATION.md](PUBLICATION.md)。

## 2026-09-18 C-01 / C-04 返修复核追加

准确候选 62a252081d52b3aa9d9dc142f7cc2bf298d9c34d 的六份文档更正获限定 PASS，见 [增量复核](INCREMENTAL-REVIEW.md)。本页以上为上轮原结论；历史 24/25 异常仍保留，不扩大其他包批准。
