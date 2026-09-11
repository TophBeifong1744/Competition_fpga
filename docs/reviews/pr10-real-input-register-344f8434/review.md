# A 限定复核：PR #10 首批真实四路输入登记

结论：**通过限定复核**。本次新增登记、证据迁移、复跑适配和两处状态更新符合申请范围，未发现阻断问题。只给出后续可合入范围；本轮没有提交、推送、合并、重新签发原数据诊断或宣布阶段收尾完成。

日期：2026-09-11（UTC+08:00）；复核人：A。

## 1. 实际审核版本与隔离

- PR：https://github.com/TophBeifong1744/Competition_fpga/pull/10 ，首查与收尾复查均为 OPEN。
- 固定且实际获取的审核 SHA：`344f8434c54187f7c5d412ee1ef38335a433beff`。
- 远端分支：`task/member-b-real-input-register-01`；Git 获取结果与 PR head 完全一致。
- 本轮 main：`4957d18837f79eca7a6acc86a2757d10f41dd410`。
- 原 A 实录：`d088e2c7deda9c505c094fd48d6f90bcd7f52807`；含 B 回执的实录分支头：`2e2f685faf5520181cdd00cde2cd5030e75e67e2`。
- A 独立 detached worktree：`E:/ss-pr10-register-review-01`，固定于 344f8434。共享 checkout 与其他任务未提交工作未切换、重置、暂存或修改。
- 已先阅读最新协作约定、阶段收尾规则和 B 分工页，并核对独立副本规则与本轮 main；已读取申请中的五份登记文件、两份关联回执/交接文件、校验和复跑源码、历史日志/JSON。

上一次的访问阻断现已解除。此前 `2026-09-11-b-real-input-register-344f8434-access-review.md` 保留为当时的真实记录，不覆盖；当前技术结论以本记录为准。

## 2. 实际执行命令

远端仅执行只读查询与 fetch，无 GitHub 写操作：

```powershell
gh pr view 10 --repo TophBeifong1744/Competition_fpga --json number,url,state,headRefName,headRefOid,baseRefName,baseRefOid,files,body
git -c http.sslBackend=openssl -c http.proxy=http://127.0.0.1:7897 fetch origin main task/member-b-real-input-register-01 codex/toph/four-channel-dupont-diagnostic-01
git -c core.longpaths=true worktree add --detach E:/ss-pr10-register-review-01 344f8434c54187f7c5d412ee1ef38335a433beff
```

本机没有 BryanZheng 的 Python 路径，使用 A 本机 Python 3.12.14。以下验证由本记录旁的 `review_checks.py` 在上述独立仓库根目录实际调用，使用 `-B`，退出码 0：

```powershell
& 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B task-packages/PKG-B-ALG/tasks/four-channel-receipt-01/real-input-20260911/verify_register.py
git diff --check 4957d18837f79eca7a6acc86a2757d10f41dd410...344f8434c54187f7c5d412ee1ef38335a433beff
```

登记校验实际输出：

```text
PASS: 10 historical evidence hashes; 76 original Git blobs; 76 unchanged receipt-update blobs; receipt identity; capture index; replay syntax
No numerical diagnosis or 64-test historical regression rerun; no hardware acceptance.
```

完整检查入口实际执行为：

```powershell
& 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B 'E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/docs/reviews/pr10-real-input-register-344f8434/review_checks.py' --repo E:/ss-pr10-register-review-01 --out 'E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/docs/reviews/pr10-real-input-register-344f8434/run01'
```

`run01` 是新输出目录；该入口拒绝已有输出目录，复用时须换新路径。实际检查命令和退出码在 `run01/commands.json`，验证输出在 `run01/verify-register.stdout.txt`，stderr 为空。该入口没有运行声学数值复跑或历史测试。

## 3. 六项重点结论

