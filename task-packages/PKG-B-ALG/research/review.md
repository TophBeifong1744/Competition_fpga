# A 侧六麦离线研究第三轮复核

日期：2026-09-09。执行者：Codex（A 侧独立复核辅助，不冒充新增人类签字）。

结论：**通过，允许按下述范围合入 main**。本轮在 A 实际 Intel 环境关闭剩余历史输入复现阻断，独立集成回归全部通过；此前失败记录继续保留。

## 对象、范围与隔离

- PR：<https://github.com/TophBeifong1744/Competition_fpga/pull/3>
- 审核提交：`6491d1bab04038b71fdd8c22d45a58455aa58ade`。
- 上轮提交：`df4146af6aab3263209f54bb36ded8693d2d9d90`。
- 集成 main 基线：`6ea647d5a9b6d27b164fde4c78103d50e5d1e43e`。
- 独立原提交工作区：`E:/Users/Toph Beifong/Documents/GitHub/ss-review-r3`。
- 独立集成工作区：`E:/Users/Toph Beifong/Documents/GitHub/ss-review-int-r3`。
- A 原始输出目录：`C:/Users/Toph Beifong/.codex/visualizations/2026/09/09/01a0854e-8b0a-77c3-8e6c-71c465950deb`。

相对上轮仅新增 `revisions/pr3-input-reference-02/` 下 71 个文件；前两轮代码、原始六包、默认 PHAT、跟踪器及其他成员成果未修改。所有计算输出写入独立 A 目录，未覆盖 B 提交中的原始证据。前两轮请求修改仍保留在 PR 及本地历史报告中，本轮结论不抹除历史失败。

## 本轮剩余阻断已在 A 的实际 Intel 环境关闭

A 使用 Windows 11、CPython 3.12.14、NumPy 2.3.5、Intel Family 6 Model 183，支持 AVX2/FMA3，不支持 AVX512；没有设置哈希绕过或关闭断言。完整环境及二进制哈希见 `review-r3-intel01/environment.json`。

在任务包根目录运行：

```text
python -B revisions/pr3-input-reference-02/verify_release.py
python -B revisions/pr3-input-reference-02/test_reference.py
python -B revisions/pr3-input-reference-02/run_all.py --out <A_OUT>/review-r3-intel01
```

三条命令均退出 0。新清单 70 项、20 个 RIR 参数键、86 个用途绑定、原 633 个冻结路径通过；新增 7 项机制测试通过。12 个 NPZ 仅含无损 float64 RIR，总计 6,205,843 字节，容器文件哈希与数组哈希分别校验。导出来源、参数/清单绑定和元数据已检查。

新入口只替换复核进程的 RIR 数据来源，混合、目标、噪声及 RIR 的历史 SHA-256 检查仍严格保留；损坏文件、仅重算容器哈希、未声明参数、混合输入不匹配等负例测试已通过。不是关闭旧断言，也不是按最终计数相等放行。

| A 实际执行阶段 | 结果 |
|---|---|
| 参考输入预检 | 86/86 用途绑定的 input/target/noise/RIR 四类历史哈希严格匹配 |
| narrowband live audit | 通过，重建 10 项输入 |
| subband live audit | 通过，重建 8 项输入 |
| leave-band-out live audit | 通过，重建 8 项输入 |
| effective live audit | 通过，重建 8 项输入及规定频谱抽查 |
| stable 完整重跑 | 通过，26 组、2,252 个同帧对照 |

86 是用途绑定数，并非 86 个独立试验。旧入口仍保留原行为；在 A 机器复现应使用本轮参考数据入口，不得从新入口通过推断旧的原生 RIR 生成已跨 CPU 字节一致。

## 核心结论与独立复算

除运行 B 的新入口，还执行 A 自有 `review_stable_independent_r3.py`：从 67,248 条 features 独立重算有效删频资格及分类，重新选出候选；使用已验证 RIR 重建输入，再复算同帧对照。估计器复用原实现，资格、候选计数、帧起止及接收活动区间独立检查。

