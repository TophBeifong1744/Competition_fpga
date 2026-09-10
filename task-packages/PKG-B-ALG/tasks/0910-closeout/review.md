# A 复核结论：9.10 阶段复盘与单麦诊断接收

结论：**通过，批准范围仅为阶段复盘、单麦文件/数值诊断接收及其证据归档。** 下列澄清是本次批准的一部分；不批准完整 H2/H3、全链定点、资源时序或实板验收。

## 1. 固定版本与完整检查范围

- 原交付：`146736bf692d10fcfe0a95e8ffd7e16a0d4b4120`，父提交 `464d7fc80e2b136115994197a342fb63a46c0146`。
- PR #8 审核入口：`785e9abfb1f594844070a109e0bf81792b849d6b`，分支 `task/member-b-0910-closeout`。它只新增 REVIEW-REQUEST.md，不能替代原交付审核。
- 审核时远端 main：`70d70b4657f571c903ae7faac9b78cadbb2e44b3`；原交付确已在 main。Git 合入与技术批准分开，本记录才是本次 A 的限定技术结论。
- 在独立工作区 `E:/ss-pr8-review-01` 先固定 PR 入口，再切到原交付 SHA 复跑，结果写入全新 `E:/ss-pr8-repro-01`。没有删除或重用旧 run01。
- 已检查原提交全部 15 文件；`a-review-01/evidence/review-result.json` 列出逐文件 SHA-256，全部与原提交 Git blob 相同。大文件 inputs.mem 按字节与新生成输入比对，reference.json 按完整数值结构及字节检查，不以人工逐行阅读代替数据校验。

15 文件覆盖：.gitattributes、RECAP.md、check.py；run01 下 export/h3/manifest/tests.txt、result.json；h3 下 calculations.json、fft.txt、result.json、tests.txt；h3/fft 下 check.json、vectors/inputs.mem、vectors/reference.json。另读 PR 的 REVIEW-REQUEST.md，并交叉核对 A 侧单麦源码/导出协议、H1 确认、预算限定批准和 H3 约束记录。

## 2. 实际命令与结果

Python：`C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`，3.12.14。

本轮复现入口（脚本现归档为 a-review-01/reproduce.py）：

```text
python -B pr8_reproduce.py --repo E:/ss-pr8-review-01 --out E:/ss-pr8-repro-01
```

其中原交付副本的单麦包目录分别执行：

```text
python -B source/file_manifest.py verify
python -B source/mono_delivery.py verify
python -B source/test_delivery.py
```

仓库根执行：

```text
python -B task-packages/PKG-A-H3-INTEGRATION/source/verify.py --out E:/ss-pr8-repro-01/h3
```

以上四入口退出码均 0。精确解释器路径、工作目录和参数见 review-result.json。额外执行原 check.py 时，因旧 evidence/run01 存在而得到预期 FileExistsError/退出码1；随后 git diff --exit-code 通过，原证据未改写。这不是测试失败，也未删除目录重试。

| 复核项 | 实际结果 |
|---|---|
| 单麦原清单 | 41 文件哈希通过；publication 增量不在此清单内，仍靠 Git 提交绑定 |
| 单麦导出与负例 | 两份导出通过、10 项测试通过，包括截断、校验、符号、编号跳变/进位及错误标志 |
| A 独立读取 | int.from_bytes 解 BIN，独立 CSV 解析，96,000 行逐样本一致；不调用 B 的 struct 统计过程 |
| H3 归档验证 | 47 份来源哈希、11 项算术/边界测试通过，FFT 历史复算通过；不是新 XSim/综合 |
| 原交付保护 | 全部 15 文件运行前后哈希不变，与提交 blob 一致 |

独立复算全部 mono_records 字段通过。均值/平方和从整数计算，AC RMS 用 E[x²]-E[x]² 交叉复算，浮点比较绝对容差 1e-7、相对 1e-10；离散量及哈希严格相等。

| 记录 | 数量 / 首尾 ID | PCM 最小/最大 | 均值 / RMS | 检查 |
|---|---|---|---|---|
| quiet_03 | 48000 / 14223–62222 | -23616 / 26176 | 1048.921333 / 8215.301252 | gap、非零 flags、signed24 越界、端点削顶均 0 |
| music_04 | 48000 / 13352–61351 | -18816 / 28288 | 1353.454667 / 7702.573808 | 同上均 0 |

