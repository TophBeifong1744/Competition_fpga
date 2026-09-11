# A 复核记录：首批真实四路输入登记（固定交付不可达）

日期：2026-09-11（UTC+08:00）；本次对象检查时间为 22:16 左右。

结论：**暂不能通过限定复核，需补齐本机可访问的固定交付。** 状态为 `BLOCKED_INPUT_ACCESS`，不是“材料不存在”，也不是已发现实现缺陷。没有批准新增登记或任何合入范围；本轮没有推送、合并、阶段验收或覆盖原件。

## 1. 审核身份与先决检查

- 请求审核分支：`task/member-b-real-input-register-01`。
- 请求固定提交：`344f8434c54187f7c5d412ee1ef38335a433beff`。
- **实际取得并完成实质审核的本次 B 提交：无。** 本机对象库没有该提交，不能用旧版或原 A 提交替代。
- 用户指定本地副本 `F:/NUEC/review-worktrees/member-b-real-input-register-01` 在 A 当前电脑不可访问；`F:/NUEC` 本身也不存在。不能据此推断 B 电脑上的副本不存在。
- 用户提供的 BryanZheng Python 路径在本机不存在；Toph 本机 Python 可用，但缺少待审脚本，尚未运行登记校验。
- 已完整阅读共享目录以及最新获取 main 的 AGENTS.md、docs/phase-closeout.md、docs/phases/2026-09-11-to-09-16/B.md。共享 checkout 未切换、重置或暂存；未访问或修改其他任务副本的未提交内容。

## 2. 远端与本地取得尝试

当前仓库为 `TophBeifong1744/Competition_fpga`；以下 Git 命令在 A 共享仓库根目录仅操作对象/远端跟踪引用，不切换工作树。网络参数只用于单次调用，没有修改全局配置。

```powershell
git -c http.sslBackend=openssl -c http.proxy=http://127.0.0.1:7897 ls-remote origin refs/heads/task/member-b-real-input-register-01 refs/heads/codex/toph/four-channel-dupont-diagnostic-01 refs/heads/main
git -c http.sslBackend=openssl -c http.proxy=http://127.0.0.1:7897 fetch origin main codex/toph/four-channel-dupont-diagnostic-01
git -c http.sslBackend=openssl -c http.proxy=http://127.0.0.1:7897 fetch origin 344f8434c54187f7c5d412ee1ef38335a433beff
git cat-file -t 344f8434c54187f7c5d412ee1ef38335a433beff
```

实际结果：

- `ls-remote` 成功，但没有返回请求的 B 登记分支。
- 当前远端 main：`4957d18837f79eca7a6acc86a2757d10f41dd410`。
- 原 A 实录分支头：`2e2f685faf5520181cdd00cde2cd5030e75e67e2`。
- 获取 main 与原实录分支成功。
- 按固定 SHA 直接获取失败：`remote error: upload-pack: not our ref 344f8434c54187f7c5d412ee1ef38335a433beff`，退出 1。
- 本机 `cat-file -t` 返回无法取得对象信息；共享本地任务目录也没有 real-input-20260911/verify_register.py。
- 因精确提交尚不可取得，没有建立一个假称固定在该 SHA 的审核 worktree。取得后才创建 A 自己的独立副本。

## 3. 已执行的适用前置核查（不重复诊断）

1. 从固定 `2e2f685faf5520181cdd00cde2cd5030e75e67e2` 读取原交付目录的 B-REVIEW.md 与 B-START.md。回执明确审查 `d088e2c7deda9c505c094fd48d6f90bcd7f52807`，结论为“可接收、无本轮阻断”。B-START 保留的是原交付时“B 回执尚待”的历史说明；不能用它否定后来回执。
2. 执行 `git diff-tree --no-commit-id --name-status -r 2e2f685faf5520181cdd00cde2cd5030e75e67e2`，该回执提交仅新增 B-REVIEW.md。与 d088e2c 的差异也仅此文件，原 A 输入及原件没有随这次回执更新改变。
3. 对 d088e2c 下 `task-packages/PKG-A-ACQ/deliveries/dupont-diagnostic-20260911/` 执行 `git ls-tree -r -l`，得到 76 个发布文件；将其对象 ID 交给 `git cat-file --batch-check=%(objectname) %(objecttype) %(objectsize)`，76 个 blob 均可取得，类型与大小和树条目一致。**这只是本机原发布对象可用性检查，不是 REGISTER.json/历史迁移清单的哈希校验通过。**
4. 对 d088e2c 与 2e2f685 分别执行 `git merge-base --is-ancestor <SHA> origin/main`，均退出 1；再检查当前 main 中原交付目录，未列出文件。因此原 A 交付与该 B 回执当前没有进入 main，也未在同路径发现已落地的重复副本。本轮没有自行合入。
5. B 回执记录安静/人声两段、每段 32000 组，ID 分别为 17544..49543 与 15798..47797；几何未测、共同低频成分、mic2 高频差异、高相关配对及全部批准限制均仍在原回执中。以上为核对历史回执记载，**不是 A 本轮重新签发数据诊断或重复复算波形**。
6. 原 B 回执的 47+8+9=64 项属于历史执行结果。本轮没有重跑这些测试，没有运行原诊断、replay_independent.py 或产生新的诊断 PASS。

## 4. 本轮尚不能完成的核心检查

| 请求项目 | 本次状态 |
|---|---|
| B.md/任务 README 当前状态段及新增目录的变更范围 | 未审：344f8434 不可取得 |
| README、REGISTER、VALIDATION、HANDOFF、PR-BODY | 未读：不能由用户摘要代替文件正文 |
| `python -B .../real-input-20260911/verify_register.py` | **未执行**：该固定提交与脚本不可取得 |
| 历史证据迁移哈希、REGISTER 绑定的 76 项对象、回执身份/capture 索引 | 未完成；不能以原发布对象存在替代 |
| replay_independent.py 是否只改路径/身份读取/输出落点、不改数值计算 | 未审；未无故重跑整套诊断 |
| 新状态文字是否保留几何/频谱/通道风险且没有扩大批准 | 未审；原 B 回执边界已核对 |

## 5. 发现、批准边界与下一步

阻断项：**交付可达性**。请 B 将上述固定提交发布到请求分支，或提供 A 可读取且含该提交及所需历史 Git 对象的 bundle/独立仓库副本。单独复制零散 Markdown 不能支持本次提交与对象核验。

非阻断事实：原 A 数据确有 B 的限定接收回执；原输入未被 2e2f685 的回执更新修改；原发布 76 个 Git blob 当前均可读取。原 A 交付未入 main 是发布状态，不撤销 B 已作出的原范围复核。

批准区分：原 A 实录由 B 复核、依非作者合入规则另行处理；本次新增 B 登记需要 A 对 344f8434 单独复核，二者不能替代。此前 PR #9 的诊断入口批准也不能覆盖未取得的新登记。

当前允许自动合入范围：**无**。待上述输入可达后，只评审 B.md/任务 README 的指定状态段和 real-input-20260911/ 新增材料；继续不重跑整套诊断、不扩大为正式 M1、完整 H2、定位/波束、H3、C 板实物或整机验收。届时审核另存新记录，保留本次阻断记录和所有历史证据。
