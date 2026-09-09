# A 对 PKG-B-ALG 六麦研究修订的第二轮复核

日期：2026-09-09。结论：**需修改；暂不合并**。

本次科研计数与数值诊断继续一致，缺失日志、近零角度比较及 main 历史评审兼容问题均已有实质修复；剩余阻断是 A 无法在收到的材料与可用环境中完成历史输入的精确复现。不是认定算法结论错误，也不是宣称 B 在其机器上的运行记录失败。

## 审核对象与隔离

- PR：<https://github.com/TophBeifong1744/Competition_fpga/pull/3>
- 实际远端/审核提交：`df4146af6aab3263209f54bb36ded8693d2d9d90`。
- 上轮请求修改对象：`25a6257fe3136b058cefa06e86fde0f3c8dd8dff`；旧批准不沿用。
- 本轮 main 集成基线：`1ec105f609ac52d7b97d3245a90dc212591c1cfa`。
- 原提交独立工作区：`E:/Users/Toph Beifong/Documents/GitHub/ss-review-r2`。
- 集成独立工作区：`E:/Users/Toph Beifong/Documents/GitHub/ss-review-int-r2`，从上述 main 执行 `git merge --no-commit --no-ff df4146af6aab3263209f54bb36ded8693d2d9d90`，仅试合并，不提交、不推送。
- 共享工作区未切换分支；B 已提交证据未被复现覆盖。本报告与本轮 A 证据另存，不覆盖上一轮报告。

相对上轮，六个历史研究目录唯一变化为补充 `stable-wrong-01/run.log`；其余整改在 `PR3-REVISION.md` 与 `revisions/pr3-repro-01/`。整个 PR 的 302 个差异路径均为允许范围内的新增文件；没有修改默认 PHAT、跟踪器、其他成员文件。独立试合并后没有修改或删除 main 的既有文件。

## 复现命令与真实结果

Python：`C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`，CPython 3.12.14 / NumPy 2.3.5，Windows 11。A CPU 为 Intel Family 6 Model 183，具有 AVX2/FMA3，不具有 AVX512。完整版本、动态库哈希与 CPU 路径在本轮 `environment.json` 中。

以下命令在独立副本的 `task-packages/PKG-B-ALG` 执行，`<A_OUT>` 为全新 A 证据输出目录：

```text
python -B revisions/pr3-repro-01/verify_release.py
python -B revisions/pr3-repro-01/run_all.py --out <A_OUT>/review-df4146a-run01
```

| 项目 | A 实际结果 |
|---|---|
| 六包文件清单 | 142/142 存在且 SHA-256 匹配 |
| 冻结路径 | 633 个去重路径通过 |
| 修订目录清单 | 153 项通过 |
| 修订机制测试 | 7 项通过 |
| 六组回归（依赖顺序） | 170、172、173、173、173、172 项通过；各组重复包含原 167 项，不能相加宣传为独立测试数量 |
| 五个 final | 全部通过 |
| narrowband live audit | 通过 |
| subband live audit | 输入哈希校验失败 |
| leave-band-out live audit | 通过 |
| effective live audit | 输入哈希校验失败 |
| stable 完整受支持入口 | 输入哈希校验失败，未完成全部对照 |
| 完整 run_all | 17 个阶段中 14 通过、3 失败；退出码 1 |

精确命令、退出码、失败 traceback、每项数值差异和输入哈希均保存在 `a-review-20260909-r2/review-df4146a-run01/`；不能用 B 原有 PASS 记录替代本表。

## 上轮三类问题的关闭情况

### 1. 缺失 run.log：已关闭

补交日志 SHA-256 为 `fb1e82e7e76c53706568e19883ba46ffd61cae4b0ee1e3f163c75c66713121fb`，与上轮已存在的原清单相同；这是对补交字节的独立确认。作者本地找回路径属于作者来源声明，A 没有访问该机器。新增缺失/篡改拒绝测试已实跑通过。

### 2. 数值比较：近零角度问题已关闭；输入复现仍阻断

新版采用归一化向量的 atan2 夹角，并用 binary64 舍入预算映射旧 arccos 结果的比较区间；没有把大容差带入分类门限。实际分类、计数及样本键继续精确检查。

在 A 侧，leave/effective 对旧近零夹角的最大差异分别约 `1.7075472925e-6°`、`1.9090959104e-6°`，均通过逐值误差界；时延变化重算差异为 0。effective 已通过全体落盘分类/统计重算，随后才在输入重建处失败。此次失败不再是上一轮的 near-zero acos 问题。

剩余阻断首次出现位置：

| 入口 | 条件 | seed | 不同的历史哈希字段 |
|---|---|---:|---|
| subband | tone900__front__early_late | 2026091500 | input、target、RIR |
| effective | tone1200__front__early_late | 2026091700 | input、target、RIR |
| stable | band__az32__early_late | 2026091700 | input、target、RIR |

这三处 noise 哈希相同。错误均明确为 `UNSUPPORTED_EXACT_INPUT_ENVIRONMENT`。特别注意：A 的 RIR 也不同，不能把 B 受控实验中“RIR 相同”的观察直接套到 A 机器。