全部样本为 32 的整数倍；两份峰值相对 2^23 为 0.00312042236328125、0.0033721923828125。首/尾 4800 点均值与原报告一致。它们仅是记录中的数值现象，不能推出真实 SNR、音质、增益正确或原因已查清。两次 ID 属独立捕获，不拼接成同一连续时间轴。

### 字节与数值差异

本轮新 export.txt、h3/result.json、h3/calculations.json、h3/fft/check.json、FFT reference.json 与 **B run01 对应文件**数值/语义一致且字节一致；FFT inputs.mem 字节一致。测试日志运行时长与主机路径不要求逐字节相等，测试名称、数量、状态一致。

H3 result 中 `budget_bytes_equal=false` 仍正确：它比较的是 H3 包更早的 calculations.json 与规范化重算输出，不是比较本轮 A 和 B 的两份重算输出。不得把这两个比较对象混为一谈。完整比较记录见复核 JSON。

## 3. 批准范围与补充澄清

1. `93a12aab1eb5d2e70e118761a35d2d654845424b` 的单麦目录与原复盘基线无差异，PR #6 的 `6647eb8` 是合入记录。单麦文件接收无阻断，但来源仍为 user-reported-hardware-audio；48 kHz 是配置值，加载身份未绑定。零 flags 不排除未观测硬件错误，不能扩为完整四路 H2。
2. H1 的 A 共同确认确在 PKG-A-ACQ/REVIEW.md 顶部；不应再次要求签同一软件确认。它不确认实际四路映射或多路采集。
3. input-boundary-adoption-01 仅按 `80a7b929fa6ec072b1ad41d566c8f2067a5231e2` 的限定目录，经 `9878cca` 导入。另五个任务包 126 文件仍不在该批准内；原复盘基线的 B tasks 实际只有本复盘和输入边界目录。
4. RECAP 的“合后172测试”不应解读为六个研究包统一总数。准确历史来源是 `PKG-B-ALG/research/review.md`：六组依次 170、172、173、173、173、172 项，重复含原167项，不能相加宣传独立测试数。本轮未重跑这些研究。
5. RECAP 所述 fft-bitexact-01、fft-window-02、phat-fixed-03 及其新 XSim/C 模型比较，是 **B 作者报告的本机、未发布进展**。本 A 环境无其所列 F:/NUEC 工作树，故本轮不确认这些未交付文件的具体结果，更不批准它们。它们可以留在复盘的作者自测栏，不得作为 A 批准 ac0ff38 的证据。
6. FFT `ac0ff38e954dac094fd84e28b329dcb24dded7fb` 和 H3 `794ca230d11dfde980b9446b9ff8fd6a981e7c14` 可作下一轮研究输入，但不是本轮正式批准其全部内容。H3 目录与 794ca23 无差异，PR #7 合入 `464d7fc` 不替代技术复核；包内尚是待 B 复核，本轮没有发现另行正式 B 结论。A 不代签 B。
7. 61.44 MHz 采集域与100 MHz FFT候选、64 ms首次捕获与50 ms刷新、未知音频端到端目标及整机资源额度的区分均保留。仍需 A/B 明确 CDC/调度、音频路径、异常与资源账本，不能用单核报告闭合这些事项。
8. 原 RECAP 的“尚未提交或推送”是生成时状态，由 REVIEW-REQUEST.md 修正为已入库待复核；原文和原始证据不改写。9月11日及2–4小时是当时计划，不是承诺完成或自动验收。本次没有创建提醒或自动任务。
9. 审核时 main 已新增 `70d70b4` 电气证据整理，发生在原复盘之后；本轮不复核该增量，也不据其自动关闭电气/外部IO或实板门。RECAP 是固定历史快照，不替代最新主台账。

## 4. 合入决定

同意合入 PR #8 的复核入口及本次 A 补充记录/复现脚本/结果。原 146736b 已在 main，不重复导入、不回退或重写历史。批准仅覆盖该原提交15文件作为限定复盘与诊断记录，以及本次补充；不批准未发布研究、默认算法替换、完整四路 H2、完整 H3、全链定点、资源时序或实板通过。

复核执行：A 的 Codex 助手，依据本次用户授权；不是 B 作者自批。最终合并 SHA 由 Git 合并记录和交付回复给出，不在提交内自引用。
