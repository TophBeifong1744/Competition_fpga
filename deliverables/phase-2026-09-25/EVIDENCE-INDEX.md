# 2026-09-25 检查点证据索引

核查日：2026-09-30。以下是原来源及固定候选索引，动态状态以原 Issue/PR 为准。
成员事件按其提交和范围引用；旧 review 不自动批准后续 HEAD。时间统一保留 GitHub 原 UTC，另标与计划检查时刻的关系。

## 固定候选与发布

| PR | 核查状态 | 候选 SHA | 合入 SHA / UTC 时间 |
| --- | --- | --- | --- |
| [#28](https://github.com/TophBeifong1744/Competition_fpga/pull/28) | OPEN | `a91000c5e99ceb279a7178885f8fdbd7ffe0da08` | `未合入` / 无 |
| [#29](https://github.com/TophBeifong1744/Competition_fpga/pull/29) | MERGED | `e4bd1dd3a317a9cae2bc6834c70f80dd678c4c8b` | `28d58e908525d1de1c018eeb99fd607a07b6047c` / 2026-09-24T07:05:41Z |
| [#30](https://github.com/TophBeifong1744/Competition_fpga/pull/30) | MERGED | `73ef510e4eb35301695ab8313c84221e70ff1a59` | `a1cbaa48a2c09719f14998b98a8000cc343d1adf` / 2026-09-28T02:55:07Z |
| [#33](https://github.com/TophBeifong1744/Competition_fpga/pull/33) | OPEN | `a14cd0766d923f00428c42ff7dc5d2eb52db0e50` | `未合入` / 无 |
| [#36](https://github.com/TophBeifong1744/Competition_fpga/pull/36) | OPEN | `6a8b58ddc417976f6e79700c1c883eee9fe5f3ed` | `未合入` / 无 |

## 成员与发布原事件

- PR#29：BryanZheng802，2026-09-24T05:11:46Z，检查时刻前事件，`e4bd1dd3a317a9cae2bc6834c70f80dd678c4c8b`。B 限定复核：固定 e4bd1dd3a317a9cae2bc6834c70f80dd678c4c8b。批准 #13 的 S1 只读组合加载预检增量，范围仅为已归档工件及既有 A 机路径的加载前检查器。（全文及完整限制见原 PR review。）
- PR#30：BryanZheng802，2026-09-24T05:12:15Z，检查时刻前事件，`c4a2a173eb48383a30d3bfc3138e0ee14a25b4d4`。B 限定复核：固定 c4a2a173eb48383a30d3bfc3138e0ee14a25b4d4。批准 #14 的联合确认准备稿和 #18 的 16 服务测量入口作为下一阶段输入；不冻结生产 profile，也不代表实际链实现或实时通过。（全文及完整限制见原 PR review。）
- PR#30：BryanZheng802，2026-09-28T02:20:54Z，检查后事件，`73ef510e4eb35301695ab8313c84221e70ff1a59`。本人 B / BryanZheng802 限定批准候选 73ef510e4eb35301695ab8313c84221e70ff1a59 的单时钟 fixed4 叶模块及同边沿取消／协议错逻辑 gate 的有限 FUNCTIONAL_SIM，用于后续有界集成开发。（全文及完整限制见原 PR review。）
- PR#33：TophBeifong1744，2026-09-24T14:15:36Z，检查时刻前事件，`a14cd0766d923f00428c42ff7dc5d2eb52db0e50`。A（TophBeifong1744）真实成员限定确认：用户拓芙已在主流程明确回复“确认”，授权M将以下决定记录到原PR。本事件由Codex代录用户决定，不是AI自主代签。（全文及完整限制见原 PR review。）

- [2026-09-24 PR 29 限定合入与共享 main 收尾](https://github.com/TophBeifong1744/Competition_fpga/issues/13#issuecomment-5809493448)：TophBeifong1744，2026-09-24T07:09:31Z，检查时刻前事件。
- [PR 30 已按用户明确授权合并，发布收尾完成。](https://github.com/TophBeifong1744/Competition_fpga/issues/14#issuecomment-5862477721)：TophBeifong1744，2026-09-28T02:59:20Z，检查后事件。
- [B-MAIN 接收 B-CHECK 两环境独立新进程 S1/BIN-UART 核验：限定结论 PASS_RAW_UART_ONLY。固定候选 a91000c5e99ceb279a7178885f8fdbd7ffe0da08，快照清单 SHA256 650205fc570fffba844439610524faf0a166d58d2e0dbc1a9fbddf713eb51ba2；入口 verify_zip.py SHA256 2d1b14cc15bc28b8247af0e84b3b545553366240e24c5cfb67e37fec0be2baf7。](https://github.com/TophBeifong1744/Competition_fpga/issues/15#issuecomment-5811228511)：BryanZheng802，2026-09-24T09:08:54Z，检查时刻前事件。
- [M / A机收件回执（2026-09-25；由用户转交B原包）：**RECEIVED / EVIDENCE_ACCESSIBLE**。这是收件及身份核对，不是性能验收、生产冻结或成员APPROVED。](https://github.com/TophBeifong1744/Competition_fpga/issues/16#issuecomment-5824784952)：TophBeifong1744，2026-09-25T00:50:15Z，检查时刻前事件。
- [17｜B本人确认P1～P4政策意见](https://github.com/TophBeifong1744/Competition_fpga/issues/17#issuecomment-5885737091)：BryanZheng802，2026-09-29T07:31:34Z，检查后事件。
- [A 对四项政策的本人决定与现有证据答复](https://github.com/TophBeifong1744/Competition_fpga/issues/17#issuecomment-5889312362)：TophBeifong1744，2026-09-29T11:27:08Z，检查后事件。
- [A本人限定接收PR36补述与诊断资料；保留历史加载缺口](https://github.com/TophBeifong1744/Competition_fpga/pull/36#issuecomment-5893666405)：TophBeifong1744，2026-09-29T15:48:01Z，检查后事件。

## 原任务与事实快照

| 原 Issue | owner | 收尾前 Milestone | 状态 |
| --- | --- | --- | --- |
| [#13](https://github.com/TophBeifong1744/Competition_fpga/issues/13) | TophBeifong1744 | 2026-09-25 接口与可信输入检查 | OPEN |
| [#14](https://github.com/TophBeifong1744/Competition_fpga/issues/14) | TophBeifong1744 | 2026-09-25 接口与可信输入检查 | OPEN |
| [#15](https://github.com/TophBeifong1744/Competition_fpga/issues/15) | hsc119 | 2026-09-25 接口与可信输入检查 | OPEN |
| [#16](https://github.com/TophBeifong1744/Competition_fpga/issues/16) | BryanZheng802 | 2026-09-25 接口与可信输入检查 | OPEN |
| [#17](https://github.com/TophBeifong1744/Competition_fpga/issues/17) | BryanZheng802 | 2026-09-29 M1与H3模块准入检查 | OPEN |

## 本机原始核查记录

API 原始响应保存在 A 机 `codex_out/september-checkpoint-closeout-20260930/remote/`；本地缓存不是对其他成员的下载承诺，上面的 GitHub 原事件和固定 Git 对象是跨机入口。

| 文件 | 原字节 SHA256 |
| --- | --- |
| `issue-13.json` | `b45e7894da2b159f1155fa0e3adbd5db84721cf1a47299adef7b9ea0c9c1d9cb` |
| `issue-14.json` | `00bc90d4e0c4cd956f3860683c5fa6e044c557c17993a724baa6896065be1e11` |
| `issue-15.json` | `fde1b68e4acf7a2b598387bc0307fe1accebe6c330e69cb6544a0cbb2c74bec0` |
| `issue-16.json` | `05e535b21939af587d9e2e9fa52045409c3081bc1b9c89cb80c42ac957da9548` |
| `issue-17.json` | `0d1e32de1be1250b3335b72e1372cc33417a382f807b535fc3a6570bcf10d3b2` |
| `pr-28.json` | `87431722bfa17fe71c4eac0b0cec340041d7f9c87fef47ce148a3ed729e1370b` |
| `pr-29.json` | `c4c60538484ce07bcf23c50408623715f6dd4da7a079c36a919faf15a58901d1` |
| `pr-30.json` | `d96d602d8cfb13f0867f073332151cc0da187595de7fd6f7b3ea7bab083d3c4f` |
| `pr-33.json` | `b5277a758973ecf2c2c04c8c5c4ca425d910bcc8af2b629941ead8bfce4dfb18` |
| `pr-36.json` | `89f11b17fde55101fc43839910ff40881df0572730571f4bad482676041cbeca` |

## 本批验证与回退

本批仅 Git/API/Markdown/身份核查；工程、算法、RTL、EDA和板测 NOT_RUN。已有技术证据按原适用范围复用。本批仅新增两个日期目录各一份 CLOSEOUT 和本索引；原产品、旧快照和失败记录不变。
机械命令、原材料保护清单、发布前后版本与 GitHub 变更回读保存于上述本机输出根。若记录错误，新增更正且保留旧版本；不回退任何产品候选，不使用 reset/clean。
