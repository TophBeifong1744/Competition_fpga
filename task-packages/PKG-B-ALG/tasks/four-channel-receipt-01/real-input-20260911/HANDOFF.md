# 交 A 的稳定登记包与合入准备

本任务作者只准备与提交登记，不自行合并。原 A 数据和新增 B 登记是两项不同批准范围。

## 1. 原 A 交付：已有 B 回执

源分支 `codex/toph/four-channel-dupont-diagnostic-01`；已复核原输入 `d088e2c7deda9c505c094fd48d6f90bcd7f52807`，发布回执头 `2e2f685faf5520181cdd00cde2cd5030e75e67e2`。B 原回执可接收，无本轮阻断。此次检查确认回执头保留全部 76 项原交付对象。

处理人按原规则为复核人 B / 主流程指定的非作者合入人，不能把此说明当作 A 作者自合入授权。操作前重新 fetch，检查 `git merge-base --is-ancestor 2e2f685faf5520181cdd00cde2cd5030e75e67e2 origin/main` 的返回值：0 则已包含，跳过重复合入；1 则未包含；其他非零为检查失败，先处理错误。如曾 squash/rebase，需检查现有 PR 合并记录与交付目录内容，不能仅凭祖先关系再次合并。

头若已超出 `2e2f685`，先检查新增差异，不能沿用本回执覆盖后续提交。范围只应为 `task-packages/PKG-A-ACQ/deliveries/dupont-diagnostic-20260911/`，当前基线比较共 77 个新增文件；原 76 项加 B-REVIEW。在 GitHub 按 head 查询既有 PR，有则沿用，无则由合入负责人创建该固定交付范围的 PR，不能重复建单或顺带 PR5。

## 2. 新增 B 登记：待 A 复核

分支 `task/member-b-real-input-register-01` 从 main `e811c39` 建立，不以 A 尚未合入的数据分支为父，因此登记 PR 不携带 A 原件或其他任务文件。允许差异仅为：

- `docs/phases/2026-09-11-to-09-16/B.md` 当前输入状态段。
- `task-packages/PKG-B-ALG/tasks/four-channel-receipt-01/README.md` 当前状态段。
- 同任务下新增 `real-input-20260911/` 全目录。

A 复核：确认来源 Git SHA 和回执范围，运行 `verify_register.py`，核对历史日志没有冒充本轮复跑，检查未完成项及来源声明没有升级为整机通过，检查可选复跑适配未改数值计算。本次不用重跑完整历史研究。A 批准前登记仍为作者自检；A 批准并合入后才更新其状态。

以下为具体发布步骤，**本文件中的命令不代表已经执行**。在本分支独立干净 worktree 内执行，远端已有同 head PR 时直接沿用：

```powershell
git status --short
git rev-parse HEAD
git diff --name-status origin/main...HEAD
git push -u origin task/member-b-real-input-register-01
gh pr list --repo TophBeifong1744/Competition_fpga --head task/member-b-real-input-register-01 --state all
# 确认无既有 PR 后创建；正文是已准备好的文件。
gh pr create --repo TophBeifong1744/Competition_fpga --base main --head task/member-b-real-input-register-01 --title 'docs: register reviewed four-channel Dupont recordings' --body-file task-packages/PKG-B-ALG/tasks/four-channel-receipt-01/real-input-20260911/PR-BODY.md
```

将实际 PR URL 与提交 SHA 交指定复核人 A。这里不猜 A 的 GitHub 账号，不设置 auto-merge，也不提供作者自合入命令。A 数据可以先由其复核人按限定范围合入；B 登记 PR 仍必须单独由 A 复核，前者通过不自动批准后者。合入前重新检查最新 main 和 PR head，若范围变动则重新确认对应差异。

网络环境如遇本机 schannel 凭据问题，可用本次已成功的 `git -c http.sslBackend=openssl -c http.proxy=http://127.0.0.1:7897 fetch origin`；safe.directory 只指定正在使用的实际 checkout 路径，不改全局配置。

## 3. 合入后主流程收尾

记录两个实际合入 SHA、批准人及准确范围，更新 B 页中“尚未合入”的时点说明。按 `docs/phase-closeout.md` 在相应阶段集中归档批准后的快照和 CLOSEOUT，注明本次只是诊断材料登记，无新增获准算法源码，不推定完整 H2/H3 或系统集成完成。旧 run01、A 审核记录、A/C 原件与其他任务分支继续保留。
