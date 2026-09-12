# 2026-09-11 已完成任务分支与本地副本清理

执行依据：用户要求按9月10日阶段验收结果合并、清理已完成任务，保留未完成任务。核对基线：远端 main `73352fc22ddf3f5aa5b923e7b4fadc5efd8fa6ad`；本轮已重新拉取远端并读取 PR 1～8 的状态。

## 结果

- 删除9个已结束的本地复核工作树，原文件合计6,346,164,844字节（约5.91 GiB）。
- 删除5条远端短期任务分支、6条本地已完成复核分支。
- 1168个差异/未跟踪/忽略文件条目先压缩备份，逐文件解压流SHA-256核对通过；另保存暂存与未暂存二进制补丁、Git状态及完整历史bundle。有效恢复资料约1.20 GB，不上传仓库。
- 被删除分支的提交均已包含在main历史，无需再次重复合并。未整支合并任何未通过复核的算法或采集任务，不扩大原有验收结论。
- 主工程未提交内容、stash、成员长期工作分支及未完成任务均保留。本轮没有同步覆盖脏的主工作区，也没有清理其他比赛项目或Codex聊天。

## 删除的本地目录

下列目录均位于 `E:/Users/Toph Beifong/Documents/GitHub/`，删除前核对实际路径、所属Git仓库、HEAD、无重解析点及备份后未变化。操作通过Git工作树管理移除，不对GitHub父目录递归删除。

| 目录 | 原HEAD | 完成/替代依据 |
| --- | --- | --- |
| Competition_fpga-review-b | 9e104b0 | B旧稳健性复核已集成；复跑额外数据保留在备份 |
| Competition_fpga-review-c-mic | fcff86f | C麦克风资料归档已集成；临时图片/原始包保留 |
| Competition_fpga-review-six | 25a6257 | PR3旧复核副本，后续e3f4905完成限定集成；reviewer-copy和原始复跑输出全保留，不将其另作批准 |
| ss-b-budget-integration | 9878cca | A限定预算复核已集成 |
| ss-input-boundary-review | d262f27 | 输入边界交付已集成 |
| ss-review-int-r2 | 1ec105f | 旧中断集成尝试，后续int-r3/e3f4905替代；302项暂存差异和合并状态备份，不用旧尝试覆盖最终版本 |
| ss-review-int-r3 | e3f4905 | PR3最终合并副本 |
| ss-review-r2 | df4146a | PR3上一轮复核副本；额外日志已备份 |
| ss-review-r3 | 6491d1b | PR3最终原始提交，已随e3f4905合入 |

## 删除的分支

远端删除使用旧SHA条件保护并作为一组执行；若远端被他人更新则不删除。删除后再次查询远端确认。

| 远端分支 | 原SHA |
| --- | --- |
| codex/toph/input-boundary-0.1 | d262f275ed6817b07f732d5c85f675fd4ebeccdc |
| codex/toph/mono-diagnostic-delivery | 93a12aab1eb5d2e70e118761a35d2d654845424b |
| codex/toph/review-b-input-budget-01 | 9878ccafdda6cd5a522cc9de95c1277bcee70f08 |
| review/member-b-to-a-pkg-b-alg | 6491d1bab04038b71fdd8c22d45a58455aa58ade |
| task/member-b-0910-closeout | 0dc3e65d5989317540a10e2961c4acfb7cb307a4 |

删除的本地分支：`codex/toph/input-boundary-0.1`、`codex/toph/review-b-input-budget-01`、`codex/toph/review-b-robustness`、`codex/toph/review-c-microphone`、`review/member-b-to-a-pkg-b-alg`、`codex/toph/pr8-review`。删除前确认未被其他工作树检出，按准确SHA删除引用。

`mono-publication`位于本次指定GitHub目录以外，因此其本地工作树和本地分支未删除；只是远端已完成交付分支清理。其余范围外工作树同样未删除。

## 保留及原因

| 对象 | 原因 |
| --- | --- |
| Competition_fpga | 主工程，存在未提交/未跟踪的独有工作；不重置、不清空 |
| Competition_fpga-ddr-delivery / codex/toph/ddr-dma-delivery | 4bfaeb3含未整支集成的交付和证据，尚不满足本次清理条件 |
| Competition_fpga-h2-diagnostic / codex/toph/h2-diagnostic-capture | H2四路真实输入任务仍在进行，有独有提交 |
| ss-b-budget-review / review/member-b-budget-to-a-01（PR5仍OPEN） | 只有input-boundary-adoption-01获准导入；额外126文件不在批准范围，保留原始待审副本 |
| codex/toph/fft-ip-budget-01 | 候选FFT交付仍待限定复核 |
| codex/toph/h3-fpga-integration-constraints | 文档已合入，但仍承担H3输入复核，暂不清理 |
| codex/toph/pkg-a-acq、pending-review-packages-20260908 | 包含待审DDR或其他历史交付，不因局部成果入库而整条丢弃 |
| codex/c-rtl-001-outsourcing-docs | 已推进到99a48b0，含新004进度报告，不能按PR4旧合并状态删除 |
| codex/toph-development、feature/member-b-algorithm、feature/hsc119 | 成员长期工作入口；不是完成一次子任务就删除的临时分支 |

C状态补充（9月11日后续接收核查纠正）：99a48b0的直接父提交就是0457afc，完整树已含004源码及日志，26项原清单匹配。先前只看99a48b0新增报告而误判“未交付”不成立，报告里的“尚未推送”是历史文字。正确状态为已交付、待独立技术复核；保留分支的决定不变，不倒改9月10日原检查时点。详见 task-packages/PKG-A-ACQ/outsourcing/review-status/c004-next-stage-20260911.md。

清理后，指定GitHub目录中本项目只剩主工程及上表3个待审/进行中副本。Competition_CUMCM未作修改。

## 备份与恢复

本机有效备份位置：

`C:/Users/Toph Beifong/.codex/visualizations/2026/09/05/01a06fc1-b474-7a41-9b32-b2aa8386099b/cleanup-2026-09-11/verified/`

- `inventory.json`：完整原路径、HEAD、差异列表、文件长度及SHA-256、ZIP校验和。
- `all-refs-before-cleanup.bundle`：清理前的分支、工作树HEAD及可达完整Git历史，bundle验证通过。
- 各目录同名ZIP：`files/`保存差异/未跟踪/忽略文件，`git-state/`保存原索引及合并状态用于追溯。
- 同名`.staged.patch`和`.unstaged.patch`：准确保留暂存与工作区差异（包含删除文件）。

恢复时在**新的空路径**按记录HEAD重建工作树，按需依次应用暂存、未暂存补丁，再把ZIP的`files/`内容还原到原相对位置。历史已在main中；若原仓库不可用，可先从bundle恢复。`git-state/`只用于追溯，勿直接覆盖新工作树的Git管理目录。删除的远端分支也可从表中SHA重新创建。

不要清理上述有效备份，除非已确认其中独有复跑资料不再需要。报告不代表重新运行算法、RTL或板测。
