# 454 项本地差异的发布与整理

日期：2026-09-12。起点 main：`29c47fe2ecc3e664c42009344c4731cead6c8c12`。

这 454 项是文件差异，不是提交次数。原先只做保全，未提交成果，本轮改为逐项分流，不能以“待复核”为由无限留在共享 main 的未提交区。

| 原有差异 | 数量 | 本轮去向 |
| --- | ---: | --- |
| 当前文档 | 14 | 主线文档，纠正旧时点状态并保留真实证据边界 |
| 历史与复核记录 | 22 | 主线；旧硬件草案集中归档，历史失败/成功记录均保留 |
| 未复核工程成果 | 141 | 独立待审分支，不接入主线 RTL/BD/XDC |
| 已有相同材料 | 32 | 逐字节验证后使用主线已有位置，不再重复存储 |
| 旧工程恢复/仿真缓存 | 245 | 仓库外已校验备份，不冒充可发布源码 |
| 合计 | 454 | 逐项路径、原 SHA-256 和处理类别见 JSON 清单 |

额外从忽略项中补交 48 份诊断原始数据、失败/成功日志及合成测试输入到待审分支；忽略文件总清单和原件保留在本机恢复档案。新清单、说明和验证结果不计入原 454 项。

## 继续工作与复核

- 四路工程待审分支：`codex/toph/four-channel-engineering-review-20260912`。
- [待审工程目录](https://github.com/TophBeifong1744/Competition_fpga/tree/codex/toph/four-channel-engineering-review-20260912/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01)，进入 `DELIVERY-20260912.md` 阅读范围和复核步骤。以远端准确提交为复核对象，不用移动中的分支名替代固定 SHA。
- 现有 F 盘 one 工程保持不动。其 XPR 的当前源码引用为自身 `one.srcs` 的导入副本，不依赖被整理的共享任务源码。
- 已接收的[四路杜邦线诊断包](../../task-packages/PKG-A-ACQ/deliveries/dupont-diagnostic-20260911/README.md)及 [B 回执](../../task-packages/PKG-A-ACQ/deliveries/dupont-diagnostic-20260911/B-REVIEW.md)仍是主线 H2 依据，不重复派发。本批工程源码提交不是新技术批准；C 板实物、正式 M1 和完整 H3 仍单独验证。
- 只保留一个待审工程工作副本；共享 main 继续作为干净的主线入口。复核通过后按 `team-workflow.md` 合入、验证、删除这个短期分支及工作副本；未通过时保留，不提前删除。

## 去重后的有效位置

- FFT25 研究参考：`task-packages/PKG-A-H3-INTEGRATION/references/fft/`，对应旧 `PKG-A-ACQ/tasks/fft-ip-budget-01/` 的 22 个文件。
- RTL/BD 语言约定：`task-packages/PKG-A-H3-INTEGRATION/references/policy/rtl-language-and-bd-integration.md`，不再复制成 docs 下第二份。
- B 限定收口 9 份分析输出：`task-packages/PKG-B-ALG/tasks/phat-fixed-03/closeout-01/evidence/run01/`；原复核日志仍保留当时路径。
- [旧硬件草案](../../archive/2026-09-12-local-materials/README.md)只作历史，不恢复旧单 CLOCK 方案。
- `docs/reviews/2026-09-11-b-real-input-register-344f8434-access-review.md` 是当时访问失败记录，后续 PR10 已解决，不是当前阻塞。

## 可恢复性与检查边界

本机 `sync-main-2026-09-12/backup/` 保存 `local-before-update.zip`、`ignored-local-recovery.zip`、原路径清单与哈希；本轮另存 `closeout-local-20260912/current-documents.zip`，保存 14 份合并前本地文档。档案内容按 ZIP 内 `files/<原相对路径>` 恢复到单独目录，不覆盖当前 main 或 one。

档案 SHA-256、每个原文件去向见[机器可读清单](local-materials-2026-09-12.json)。旧恢复工程含厂商生成文件，不整包公开。`audit_c_build.py` 等历史现场工具需要原恢复目录、one 与 BSP，未将归档删除解释为现场审计可独立复现；恢复步骤在待审包说明中。

本轮只做保全、去重、文档和发布测试，不重跑综合实现、不上板、不改 H1/H2/H3 或 A/B/C 分工、不倒填 9 月 10 日快照。最终提交号以 Git 提交记录和发布回执为准；最终恢复路径及共享工作区检查写入本机处理报告。
