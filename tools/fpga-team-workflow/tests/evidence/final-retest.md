# F-FTW-001 最终定点复测

结论：安装收据核对缺口已在本次准确快照中修复，`F-FTW-001` 状态为 **VERIFIED_CLOSED_FOR_TESTED_SNAPSHOT**。新版成功受控安装；4 种收据损坏均被拒绝；回退保留后续改动，解除自己设置的测试改动后，逐字节恢复初始安装。

## 已测版本与实际结果

- 原包来源：`<workspace>\outputs\fpga-team-workflow`，只读。
- 冻结副本：`source-final-2/`，VERSION `0.1.0`。
- 实测 content SHA-256：`1e0b3f29cc0661bd30260898bc78477aa0592f921afecdf2706d046d8798e6fc`。
- 实测 full tree SHA-256：`2f0a854a12267f664bbc87a4a8cbac68af7f98abfaa3d97082ecfedd2c3b3741`。
- 12 次独立真实 CLI 调用，准确命令、工作目录、退出码与返回保存在 `forward-logs/final-2/`；执行脚本 `final_retest.py`；结果 `final-retest.json`。

| 定点检查 | 结果 |
|---|---|
| 新源包 verify 与期望摘要一致 | OK |
| 新包 install-plan → install → installed verify | OK；安装内容与冻结源包逐文件一致 |
| installed_files 置空 | exit 2 / BLOCKED |
| 收据版本改为 999.0.0 | exit 2 / BLOCKED |
| 收据 schema 改为 999 | exit 2 / BLOCKED |
| 删除 transaction_id | exit 2 / BLOCKED |
| 恢复收据原字节后 verify | OK |
| 安装后增加自定义 README 内容再请求回退 | exit 2 / BLOCKED；自定义内容哈希不变 |
| 恢复该测试编辑后 dry-run → rollback | OK；所有文件及收据与升级前初始安装精确一致 |

事务路径：`skills/.fpga-team-workflow-transactions/1430510d6fcd47b791fabd49730984ca`，最终 `ROLLED_BACK`。退役安装和所有旧事务保留。当前沙盒活动安装因此恢复到初始旧快照；修复快照的副本、验证记录和退役安装均仍存在，不能把已回退状态称为当前运行已升级。

## 第一次最终取样的封装冲突

第一次复制 `source-final/` 时，作者正在修改交付文档，得到的文件和 manifest 不一致。verify 正确返回 BLOCKED，未安装。差异仅为 COMPATIBILITY.md、references/cli.md、assets/workflow-lock.example.yaml。作者确认这是封装期间并发修改，并冻结源码后重新 seal。

该拒绝记录保留在 `forward-logs/final/01-final-source-verify.json`，首次副本原样保留。随后使用新的 `source-final-2/` 和 `forward-logs/final-2/` 完成上述复测；没有覆盖失败历史，没有把未封装快照的失败算成收据修复失败。

## 复测边界

本次只重测原独立发现的收据缺口及相关安装/回退保护，没有重复全部回归。95 项回归通过为作者提供的结果，本代理没有把它声明成自己运行；本代理实际完整运行过初始快照的 86 项回归。

原始独立报告 `report.md`、21 次独立探针、旧缺陷证据和实际 `fpga_architect` 的 ANALYZE/PREFLIGHT 记录 `architect-call.md` 均保留。没有重复与本次修复无关的工程角色检查。

所有写入仍位于 `work/independent-forward`；未修改源包、全局配置/安装、上游角色、工程原始两文件、远端或硬件；无 EDA 项目运行。客户端自动发现/刷新、实际模型/effort、原生工程工具和真实 GitHub 事件仍 UNKNOWN/NOT_RUN。本复测是 AI 独立测试结果，不是真实人类成员批准或 FPGA 验收。