| 检查 | 实际结果 |
|---|---|
| 变更范围 | 20 个文件：B.md 仅新增当前状态段；任务 README 仅替换当前状态段；新增 real-input-20260911/ 内 18 个文件。没有 FFT/PHAT、旧 run01、A 审核记录或 A/C 原件修改 |
| 历史证据迁移 | 10 个文件 SHA-256 全匹配 REGISTER，文件集合也恰为该 10 项；与固定提交对应 blob 原字节一致 |
| 原发布身份与回执 | 76 项原发布 blob/hash 全通过；A 额外检查路径唯一、集合与 d088e2c 实际 Git 树完整一致。2e2f685 中这 76 项均不变，整个回执提交仅新增 B-REVIEW.md；回执 SHA-256 与 blob 身份匹配 |
| capture 与清单索引 | 18 项 capture 路径/hash 索引无重复、无漏项；负载清单哈希直接与原 Git blob 对照通过；两段 metadata 的 acquisition、未知坐标/diagnostic 声明与登记相符，历史 reader/independent 日志的组数和 ID 一致 |
| 历史结果层级 | 原日志分别为 47、8、9 项，共 64 项；正文明确这些是历史执行。本轮没有重跑这些测试，没有把它们计成本轮执行结果 |
| 复跑适配 | 从 snapshot 检查到数值计算及结果构造的代码，统一换行后逐字一致，AST 也一致，末尾打印部分一致；仅参数路径、输入身份来源及新输出落点改变。未发现具体数值疑点，不运行 replay 的数值路径 |

复跑计算块 SHA-256（UTF-8、统一换行后）：`b2abc57e2986ace96c15cdf055d9f52604f92ea524fcfc95b865d920b0d58bfa`。差异保存在 `run01/replay-adaptation.diff`。身份来源由旧 API tree/branch 响应改为已核验的 76 项固定身份，仍检查文件 SHA-256 与 Git blob；没有去除数值断言。输出先检查不存在，再用独占创建模式 `open('x')`，不覆盖历史 JSON。这里只批准适配代码的上述检查，不声称已实际完成一次新位置数值诊断。

补充独立检查：相对链接可达、语法编译通过；20 个审核文件运行前后哈希不变，独立 worktree 检查后仍干净。详细结果在 `run01/checks.json`。

## 4. 非阻断发现与保留项

1. **时点说明须区分。** 登记保留作者核对时 main=e811c39 的历史值；本轮已更新核实 main=4957d18。原 A 实录及回执对当前 main 的祖先检查均退出 1，当前 main 同路径也没有交付文件，故“尚未合入”的实质结论仍成立。后续实际合入后才更新发布状态，不为保持旧文字重复合入。
2. **字节差异不是内容差异。** B.md 的 Git/index 为 LF，Windows checkout 为 CRLF，共 26 行，逐行文本相同；其余本次 19 个文件均与固定提交 blob 字节相同，包含全部 10 份历史证据。没有统一换行改写历史证据。
3. **本机来源限制如实保留。** A 不能直接访问 B 的 F:/NUEC 原历史目录，本轮核验的是已发布固定提交中的迁移文件、REGISTER 哈希及其绑定的原 Git 对象，不声称直接读取过 B 电脑。大文件不在 B 包重复，API 响应/失败下载/原本机完整 b-recheck 输出也未被错误宣称已发布。
4. **声学风险不变。** 几何和物理顶点映射未测、实测采样率/同步/标定/长稳未知；低频共同成分、mic2 高频差异、高相关配对继续是非阻断跟踪项。状态更新没有把相关性解释为同步证明或复制通道定论，也没有把杜邦线实录写成 C 转接板实物通过。

阻断问题：**无**。以上不要求重做原 A 数据诊断或把短片段升级成长稳门槛。

## 5. 可合入范围、职责及停止点

本次允许后续合入的范围，仅为固定 344f8434 相对 main 的 20 个文件：

- `docs/phases/2026-09-11-to-09-16/B.md` 的本次当前状态段。
- `task-packages/PKG-B-ALG/tasks/four-channel-receipt-01/README.md` 的本次当前状态段。
- `task-packages/PKG-B-ALG/tasks/four-channel-receipt-01/real-input-20260911/` 的本次 18 个新增文件。

PR #10 的本次新增 B 登记由 A 在这里限定复核通过；**不是重新签发原 A 数据诊断**。原 A 的 d088e2c 实录已有 B 在 2e2f685 的可接收回执，其合入仍由 B/主流程指定的非作者按原规则另行处理。本次批准不自动包含那 77 个 A 交付文件，也不能用原 A 的回执替代本次 B 登记审核。

本轮按用户要求停在审核及可合入范围：PR #10 保持 OPEN，未提交/推送本地审核记录、未合并任何分支。以后操作前须再次核对 main、PR head 和实际差异，不能用本记录批准新追加的内容。

本次仅为诊断材料登记，无新增获准实时算法源码，不强搬入活动 RTL/算法目录，也未创建已验收阶段快照。若后续阶段收尾，由主流程按 docs/phase-closeout.md 记录实际批准范围、两项交付各自合入 SHA 和 CLOSEOUT；不能宣称正式 M1、完整 H2、定位/波束、H3、C 板实物、系统集成或整机验收完成。
