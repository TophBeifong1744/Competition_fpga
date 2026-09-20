# A 本机八段输入收尾（2026-09-20）

结论：**A本机同步和本批材料核对完成，未处理独有材料0项。** 接收B的开发/诊断材料限定PASS，不批准定位精度、SNR收益、完整M1/H3或实时。B未代签本页；本页由A主流程实际执行并记录。

## 版本与范围

- 准确作者审核SHA：`94b5fe79d87e038e895878fb31030cded469bb33`。
- B已发布main：`46aee3d59840ad79cd5094ee471576bbf91f8bc6`，本机确认它是当前HEAD祖先（退出0）。
- 任务包：`task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/trusted-direction-input-20260918/`，共286个文件。
- B报告：[B-REVIEW.md](B-REVIEW.md)。复用B的72项当前哈希、8段BIN/UART/CSV及32WAV逐值核验、10项离线测试；本轮没有重复这些技术测试。

## 本机实际操作与结果

cwd：`E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga`。先fetch，真实本地main从`a17c4acd7a61d8bc2b5b2e1944f8c40fa4cc9ebd`落后至上述远端。

1. 使用已有`deliverables/phase-2026-09-18/recheck-20260920/audit-local-sync.ps1`核对同名文件：266项均与远端Git blob原字节相同，差异0；递归包含隐藏文件核对本批磁盘集合，远端集合以外文件0。结果见[a-local-before.json](a-local-before.json)。
2. 为避免同名未跟踪文件阻挡快进，逐项重新校验SHA-256后，将266份原件保存到`E:/ss-eight-a-preserve-20260920-01/`下相同相对路径，移后哈希全一致。此目录是保留的原件副本，**本轮没有删除**。映射/哈希就在上述清单；不移动批次范围外的在做任务。
3. 执行`git merge --ff-only --no-stat origin/main`，退出0，本地main安全前进至`46aee3d`；远端的其余20个文件同时进入本机。
4. 对同步后的286个文件逐一执行`git hash-object --no-filters`并对照HEAD树：原字节差异0。`git diff --name-only 94b5fe7 HEAD -- <任务包>`为空；本批tracked修改、暂存、未跟踪、忽略未跟踪项均为0。见[a-local-after.json](a-local-after.json)。原文件/旧清单未改。
5. 核对A发布工作树`%USERPROFILE%/.codex/visualizations/2026/09/07/01a07c21-b7f9-74d2-92c5-7f8d235d8379/eight-captures-publication`：HEAD为准确94b5fe7，状态干净，本批无忽略未跟踪项；按用户要求保留工作树及`codex/toph/eight-captures-20260920`分支。其他成员副本也未清理。

## 三端核对（接受B发布后的检查点）

| 项目/命令 | 实际结果 |
| --- | --- |
| `git rev-parse main` | `46aee3d59840ad79cd5094ee471576bbf91f8bc6` |
| `git rev-parse origin/main` | `46aee3d59840ad79cd5094ee471576bbf91f8bc6` |
| `git ls-remote --heads origin main` | `46aee3d59840ad79cd5094ee471576bbf91f8bc6 refs/heads/main` |
| `git rev-list --left-right --count main...origin/main` | `0 0`，ahead=0/behind=0 |

这些查询均退出0。此后只发布本页/审计JSON及当前状态、台账的收尾补充，最终三端SHA在实际推送后另行核对并回报；不把46aee3d永久称作最新main。

## 材料去向与限制

- 286个获批任务包文件、B报告/证据已在main；本批未处理独有材料为 **0**。266份本地原件副本有明确恢复路径和逐项哈希；保留不是遗漏或新审批任务。
- 共享目录中其他continuous、帧适配、Skill及操作单等未完成资料保留，没有夹带提交。全工作区不宣称干净。
- 八段是开发集。存在门两段背景1119/1122帧放行，尚不能有效区分本批背景与目标。六段48标记峰复现一致不等于精确声学标签；标记/混响不得混入评分。调参后本批仍是开发集，不能改称独立验证集。
- 无继续录制、FFT或耐久重跑，无one/默认算法/实际工程变更；无分支或发布副本删除。未来清理须先确认无继续任务、独有材料已保护且证据可恢复。
