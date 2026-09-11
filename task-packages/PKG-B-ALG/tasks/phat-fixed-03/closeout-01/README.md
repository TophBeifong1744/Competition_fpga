# 定点误差与预算收口草稿 01

2026-09-11；作者归档分析已复跑，稳定草稿交 A 包级复核。没有冻结数制或误差门限，没有完整定点链/H3/实板通过结论。9/16提供可复现进展；完整包/H3按9/22及成熟度评审。

研究输入固定为已发布提交 `bff45e7bbedab321fc4815e1432f1575c750edc4`，本分支 `task/member-b-fixed-closeout-01`，专用工作树 `F:/NUEC/review-worktrees/member-b-fixed-closeout-01`。读取远端 main `e811c399adaa083d520bfda998f15fe86b445b9a` 的 AGENTS.md、docs/phase-closeout.md、docs/phases/2026-09-11-to-09-16/B.md，未混入其余主线改动。上游 README 中“未推送”及旧 HEAD 是历史记录；本次以固定发布 SHA 为来源，不改写原件。

## 本包入口

| 内容 | 入口 |
|---|---|
| 误差分布、范围与信息损失 | [ANALYSIS.md](ANALYSIS.md) |
| 格式、运算、缓存、参数化调度及 A 候选差异 | [BUDGET.md](BUDGET.md) |
| 完整交付索引、验证层次与 A 待补项 | [HANDOFF-TO-A.md](HANDOFF-TO-A.md) |
| 本轮源代码 | [analyze.py](analyze.py) |
| 哈希、环境、196 NPZ核验和96组旧统计复算 | [evidence/run01/verification.json](evidence/run01/verification.json) |
| 幅值汇总/联合分层/尾部定位 | [amplitude.csv](evidence/run01/amplitude.csv)、[strata.json](evidence/run01/strata.json)、[tail-cases.json](evidence/run01/tail-cases.json) |
| 逐对和逐级差异 | [pairs.csv](evidence/run01/pairs.csv)、[stage-pairs.csv](evidence/run01/stage-pairs.csv)、[stage-amplitude.csv](evidence/run01/stage-amplitude.csv)、[numerical-loss.csv](evidence/run01/numerical-loss.csv) |
| 本轮新增文件清单 | manifest.json（不替换任何上游 manifest） |

## 准确复跑

在本工作树根目录运行，Python 3.12 + NumPy（本轮 NumPy 2.3.5）；不需供应商 DLL。本轮只分析已归档196帧，不再扫描场景。输出目录必须不存在：

```powershell
$py='C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $py -B task-packages/PKG-B-ALG/tasks/phat-fixed-03/closeout-01/analyze.py --out task-packages/PKG-B-ALG/tasks/phat-fixed-03/closeout-01/evidence/reviewer-run01
```

原交付完整性检查（实际已退出0：16个清单文件、12个本地链接、分析源码与输出哈希一致）：

```powershell
& $py -B task-packages/PKG-B-ALG/tasks/phat-fixed-03/closeout-01/verify_delivery.py
```

完整性检查会拒绝本目录内新增但未列清单的文件，因此应在生成reviewer输出之前运行，或把reviewer输出放到本目录外的新路径。新增复核结果不得覆盖本次manifest。

实际已运行同命令，输出为 `evidence/run01`；退出0，输出 `Verified 196 NPZ / 11760 candidate pairs / 96 archived amplitude groups`。重新解压219818744字节逐字节哈希核对，核验7个上游源文件、196个NPZ及每个归档比较字段；重算PCM、整数窗和公共指数舍入数组，并用归档整数窗新增浮点PHAT/IFFT/峰对照。96个幅值统计全部恢复一致。本轮未调用供应商模型、Vivado、板卡或更改历史证据；本结果不是独立评审人的验收。

`verification.json` 记录输出文件哈希和源码SHA。跨机器先核对原件bytes/hash，再核对数组整数值及有效性/掩码/峰等离散结果；浮点统计允许环境差异必须明确报告，不能直接宣称字节一致。JSON/CSV容器哈希与数值结果是两种检查。本脚本不修改归档，也不重新打包原frames。

本阶段无新增获准源码。全部新增材料为待审研究，尚不接入rtl/tb/sim/model活动目录，不创建“已验收”快照；A批准准确范围后由复核/主流程按phase-closeout规则集成并在新位置验证。未改四路接收任务、阶段公共状态页或 A/C 文件。
