# 连续原型复核批次收尾

2026-09-15，B 本机实际共享项目为 `F:/NUEC/develop`。限定复核通过；合并提交 `f4fc899462a715bd878ee05d6bbb935b10b47651`，父提交分别为最新主线 `e5621cae92108f480a831b4da679f40fe64631c8` 和准确作者提交 `88805ee415f137998b59b7cb197f2eeb988d17b7`。恢复连接后已推送至 `8371f014711e04553749e6c2ffc29f34b9d5ccc9`，直接远端核对成功，并完成本次 B 副本去重。本文件及清理回执的最终文档提交随后非强制推送，最终 main SHA 见交回用户的结果及包外 `F:/NUEC/review-evidence/continuous-final-main.json`，避免自引用 SHA。

| 项目 | 实际状态 |
| --- | --- |
| 批准范围 | 作者 `continuous-prototype-01/` 全部 222 文件；包外 `docs/reviews/continuous-88805ee/` 的 B 记录、工具与软件复跑证据。没有范围外暂存文件 |
| 集成验证 | 合并后包清单、逐 Git blob 字节、19 ZIP CRC、实际 ELF 适配检查、来源校验、10+34 单测及 16 主机场景通过；暂存的 279 个原件/复核文件逐字节核对通过 |
| 入口 | 原型仍在任务包；修复版入口为 publication/README.md 指向的 board-run-20260915-02。没有替换实际 one、活动 RTL、算法或旧构建器 |
| 本地 main | 实际共享目录的 main 已推送到 8371f014711e04553749e6c2ffc29f34b9d5ccc9，包含作者原件、B 复核和首次收尾记录 |
| 跟踪/直接远端 | 发布后本地 main、origin/main、直接 ls-remote 三者同为 8371f014711e04553749e6c2ffc29f34b9d5ccc9，领先/落后 0/0；作者远端仍为 88805ee415f137998b59b7cb197f2eeb988d17b7。原型目录 Git tree 与批准 SHA 完全相同 |
| 推送结果 | 前次连接重置和 HTTP/1.1 连接失败保留为历史；用户要求继续后网络恢复，普通 HTTPS 非强制 push 成功。没有自动批准拒绝、分支保护或强推 |
| 共享材料 | 收尾前实际共享目录已修改/暂存/未跟踪/忽略项均为 0；详见 closeout-pre.json。当前追加的本报告和快照会随收尾文档提交，不把它们算成遗漏 |
| 本批有用材料 | 57 份 B 原始复核文件已经合入 f4fc899；host 日志、exe、SHA 和失败脚本均显式入库，未被通用忽略规则丢掉。closeout-pre.json 和首次收尾记录随 8371f01 发布；本批未说明的遗漏为 0。最终仅追加本表更新及 cleanup-receipt.json |
| 本地依赖 | Capstone 5.0.6 保留在 F:/NUEC/review-tools/continuous-capstone-5；本机原生 GCC 与 Python 不在本批清理范围。依赖可按 B-REVIEW.md 重装，不提交第三方运行时 |
| 审核工作树/重复证据 | 已删除本次 B 的 F:/NUEC/review-worktrees/continuous-88805ee 及 F:/NUEC/review-evidence/continuous-88805ee。前者完整 status（含忽略项）为 0，审核提交已包含于远端 main；后者 58 文件逐 SHA/Git blob 核对与已发布材料相同后删除。精确路径、恢复提交及逐文件哈希见 cleanup-receipt.json |
| 作者分支 | codex/toph/continuous-prototype-20260915 保留；虽然此次准确提交全范围通过，但未获知 A 是否继续在该分支准备后续采集，不代确认整条任务结束 |
| A 本机 | F:/College 下实际 one、Vitis、发布副本及历史构建目录不可访问，不代删、不代签同步。由 A 工作执行核对其实际 main/跟踪/远端、未提交/未跟踪/忽略材料和后续分支用途后回传 |
| 最终状态 | **B 本机限定发布、材料核对与安全去重完成；最终收尾文档继续推送并再次核对。** A 本机状态与后续分支用途由 A 本人核对，不代签全员同步 |

本次逐工作树只读检查的其他任务状态见 closeout-pre.json：a-h3 有 8 个未跟踪项，a-mono 有 5 个未跟踪项，member-b-real-audio-compare-01 有 1 条跟踪差异与 1 个未跟踪项，pr3-main-20260909 有 231 条跟踪差异；其余列出的工作树在普通 status 中没有差异。本批路径在全部所列工作树的 status（含忽略项）均为 0。没有删除、暂存或重置上述其他成员工作；普通 status 不等于已全面核对其他任务忽略的构建材料。

前一整理流程留下的 F:/NUEC/local-archive/develop-before-main-20260915 和其他既有归档/分支原样保留，不在本次复核中重新签署其材料清理完成。

恢复方法：原型原字节可从准确 88805ee 提交创建全新 detached 工作树；B 初始证据可从 8371f01 的本目录恢复。历史命令中的 EVIDENCE 是原执行位置，今后复跑将 EVIDENCE 改为 `F:/NUEC/develop/docs/reviews/continuous-88805ee`，输出另取包外不存在的新目录；不修改归档命令日志中的历史路径。无需重新加载作者旧固件。若远端出现合法新提交，先安全同步并按变化回归，不强推。
