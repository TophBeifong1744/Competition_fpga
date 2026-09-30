# 2026-09-25 合同与可信输入检查点收尾

记录日期：**2026-09-30（UTC+8）**；计划检查时间为 9/25 20:00。本文件是事后据实收尾，不是当日全通过报告。

**裁决：检查点关闭并携带遗留项，目标部分达成；不作整体技术 PASS。** 用户拓芙在 M 审阅“9/25 有遗留项收尾、9/29 部分完成且不整体通过”的方案后明确授权“全面执行”。本授权用于记录、发布和任务承接，不替代工程成员批准。

权威入口：[Milestone 1](https://github.com/TophBeifong1744/Competition_fpga/milestone/1)、原 Issue #13～#16。未完成工作沿原 Issue 承接到 10/3 下一检查，不新增重复任务。10/6 冻结及 10/7 10:00 总验收不顺延；关闭日期 Milestone 不等于工程完成。

## 截至检查日的事实与缺项

| 判据 | 已有证据及限定结论 | 当日缺项与边界 |
| --- | --- | --- |
| 受控入口 | PR29 的 S1 只读加载预检 `e4bd1dd3a317a9cae2bc6834c70f80dd678c4c8b` 获 B 限定批准，9/24 合入 `28d58e908525d1de1c018eeb99fd607a07b6047c`；最终入口检查为 ARTIFACT_CHECK_PASS_NOT_BOARD。 | 不是 C 每次实际加载批准或完整 M1。 |
| 候选合同、16 服务入口 | PR30 中 `c4a2a173eb48383a30d3bfc3138e0ee14a25b4d4` 的准备合同/测量入口于 9/24 获 B 限定接受。 | 生产 profile 未冻结；145 向量是准备，16 项 cycles_per_hop 未知。 |
| 新录音或明确缺项 | 两环境各 8/8 原始 UART/BIN 完整性有限通过；新旧录音分列，错素材原件保留。原计划允许明确列出缺项。 | 顶层仍 PARTIAL_RECEIPT_PENDING_POSITION_AND_PROVENANCE；播放字节、位置误差与逐段加载来源不能由用户配置声明推定完整。 |
| 诊断与证据交付 | PR33 `a14cd0766d923f00428c42ff7dc5d2eb52db0e50` 于 9/24 获 A 有条件开发诊断范围批准；#16 三批诊断包于 9/25 已在 A 机收件核哈希。 | PR33 未合入；内容对应和物理时序仍 UNRESOLVED，收件不是正式声学验收。 |
| 正式评价条件 | 不倒填成 9/25 已冻结。 | P1～P4 的 A/B 本人确认事件到 9/29 才齐；生产时基、消费者及期限仍缺。 |

## 后续补进展（不计作按期达成）

- 9/28：PR30 候选 `73ef510e4eb35301695ab8313c84221e70ff1a59` 按分项真实批准合入 `a1cbaa48a2c09719f14998b98a8000cc343d1adf`，包含 fixed4 叶模块限定 FUNCTIONAL_SIM；不是完整 #14、生产冻结或实时系统通过。
- 9/29：P1～P4 的 A/B 政策意见齐备；政策与实现、生产参数及实测分开。
- 9/29：A 对 PR36 `6a8b58ddc417976f6e79700c1c883eee9fe5f3ed` 的限定接收为“带明确来源缺口的开发诊断资料”。19 Run 逐段历史加载绑定及授权仍 UNKNOWN；PR 开放，不为追溯历史要求新录音。

## 原 Issue 承接

| 原任务 | owner / 非作者 | 保留事项与下一裁决 |
| --- | --- | --- |
| [#13](https://github.com/TophBeifong1744/Competition_fpga/issues/13) | A / B | S1 已发布入口复用；实际使用范围与关闭范围沿原定义裁决，不把旧入口自动用于新 M1，不重派同一修复。 |
| [#14](https://github.com/TophBeifong1744/Competition_fpga/issues/14) | A / B | 生产引用闭包、身份/消费者/终态及 I14-TOKEN-01 等未完成项保留；服务实测归 #18，不靠叶仿真补上。 |
| [#15](https://github.com/TophBeifong1744/Competition_fpga/issues/15) | C / B；A 接工程来源 | 保持 PR36 诊断用途和历史 UNKNOWN，不重复查无的新调查、不升格留出集；后续正式输入绑定冻结评价条件。 |
| [#16](https://github.com/TophBeifong1744/Competition_fpga/issues/16) | B / A | 诊断交付已收，保留 UNRESOLVED；PR28/33 各自未发布范围、正式评价输入准备沿原任务处理，不重跑已接受诊断。 |

四个原 Issue 保持 OPEN 并转到 10/3 检查；原计划归属由本快照与原评论保留，不承诺届时全部通过。后续动态事实只更新原 Issue/PR。

## 版本、入口与发布边界

本次文档发布前 main 三端为 `11053af5ab15b7593d418cfdc4bf615d549d5e66`，只是 9/30 核查的集成参考，不冒充 9/25 全部实测版本。逐项候选、成员事件和证据见 [EVIDENCE-INDEX.md](EVIDENCE-INDEX.md)。

- S1 入口保持在 `task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/background-target-stop-20260917/entry-adaptation-20260924/`。
- PR30 后续已发布的 fixed4 活动源和测试仍为 `project/rtl/algorithm/fixed4/`、`simulation/tb/algorithm/fixed4/`；合同与原件不搬动。
- PR28/33/36 未合入内容仍由准确候选保存；本轮不复制为新活动源、不夹带产品合入。
- 仅核 GitHub 事件、文件/链接和版本索引；旧算法、录音、FFT、仿真、耐久证据按原范围复用，未重跑。无构建、下载、板测或新工程 PASS。

本次只增加收尾文档。共享 fixed4 五文件修改、未跟踪/ignored 和失败材料原位保护，不清理。发布后核 local/origin/直接远端及本批差异，机械记录位于 `codex_out/september-checkpoint-closeout-20260930/`。若撤回治理记录，新增更正并保留旧版本；工程回退沿各原发布记录，不 reset/clean。