B 已诚实收窄到其 AVX512 环境，也保留输入不一致即失败的保护。这是合理的环境边界说明，但当前没有提供 A 能实际使用的匹配执行环境或已绑定历史哈希的参考输入。因此“支持环境已说明”尚不等于“A 完成了可验收复现”。本轮不以跨 CPU 字节必须相同为普遍要求；真正缺失的是输入不同后，可独立判断差异的参考或可访问的精确复现路径。

### 3. 当前 REVIEW 与历史冻结：已关闭

在独立 main 试合并副本中，新 release 和五个 final 全部通过。`history/REVIEW.md` 已与 `25a6257:task-packages/PKG-B-ALG/REVIEW.md` 的 Git 原始 blob 逐字节比对；当前根 `REVIEW.md` 与 main 原始 blob 逐字节一致，Git blob 均为 `f5dd54b5db0f4938746148d8d53c652c59251e5d`。不是删除 A 旧评审后获得通过。

集成核查命令：

```text
python -B review_revision_checks.py <INTEGRATION_WORKTREE> <A_OUT>/integration-r2
```

脚本同时独立核对修订 source-origins 的 10 条源码哈希；详细子命令与返回码见 `integration-r2/result.json`。这一结果只关闭集成兼容问题，不覆盖输入复现失败。

## A 独立数值诊断：保留结论，但不冒充精确输入验收

执行：

```text
python -B review_stable_independent_r2.py <REVIEW_WORKTREE>/task-packages/PKG-B-ALG <A_OUT>/stable-independent-r2.json
```

脚本从全部 67,248 条 features 独立重算有效删频资格及分类，不直接信任原分类；随后在本机重新生成 26 组输入、复算 2,252 个同帧对照，并独立核查帧起止与接收活动区间。这里复用原估计器是为了复现，而非声称另行实现了一个独立算法。

- 范围外活动母体：12,312；错误 stable 候选：563；删频跨界：317；全部有效删频仍在范围内：246。
- 所选候选同帧 fresh：182；上一包整批范围外 fresh：205。没有重跑对照跟踪器，不能外推 HOLD 或延迟改善。
- 四组对照误入数：563 / 185 / 309 / 0；有效数：563 / 563 / 549 / 563；去反射的 14 个无效未计作正确。
- 全部重算类别无差异；最大候选诊断角度差异约 `8.2191e-11°`，对照方向误差差异约 `4.6760e-10°`，到允许轴夹角差异约 `1.0658e-13°`。
- 26 组中原 input/target 仅 11 组与历史哈希相同，15 组不同；noise 26/26 相同。全部输入/帧哈希及离散结果已记录。脚本结果明确标为 `NUMERIC_DIAGNOSTIC_ONLY_NOT_EXACT_INPUT_ACCEPTANCE`。

这些数值说明本机浮点路径变化尚未改变所检查的离散结果，但没有历史完整波形参考，不能反推输入逐样本相等或声称已证明输入差异很小。也不能将这批选定错误样本的回溯对照作为独立验证集成绩。

科学表述核查：原报告已区分“移除估计器频谱贡献”与“移除有效目标信息”，没有把稳定性等同于方向正确；对共同偏差与 5° 稳定阈值大于 2° 边界余量的解释与已核对证据一致。保留默认算法的决定继续合理。

## 给 B 的下一轮最小交付要求

无需重做已通过的日志、近零角度或历史 REVIEW 修复，也不要调整默认算法或分类阈值。只补齐 A 可执行的输入复现路径：

1. 优先提供在已验证支持环境导出、与现有历史哈希逐一绑定的参考数据及读取入口，覆盖四个 live audit 所需输入和 stable 的 26 组同帧对照。可先验证较小的 RIR/必要生成中间量参考是否足以使原 input/target/noise 哈希严格重现；若不足，再补足相应参考波形。不要只提供最终角度或把本机新波形重新命名为历史参考。
2. 或交付 A 实际可使用的匹配执行环境及完整命令。仅列作者 CPU 型号、Python/NumPy 版本，不足以使缺少 AVX512 的 A 机器获得该能力。
3. 若选择跨环境数值比较，必须有上述已绑定历史哈希的参考样本，分别报告波形绝对/相对误差、离散结果及合理容差，继续保留失败记录；不能简单关闭哈希断言、放宽到只看最终计数，或重写历史清单。
4. 新输出继续单独保存，原证据不覆盖。将修订推送同一 PR，并给出新 SHA、推荐复核入口和变更说明，A 再复核。

## 合入范围与限制

本轮 **不批准合入**，没有生成或推送 main 合并提交。仅实施本地未提交的试合并以核验兼容性。

复核通过后的潜在批准范围仍仅为六麦合成离线研究及其复现材料入库，不包括默认算法替换、四麦主线验证、实板、H2/H3 或完整算法包验收。此前 robustness-sweep-0.1 的批准不自动覆盖这六包。
