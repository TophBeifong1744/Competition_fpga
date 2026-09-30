# 2026-09-29 检查点证据索引

核查日：2026-09-30。以下是原来源及固定候选索引，动态状态以原 Issue/PR 为准。
成员事件按其提交和范围引用；旧 review 不自动批准后续 HEAD。时间统一保留 GitHub 原 UTC，另标与计划检查时刻的关系。

## 固定候选与发布

| PR | 核查状态 | 候选 SHA | 合入 SHA / UTC 时间 |
| --- | --- | --- | --- |
| [#30](https://github.com/TophBeifong1744/Competition_fpga/pull/30) | MERGED | `73ef510e4eb35301695ab8313c84221e70ff1a59` | `a1cbaa48a2c09719f14998b98a8000cc343d1adf` / 2026-09-28T02:55:07Z |
| [#31](https://github.com/TophBeifong1744/Competition_fpga/pull/31) | OPEN | `97a04e9cb859a915a31d8a2b3cdaaaa09009019b` | `未合入` / 无 |
| [#32](https://github.com/TophBeifong1744/Competition_fpga/pull/32) | OPEN | `beceee335d5c6d0ce96a2150f4a2ad107854e3a9` | `未合入` / 无 |
| [#34](https://github.com/TophBeifong1744/Competition_fpga/pull/34) | MERGED | `cabe1a0cdb263fce012f99f5d32675f194dfe8d8` | `87fdb3d0029c6a18a78408b20d93efcbfcb01923` / 2026-09-29T04:56:32Z |
| [#35](https://github.com/TophBeifong1744/Competition_fpga/pull/35) | MERGED | `eb50145225e703aa060328e7a2113deaca353ddf` | `3bf64351728dbe4bdba4e2b7836a5d96c613e444` / 2026-09-29T00:14:44Z |
| [#38](https://github.com/TophBeifong1744/Competition_fpga/pull/38) | OPEN | `48c494e73996b734d887d1def08b30d485bbe23e` | `未合入` / 无 |

## 成员与发布原事件

- PR#30：BryanZheng802，2026-09-24T05:12:15Z，检查时刻前事件，`c4a2a173eb48383a30d3bfc3138e0ee14a25b4d4`。B 限定复核：固定 c4a2a173eb48383a30d3bfc3138e0ee14a25b4d4。批准 #14 的联合确认准备稿和 #18 的 16 服务测量入口作为下一阶段输入；不冻结生产 profile，也不代表实际链实现或实时通过。（全文及完整限制见原 PR review。）
- PR#30：BryanZheng802，2026-09-28T02:20:54Z，检查时刻前事件，`73ef510e4eb35301695ab8313c84221e70ff1a59`。本人 B / BryanZheng802 限定批准候选 73ef510e4eb35301695ab8313c84221e70ff1a59 的单时钟 fixed4 叶模块及同边沿取消／协议错逻辑 gate 的有限 FUNCTIONAL_SIM，用于后续有界集成开发。（全文及完整限制见原 PR review。）
- PR#31：BryanZheng802，2026-09-24T05:12:36Z，检查时刻前事件，`97a04e9cb859a915a31d8a2b3cdaaaa09009019b`。B 限定复核：固定 97a04e9cb859a915a31d8a2b3cdaaaa09009019b。批准 #21 的 SKL-001 自含导出包及其身份清单，范围仅为本次发布包装；不签完整 Skill 任务或陌生模块复用能力。（全文及完整限制见原 PR review。）
- PR#32：hsc119，2026-09-27T16:08:30Z，检查时刻前事件，`6a1efb1fa945ec17a38baa128ca93fb829503085`。C（hsc119）授权按已公布的增量技术复核结论，对提交 6a1efb1fa945ec17a38baa128ca93fb829503085 的 C22-01、C22-02 修复给予限定批准，两个原问题在此准确版本下记为 VERIFIED_CLOSED。依据见本 PR 的 C 增量复核记录：https://github.com/TophBeifong1744/Competition_fpga/pull/32#issuecomment-5831378875 。（全文及完整限制见原 PR review。）
- PR#34：TophBeifong1744，2026-09-29T04:56:06Z，检查时刻前事件，`cabe1a0cdb263fce012f99f5d32675f194dfe8d8`。真实非作者 A / TophBeifong1744 在 M 对准确候选与限定批准/转ready/组合核验后合并授权文本回复“批准”。本 review 由 Codex 依该明确指令代执行，记录成员决定，不把原 R 的 AI 结论冒充批准。（全文及完整限制见原 PR review。）
- PR#35：TophBeifong1744，2026-09-29T00:14:31Z，检查时刻前事件，`eb50145225e703aa060328e7a2113deaca353ddf`。A / TophBeifong1744 在 M 主流程对明确的批准及合并授权文本回复“我批准”；本 review 由 Codex 按拓芙这次明确指令代执行，记录真实非作者成员决定，不把 R 的 AI 结论当作成员批准。（全文及完整限制见原 PR review。）

- [M 接收：17 既有时基与消费者事实补充](https://github.com/TophBeifong1744/Competition_fpga/issues/17#issuecomment-5890135595)：TophBeifong1744，2026-09-29T12:17:23Z，检查后事件。
- [17｜A 本人同意三项目标选择政策](https://github.com/TophBeifong1744/Competition_fpga/issues/17#issuecomment-5890337643)：TophBeifong1744，2026-09-29T12:30:08Z，检查后事件。
- [18 B 本人对固定固件 × LINK 组合的限定接受](https://github.com/TophBeifong1744/Competition_fpga/issues/18#issuecomment-5890993248)：BryanZheng802，2026-09-29T13:11:16Z，检查后事件。
- [B 本人成员决定｜C1 平台限定接受](https://github.com/TophBeifong1744/Competition_fpga/issues/18#issuecomment-5892159585)：BryanZheng802，2026-09-29T14:19:22Z，检查后事件。
- [M 接收用户真实 M1 工程操作结果（2026-09-30）](https://github.com/TophBeifong1744/Competition_fpga/issues/18#issuecomment-5904911365)：TophBeifong1744，2026-09-30T05:44:06Z，检查后事件。
- [**A 已明确批准限定范围，PR 35 已合并；不是整个 19 或独立 BOARD 验收。**](https://github.com/TophBeifong1744/Competition_fpga/issues/19#issuecomment-5881177159)：TophBeifong1744，2026-09-29T00:17:01Z，检查时刻前事件。
- [**I22-B-META-01：FIXED_PENDING_REVIEW**](https://github.com/TophBeifong1744/Competition_fpga/pull/32#issuecomment-5904627579)：TophBeifong1744，2026-09-30T05:19:46Z，检查后事件。
- [A/M已收到完整复核包；保留既有非作者复核安排](https://github.com/TophBeifong1744/Competition_fpga/pull/38#issuecomment-5902326341)：TophBeifong1744，2026-09-30T01:34:51Z，检查后事件。

## 原任务与事实快照

| 原 Issue | owner | 收尾前 Milestone | 状态 |
| --- | --- | --- | --- |
| [#17](https://github.com/TophBeifong1744/Competition_fpga/issues/17) | BryanZheng802 | 2026-09-29 M1与H3模块准入检查 | OPEN |
| [#18](https://github.com/TophBeifong1744/Competition_fpga/issues/18) | TophBeifong1744 | 2026-09-29 M1与H3模块准入检查 | OPEN |
| [#19](https://github.com/TophBeifong1744/Competition_fpga/issues/19) | hsc119 | 2026-09-29 M1与H3模块准入检查 | OPEN |
| [#21](https://github.com/TophBeifong1744/Competition_fpga/issues/21) | TophBeifong1744 | 2026-09-29 M1与H3模块准入检查 | OPEN |
| [#22](https://github.com/TophBeifong1744/Competition_fpga/issues/22) | TophBeifong1744 | 2026-10-03 集成与独立复用预验收 | OPEN |

## 本机原始核查记录

API 原始响应保存在 A 机 `codex_out/september-checkpoint-closeout-20260930/remote/`；本地缓存不是对其他成员的下载承诺，上面的 GitHub 原事件和固定 Git 对象是跨机入口。

| 文件 | 原字节 SHA256 |
| --- | --- |
| `issue-17.json` | `0d1e32de1be1250b3335b72e1372cc33417a382f807b535fc3a6570bcf10d3b2` |
| `issue-18.json` | `e2f1d30e71efacc2cb29b9e2c50f0106e0687bb981a0f7623608e249412d0495` |
| `issue-19.json` | `7ce04d2505a3a1a312fcccec6231ec3212870b1988f980cab4157fc621f540a8` |
| `issue-21.json` | `2b68c2b4880e915ec11a3c76e27f8330f173d578f252dbe9a363838e5cb529bc` |
| `issue-22.json` | `01ce149e7bf74991989135c01e862ba3f80b6b9ccaebaabdec22d535ca3c7133` |
| `pr-30.json` | `d96d602d8cfb13f0867f073332151cc0da187595de7fd6f7b3ea7bab083d3c4f` |
| `pr-31.json` | `cf9365643216fe2db4c97e6bf0d4ea65bd56ac62ab422306b0b938a9c6f45081` |
| `pr-32.json` | `4b5c921b2ba485852526ed74deda2ac5d665f19fab44dda24a39c2aa15cd1b29` |
| `pr-34.json` | `d821ce416cf9da08d965852b59eaff951afa874499f7288c29b181adc3ebe80e` |
| `pr-35.json` | `e7eb72994a8a685a99a115fe2bf00b619c2b647061d8a3a02c559e1d93e4ce64` |
| `pr-38.json` | `8906124bf5d9dd2284a59dda15a24f57eaa319e7eb3e8e090973f5aef2a71909` |

#18 的 9/30 实际构建补进展原件：A机 `codex_out/i18-user-build-receipt-20260930/REVIEW-ENTRY.md`、`SOURCE-INDEX.json`（`732e34e176e8294030f8d8695c28778e2df28b1da0df984c6bc3f54dbc60bd4b`）、`AUTOLOG-INDEX.json`。完整 IDE 日志快照 `ide_verbose.log` SHA256 `e45fc3c5f166fcc0dd2b185ca553cde14a5419816b36a5abec2ffb72eeb123d9`。这些是本机已核原件，不签 BOARD，不冒称已发给 B/C。

## 本批验证与回退

本批仅 Git/API/Markdown/身份核查；工程、算法、RTL、EDA和板测 NOT_RUN。已有技术证据按原适用范围复用。本批仅新增两个日期目录各一份 CLOSEOUT 和本索引；原产品、旧快照和失败记录不变。
机械命令、原材料保护清单、发布前后版本与 GitHub 变更回读保存于上述本机输出根。若记录错误，新增更正且保留旧版本；不回退任何产品候选，不使用 reset/clean。
