# 9 月 16 日阶段确认材料（9 月 12 日准备）

状态：**待组长确认；不是正式阶段通过记录**。编制日期 2026-09-12，计划检查日 2026-09-16；组长可提前审议，但必须记录真实确认日期和批准范围。

固定资料基线：`add40fd773eccdad80f26624ca899c331d6846c8`。该 main 已包含本阶段四路诊断及登记、A 工程限定复核、FFT29 包、B 定点研究和增量；“已合入”与“独立技术批准”分开。后续 main 有新成果时应另列准确提交，不能静默替换本索引来源。

1. 阅读 [阶段报告](STAGE-REPORT.md)：完成项、实际证据和仍未完成项。
2. 阅读 [组长确认稿](DECISION-DRAFT.md)：可直接填写实际裁定；未填写的字段保持待定。
3. 阅读 [集中归档入口](../../../../deliverables/phase-2026-09-16/README.md)及 CLOSEOUT，核对归档索引。

本次仅整理与文件身份校验，不重新运行算法、Vivado、录音或板测。原 9 月 10 日归档和原始失败记录保持不变。归档索引包含不同批准层级的材料，不是统一“已验收文件清单”。

## 校验与导出

在包含固定来源提交的仓库根目录运行（Python 标准库）：

```powershell
python -B task-packages/PKG-B-ALG/tasks/0916-stage-review/archive_index.py --verify --out F:/NUEC/stage0916-verify-new
```

输出目录必须不存在；该命令从 Git 原始 blob 核对所有索引项、长度、SHA-256、所属分组，并检查 9 月 10 日原快照身份。不会把 Windows 换行转换当作原件，也不把哈希通过当技术验收。

如需在另一目录集中查看选定材料，可使用：

```powershell
python -B task-packages/PKG-B-ALG/tasks/0916-stage-review/archive_index.py --verify --out F:/NUEC/stage0916-export-check --export F:/NUEC/stage0916-reference-export
```

导出目录必须不存在，保留原仓库相对路径与原字节；不是完整工程环境，也不提供一键整机运行。算法/硬件复跑使用固定提交的完整仓库与各任务的工具依赖。默认不导出，避免重复保存大批已入 Git 的波形和工具日志。

组长确认后，由指定复核人/获授权主流程依据准确范围更新正式结论、冻结归档及阶段台账，执行 team-workflow 的合入、验证和本地/远端核对。本任务分支只提交推送待确认材料，不自行宣告阶段通过或合入 main。