```text
python -B review_stable_independent_r3.py <REVIEW_WORKTREE>/task-packages/PKG-B-ALG <A_OUT>/stable-independent-r3.json
```

- 范围外活动母体 12,312；错误 stable 候选 563；删频跨界 317；全部有效删频仍在范围内 246。逐帧分类无差异。
- 所选候选同帧 fresh 为 182；上一包整批范围外 fresh 为 205；没有混淆候选、fresh 与 HOLD。
- 26 组原输入四类历史哈希均严格一致，原 input/target/noise 均为 26/26；上轮 15 组输入不一致的问题已关闭。参考预检另覆盖 26 组对应 dry 输入。

| 同一批 563 个候选的对照 | 有效数 | 仍误入范围 | 误入且 stable |
|---|---:|---:|---:|
| 原输入 | 563 | 563 | 563 |
| 去噪声 | 563 | 185 | 130 |
| 去反射 | 549 | 309 | 297 |
| 同时去掉两者 | 563 | 0 | 0 |

去反射的 14 个无效候选未计为正确。全部 2,252 条对照的帧编号、活动区间及离散结果通过检查，逐帧哈希保存在 A 独立结果中。

数值差异与字节差异分开记录：独立复算最大诊断角度差异约 `8.2191e-11°`，对照方向误差差异约 `4.6760e-10°`，到允许轴夹角差异约 `3.1974e-14°`。B 新入口逐字段有界数值比较通过，离散字段精确一致；新生成 cohort/controls/summary 三个 JSON 均与历史文件字节不同。这不影响本轮数值复现结论，也不应写成文件字节全部一致。

机制解释仍成立：对指定删频不敏感不等于方向正确；有效频谱贡献移除不等于移除语义有效目标信息；共同偏差及稳定门限大于边界余量可使错误持续稳定。本研究为选定错误样本的回溯对照，不是独立验证集性能，不证明整批误输出或捕获延迟改善。保留原默认 PHAT 的决定合理。

## 集成回归

从上述最新 main 在独立工作区执行 `git merge --no-commit --no-ff 6491d1bab04038b71fdd8c22d45a58455aa58ade`。无冲突，main 既有文件没有修改或删除，根 `REVIEW.md` 与 main Git blob 逐字节一致；没有覆盖其他成员成果或撤销 A 历史评审。

执行 A 自有回归脚本：

```text
python -B review_integration_r3.py <INTEGRATION_WORKTREE> <A_OUT>/integration-r3
```

集成完整回归状态：全部通过，退出码 0。六组回归依次 170、172、173、173、173、172 项，另有上一修订机制 7 项、本轮参考机制 7 项，五个 final 以及新版预检、四个 live audit、stable 全部通过。六组重复包含原 167 项，不将其相加宣传为独立测试总数。

所有具体命令、退出码、环境和输出保存在 `research/a-review-20260909-r3/`，包括 `review-r3-intel01/`、`integration-r3/`、`stable-independent-r3.json` 及 A 复算源码。

## 批准范围及限制

允许合入六麦合成离线研究六包（tonal-edge、narrowband-guard、subband-confidence、leave-band-out、effective-perturbation、stable-wrong）及其两轮复现修订、A 侧复核证据。允许路径仅为 `task-packages/PKG-B-ALG/research/`、`task-packages/PKG-B-ALG/revisions/` 与 `task-packages/PKG-B-ALG/PR3-REVISION.md`。最终合并 SHA 以交付消息及 Git 记录为准。

不批准默认算法替换、四麦主线验证、实板、RTL/时序、H2/H3 或完整算法包验收。前五包运行适用审计和规定输入子集，不冒称已重跑全部声学试验；stable 的 26 组对照则已完整重跑。对其他机器仍须运行严格预检；本次 Intel 通过不代表所有环境自动通过。
