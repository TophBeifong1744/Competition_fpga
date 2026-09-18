# 四路完整 H3 候选（9/18，A 交 B 独立复核）

结论先行：本包把四路输入合同、存在门候选、定位/跟踪/DAS 的可执行软件整数 golden、因果音频时序、四路预算和 Skill 范围检查集中成一个可复现候选；但**不申请“完整 H3 PASS”**。存在门在现有 quiet 诊断上 61/61 帧均判有目标，且缺可信帧级真值、客观音频参考、AMD 全链位精确对照、集成周期/时序和实时输出证据。

状态：`AUTHOR_CANDIDATE_NEEDS_B_INDEPENDENT_REVIEW`。基线 `origin/main=5cfa02e51af44bb5c930babf732ddc864a1ab6cd`，包含 B 指定的 `21780c3`。返修父提交为 `be3a2ed20d123a37bf79650f3d6a1685fc5d8625`，任务分支 `task/member-a-0918-h3-closeout`；准确审查提交由该分支最新远端 HEAD 解析，不能只按分支名批准。本包不修改默认 PHAT、原 Tracker、旧录音、RTL、Vivado/Vitis 工程或两项 Skill。

## 一页复核入口

| 项目 | 本包事实 |
| --- | --- |
| 申请批准 | 四路 H3 软件候选材料、逐级整数 golden、预算和范围检查可进入限定评审；不申请完整 H3、默认算法替换、RTL/实时/板测通过 |
| 输入合同 | 4 路、48 kHz、signed24 装 int32 右对齐；`mic0..mic3`；1024/512；40 mm 共面正方形；方向为阵列指向声源，+X 到 +Y 为正角 |
| 软件整数链 | PCM→Hann→29 位前向 FFT 候选→S25 适配→PHAT→25 位 IFFT 候选→Q12 lag→Q20 DOA→Q8 角度→跟踪→整数线性 DAS；14 组数组和 lag/DOA/跟踪事件冻结并精确复算 |
| 存在门 | 阈值在真实标签评分前冻结；静音、低能量、错误、削顶及端点有测试；但现有 center/quiet 各 61 帧全部过门，说明该候选不能承担正式存在判定 |
| 实际输入 | 主线 center/quiet 只用于诊断，无可信帧级真值；新增 6.005208 s 四路连续输入在远端 `8f708e4`，待 B 单独复核，未复制或先行采用 |
| 三路音频 | 复用已限定批准的同录音单麦/手动+X/自动三路，时间基准与增益共同；复现入口会完整重跑。无独立目标/干扰参考，客观收益 `NOT_RUN` |
| 预算 | 四路每帧 4 FFT+最多6 IFFT；两项历史 OOC 测试槽相加 73900 周期/配置100 MHz，不能当一个混合位宽整链实测；保守未复用缓存清单 91080 B |
| Skill | 两项活动目录自准确批准 SHA 后无变化；SKL-001仍是模块仿真限定，SKL-002仍是离线 static/mock，真实 PYNQ `NOT_RUN` |
| 复现 | 下方一条命令，新输出目录，前后校验 18 份上游输入；不覆盖任何旧结果 |

## 结果摘要

- run04 新候选 37 项 H3 单元测试通过：包括整数 Q12 边/对角 lag 的正负边界内、边界上、边界外，以及五帧捕获前单麦回退、fresh、HOLD/到期、断流、切换淡变和“manual/automatic 错做同一数组”的反例。
- `evidence/run04/golden/` 的合成宽带 +X 向量通过全链：DOA `ux_q20=1123531`、`uy_q20=0`、角度 `0°`，五帧后进入 LOCKED；19°切换与70°拒绝是另行注入的控制向量，不是声学精度样本。
- 14 组数组及 lag、DOA、跟踪状态/事件和音频时序均由独立检查器与作者冻结结果精确比较。第五帧方向在样点3072算出，样点3080可用于发声，3081才有首个非零波束权重；此前自动路与单麦相同，不能回填未来角度。
- 真实诊断：center 61/61、quiet 61/61 都通过当前能量门；center 数值候选36帧、fresh21帧，quiet数值候选35帧但fresh0帧。后者是允许扇区挡住了方向，不是存在门成功，也不能推出误输出率。
- 预算重算：4×7366 + 6×7406 = 73900 个历史测试调度周期；100 MHz 配置下算术为0.739 ms。PHAT、lag、DOA、DAS、DMA、切换、背压仍只有公式，没有整链实测。
- `evidence/run01/` 保留方向符号首错；`run02/` 保留秩不足覆盖问题；`run03/` 除获授权移出的单个含私密绝对路径作者复现记录外仍保留原件，原记录可由父提交与仓库外只读备份恢复，见 `evidence/run04/PRIVACY-AND-HISTORY.md`。本次返修证据只写 `run04/`。

## 复现

在仓库根目录，以 Python 3.12 + NumPy 2.3.5 运行，输出目录必须不存在：

```powershell
python -B task-packages/PKG-B-ALG/tasks/h3-complete-20260918/source/reproduce.py --repo . --out ../h3-review-new-run
```

运行环境为 Python 3.12 + NumPy 2.3.5；如本机 `python` 指向其他环境，请把命令中的 `python` 换成符合版本的解释器。该命令先验任务包清单，前后按 Git blob/LF 合同校验 18 项上游输入，运行37项新测试，生成并与冻结 run04 逐级比较整数 golden，执行真实输入诊断、预算/Skill检查，再经原批准入口复跑三路音频50项检查。输出目录必须不存在，禁止覆盖旧运行。状态仍是作者复现，不是 B 独立批准。

## 文件导航

- [HANDOFF.md](HANDOFF.md)：给 B 的范围、差异、命令和结论。
- [H3-ADMISSION.md](H3-ADMISSION.md)：可准入、限制、阻断和9/23后续。
- [REAL-INPUT-STATUS.md](REAL-INPUT-STATUS.md)：主线与待审新实录的准确身份。
- [SKILL-SCOPE-CHECK.md](SKILL-SCOPE-CHECK.md)：9/18两项 Skill 增量范围检查。
- `config.json`：输入、几何、存在门、数制和跟踪合同。
- `inputs.json`：18份上游文件SHA-256及待审外部输入版本。
- `PACKAGE-SHA256.json`：除自身外全部任务包文件的字节数和SHA-256，可由 `source/seal_package.py --verify` 核对。
- `source/`、`tests/`：模型、检查器、预算、单命令复现和测试。
- `evidence/run04/`：返修后的冻结结果、检查与脱敏复现摘要；`run01/`、`run02/`、`run03/`保留可恢复历史，具体隐私例外见 run04 说明。
- [WORK-EXECUTION-REPORT.md](WORK-EXECUTION-REPORT.md)：逐项给“拓芙工作执行”的完成/阻断报告。

## 不得扩大的结论

本包不证明目标存在门有效、方向 P50/P95、有效输出率、错向率、SNR/SI-SDR/音频收益、AMD 全链 bit-exact、完整 RTL、整板资源时序、持续实时、板端音频、M1、真实 PYNQ、完整 H3 或 V1。B 应按 [REVIEW-PROMPT.md](REVIEW-PROMPT.md) 在干净检出中独立复核后裁决准确范围。
