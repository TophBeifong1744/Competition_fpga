# A 复核：四路接收诊断入口

结论：**通过，限诊断入口、专项测试及其软件证据入库**。没有发现阻断本次范围的问题。本记录不是四路采集、声学效果、H2/H3 或整机验收。

审核日期：2026-09-11；复核人：A。

## 版本、范围与副本

- 实际远端审核提交：`94e1ae9d2ed263de6160b6c14e97b3dc71392dd0`。
- 远端分支：`task/member-b-four-channel-receipt-01`；PR #9。
- 作者基线/与复核时 main 的共同祖先：`3371aa23749026726e8588b9d8875defa7b3d726`。
- 首次获取的 main：`57afba5d415811d6ad30d35844fccab8493a1e8f`。
- 独立副本：`E:/ss-four-channel-review-01`，复跑时 HEAD 为上述作者提交；没有切换、清理或提交共享主工作区的未提交内容。
- 完整检查本次新增的 10 个文件，包括 README、diagnose.py、test_diagnose.py、.gitattributes 和 evidence/run01 全部文件。分支差异仅在本任务目录；未修改 H1 读取器、合同、默认算法或 A/C 原件。
- 原 10 个文件、读取器及两份码型的 4 个输入文件，均与固定提交 Git blob 字节一致；复跑前后 SHA-256 一致。作者 validation.json 中 3 个源码哈希匹配。

## 实际命令与结果

先执行 `git fetch origin task/member-b-four-channel-receipt-01 main` 并用 `git rev-parse` 固定上述完整 SHA，再创建 detached 独立 worktree。Python 实际为 3.12.14，NumPy 2.3.5。

在独立仓库根目录执行如下命令；`python` 对应 `C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`。原始实际参数/退出码见 `evidence/a-review-run01/commands.json`。

```powershell
python -B task-packages/PKG-B-ALG/tasks/four-channel-receipt-01/test_diagnose.py
python -B task-packages/PKG-B-ALG/payload/tb/python/test_h1_reader.py
python -B task-packages/PKG-B-ALG/tasks/four-channel-receipt-01/diagnose.py task-packages/PKG-B-ALG/reference/h1-ss-data-draft-0.3/payload/examples/h1/code-pattern task-packages/PKG-B-ALG/reference/h1-ss-data-draft-0.3/payload/examples/h1/restart --out task-packages/PKG-B-ALG/tasks/four-channel-receipt-01/evidence/a-review-run01/fixture-diagnostics
```

| 独立验证 | 结果 |
|---|---|
| 本次诊断专项测试 | 15/15 通过 |
| 既有 H1 读取器回归 | 47/47 通过；不是新增 47 项 |
| 两份既有固定码型 | readable=2、rejected=0，退出 0，h2_acceptance=false |
| A 补充边界检查 | 22 组通过；清单见 independent-checks.json |
| 混合坏目录/可解析目录 | 退出 2，坏目录保留首错，可解析目录继续输出 |
| 再用已存在输出目录 | 退出 2，拒绝覆盖；此次故意测试拒绝，不删除目录重跑 |
| 每路幅值/RMS 与连续区间 Pearson 独立复算 | 通过 |
| 原始提交与输入保护 | 15 个被保护文件哈希前后一致 |

A 复跑入口保存为 `a-review-01/reproduce.py`。首次实际从 A 临时目录执行该脚本，`--repo E:/ss-four-channel-review-01`、`--out E:/ss-four-channel-review-01/task-packages/PKG-B-ALG/tasks/four-channel-receipt-01/evidence/a-review-run01`。同一脚本归档后，可在仓库根目录复现：

```powershell
python -B task-packages/PKG-B-ALG/tasks/four-channel-receipt-01/a-review-01/reproduce.py --repo . --out task-packages/PKG-B-ALG/tasks/four-channel-receipt-01/evidence/a-review-new
```

输出目录必须不存在。脚本在新目录生成测试副本，不修改交付输入；它核对固定作者提交，记录实际 checkout SHA。22 组临时输入/输出可由该入口重新生成，审核入库保留关键摘要、比较结果、日志和样例回执，不把临时测试输入冒充实录。归档后已从上述正式脚本位置再次执行，使用新输出 `E:/ss-four-channel-placement-run01`，15/47 项测试及 22 组补充检查再次通过。

## 五项重点核查

