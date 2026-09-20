# 限定发布记录

用户在独立诊断完成后明确批准合入 main。范围仅为作者准确 94b5fe79d87e038e895878fb31030cded469bb33 的本批 286 个新增文件及 docs/reviews/eight-94b5fe7 的 B 复核记录；不包含待审 H3 接口任务分支。

B 证据提交 491a3277d1967d8a22f3b64c0b62bc2f05a3f727；作者包相对审核版本无改动。提交后以全新包外 publication-regression-run01 运行原 verify_delivery.py，结果 PASS_PUBLICATION_FORMAT_ONLY 72 8，未重复未受影响的硬件/耐久测试。

本机检查：共享 F:/NUEC/develop 保持原 task/member-b-four-track-01，普通状态及本批范围的未跟踪/忽略状态为空；B 独立工作树无未说明的忽略材料，两份辅助脚本失败/成功日志已显式入库。本批数据和诊断证据均纳入提交，网络获取脚本及回归输出保留在 F:/NUEC/review-evidence/eight-94b5fe7。不改共享任务分支或 A 实际工程。

发布前直接 API 核对 main=a17c4acd7a61d8bc2b5b2e1944f8c40fa4cc9ebd，作者分支=94b5fe79d87e038e895878fb31030cded469bb33。最终远端更新及本地主线对齐需在推送后读取确认，以本轮最终回报和包外 closeout-result.json 为准，本文不预签推送成功。

此前自动审批拒绝直接 main 推送，现已获得用户明确批准；Git HTTPS 仍出现连接重置，允许改用官方 Git 数据 API，非强制更新并核对完整树及准确提交，不覆盖并发 main。失败记录保留。

未删除作者分支、待审 H3 分支、A 原始材料或实际工程引用入口；作者分支/副本后续用途需 A 确认，已在 A-PROMPT.md 回传。本机独立检出暂保留用于复现，源代码仍以 Git 提交为准。未代签 A 共享目录或其他成员同步。
