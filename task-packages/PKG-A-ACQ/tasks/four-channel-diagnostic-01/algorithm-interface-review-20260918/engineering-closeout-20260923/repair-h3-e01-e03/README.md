# H3-E-01～03 作者返修入口

实际日期 2026-09-21。仅独立 Python 工程状态模型与复跑入口；未提交、未获 B 增量批准。不替换旧包入口或生产工程。

## 固定范围

- 工程原件：`0abdc91c57787b7c868a797b88f35129de169faf`。
- B 反馈及反例：`02f4ec23d771bd33a04ae3f297178ca34d537eb8`，`docs/reviews/a-h3-two-20260921/`。
- 软件依赖：`f879a54cf40359209895af955bcef92accdf79ea`。
- 本次只读远端 main：`949d7a0ad040975290aa4c3b692e1e0188f6af63`；共享 HEAD 为 `fd1b99c966de1f572bcd080f2b2d6860c0ac5ccd`，未切换或同步脏目录。
- PS C 候选 `fbbaa161098582ba1e5e112b86d39533769bb3e7` 不修改，不用于关闭本包缺陷。

## 三项改动

| 问题 | 修复与语义 |
|---|---|
| E01 | `ever_committed` 单调保留；可用性单独由 state 表示。当前 epoch 内已提交帧在 CLIP/STOP/RESET 后晚错仍 fail-stop，撤销后续帧；STOP/RESET 本身不递增 epoch，只有显式 start 建立新会话。旧 epoch 回调保留审计，不杀死新会话。stop 与 error 同次出现时先停止，但不吞掉追溯错误。 |
| E02 | 首次成功 submit 绑定会话配置；后续包括新 interval 都必须相同。递归、带类型的 tuple 快照隔离 dict/list 嵌套变更；不支持的类型明确拒绝。新 session 才允许新配置。条目元数据属于模型内部，不授权调用方修改 entries。 |
| E03 | `prepare.py` 从三个准确 Git 提交读取对象，导出到不存在的新目录，记录 commit/path/blob/SHA-256。不读共享兄弟任务包、不回退分支。`run_checks.py` 在导出目录运行，仅依赖本目录已校验快照，无 Git 或作者 cwd 依赖。 |

此增量的正式入口为下面命令。旧 run_checks.py、清单和证据故意保持原字节；不能继续把旧入口当修复入口。

## 可复跑命令（PowerShell）

```powershell
$repo = 'E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga'
$py = 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$fix = "$repo/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/engineering-closeout-20260923/repair-h3-e01-e03"
$out = 'E:/h3_repair_replay_01' # 必须不存在；改名创建新证据，不覆盖
& $py -B "$fix/source/prepare.py" --repo $repo --out $out
if ($LASTEXITCODE -ne 0) { throw '准备失败，停止' }
Set-Location $env:TEMP
& $py -B "$out/run_checks.py"
if ($LASTEXITCODE -ne 0) { throw '回归失败，保留 run/full.log' }
& $py -B "$fix/source/check_entry.py" --repo $repo --clean $out --out "$fix/evidence/entry_replay_01"
```

准备阶段要求本地 Git 对象库已含三个准确提交。缺失时报错停止；由发布方提供这些对象，不改用 main。在任何包含所需对象的干净仓库中也可准备，未要求将两个兄弟提交合并。本轮实际使用独立文件导出副本（不是 Git worktree），最终 clean03 从 `C:/Windows/Temp` 启动成功。

## 结果入口

- `evidence/clean03/run/summary.json`：最终 10 组 unittest，含原受影响的 epochs/priority/identities 三个函数原样提取执行；0 failures、0 errors。数量不与历史轮次累加。
- `evidence/clean03/run/full.log`：完整本轮输出。
- `evidence/clean03/run/adversarial-results.json`：原 E01/E02 反例成立，基线错误返回 COMMITTED；不是修复通过报告。B 脚本仅 AST 替换三个机器路径，原脚本字节保留。
- `evidence/clean03/run/e03-original-failure.txt`：执行原 old_unchanged 函数复现 FileNotFoundError；其 Git 读取以准确对象导出记录重放，不重跑无关数值测试。
- `evidence/clean03/bindings.json`：来源绑定及新修复源码哈希。
- `evidence/entry02/`：已有输出拒绝、空对象仓库拒绝，以及原工程包／C 候选逐文件核对。允许 Git 文本 CRLF 规范化，保留原始和本地双哈希。

## 失败历史与限制

首次 clean01 准备尚未结束时过早调用测试，报找不到 run_checks.py，退出1；待准备退出0后才重跑，非负例通过。clean01/02 是中间 9 组版本，最终 clean03 增加原状态合同复用。entry01 在长路径创建空 Git 仓库退出128，未进入依赖负例验证；entry02 改为系统临时短路径空仓库，保留前轮材料。

数值、FFT、耐久测试沿用 B 固定报告，本轮不计新执行。ARM/BSP、XSim、实现、CDC、实板均 NOT_RUN；REALTIME_BLOCKED 保持。此模型的顺序事件调用不是异步硬件证明；未冻结生产 ABI、未宣称完整 H3。完成作者自检后交工作执行发布待审 SHA，再由 B 增量复核。