1. **格式和注册表**：直接调用既有 `ReaderSession.load`，没有旁路解析或重写读取器。四列 mic0..mic3、signed24 范围/右对齐 int32、精确 uint64 均沿用严格合同。另测 3/6 通道、错误存储格式、PCM 下溢、ID 上溢/回绕拒绝；同配置内容冲突、跨配置同 geometry 冲突、同 acquisition 重叠均拒绝。坏输入不会注册配置或终点；后续好输入不受污染。
2. **编号、错误及区间**：错误行 PCM、原 ID、flags、物理 CSV 行号一致；未删除、重排、补样或拼接输入。补测 32 行无错区间 + 大幅缺号/错误行 + 32 行无错区间，得到两个区间各 6 个通道对，共 12 项；没有跨边界求相关。大于 2^53 的 ID/缺号计数及 uint64 最大值以十进制字符串保留。同 acquisition 的文件间未知间隔不虚构缺号，也不跨文件相关。
3. **幅值及提示**：用原始 CSV 的 Python 整数平方和及 `math.fsum` 复算全部行/无标志行的范围、均值、RMS、AC RMS、端点数、峰值及零码数；统计不调用被测 amplitude。容差 relative 1e-13、absolute 1e-9；相关性单独复算，absolute 1e-14。PCM 转 float64 后平方避免 int32 溢出；ID 不进入浮点。零/常量通道 Pearson 为 null，精确相同/反相及高相关只作线索。满量程端点不等于已确定削顶；格式无错不等于声学干净，相关性不能证明同步、映射或复制硬件。
4. **失败及原件保护**：首个格式错误拒绝整段，不提供部分波形统计；其他目录继续。可解析但带错误标志仍可退出 0，完整报告保留错误；至少一份拒绝退出 2。拒绝覆盖现有输出、输入本身或输入子目录；非法相关阈值/最短长度在建输出目录前拒绝。已核实缺失输入目录可结构化报告并继续；未做文件系统权限故障或磁盘故障注入，不承诺所有运行环境故障都能输出完整报告。
5. **证据层级**：即便元数据自称 hardware-audio/accepted/calibrated，acceptance_verified、calibration_verified、h2_acceptance 仍为 false。当前只有格式码型和单元测试，没有实际四路录音，没有 DOA、SNR 或硬件同步结论。没有重跑无关历史声学研究。

## 数值差异与字节差异

- 复跑 summary.json、errors.json 对绝对仓库路径做显式归一后，与作者结构化结果相同；环境字段单独记录，未作为数值结果比较。
- 三个生成文件 summary.json、errors.json、receipt.md 均非字节一致，包含作者与 A 不同绝对路径；各自 SHA 已记录，不能称全部文件字节复现。作者源文件/输入文件本身则字节及哈希一致。
- 数值独立复算结果及绝对差逐项保存在 `numerical-checks.json`；未通过改原证据、去断言或重写来源哈希获得 PASS。

## 问题、限制与批准范围

阻断问题：无。

非阻断文档说明：作者 README 末段保留了交付前“未提交/推送/合入”的文字。这是原始开发快照，不是当前发布状态；实际已提交发布的事实由本记录的完整 SHA 和 PR #9 记录确定。保留原文与 run01，避免覆盖作者证据；作者自测、A 此次独立限定批准和后续合并必须区分。

允许合入仅限：上述 10 个任务文件及 A 本目录内新增的复核记录、复跑脚本和关键证据。原读取器、默认算法、A/C 交付及其他任务不在变更批准范围。本次不是 input-boundary、FFT/PHAT 定点方案或历史声学研究的扩大批准。

使用位置：继续以本目录 `diagnose.py` 为可运行的四路短片段诊断入口，复用现有包内读取器；不另复制到活动声学算法目录。按 `docs/phase-closeout.md` 的诊断类例外，本次无需强行迁移到实时/算法主线，也不提前触发 9 月 16 日阶段验收。下一步由 B 在同一任务包为真实四路输入添加**新的**诊断回执目录；正式阶段收尾再登记本限定批准与入口。旧 run01 和 A run01 均保留。

不批准：真实四路 H2、硬件采样/同步/映射/采样率、定位/降噪效果、完整 H3、资源时序、实板或整机验收；也没有小时级内存/吞吐证明。

A 决定：本限定软件复核通过后合入 PR #9；合并提交与合并后适用回归由发布记录报告，不能把 Git 合并视为扩大技术批准。
