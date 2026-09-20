# 四路完整 H3 候选（9/18，A 交 B 独立复核）

结论先行：B 已退回上一版，因为断流未进入 automatic 音频链；run05 已把该 tracker 输出接入同一控制时间线，并冻结可复核反例。**本包仍不申请“完整 H3 PASS”，run05 也尚待 B 增量独立复核。**存在门在 quiet 诊断上 61/61 帧均判有目标，且缺可信真值、客观音频参考、AMD 全链位精确对照、集成周期/时序和实时输出证据。

状态：`AUTHOR_CANDIDATE_NEEDS_B_INDEPENDENT_REVIEW`。建分支时的主线/共同祖先为 `5cfa02e51af44bb5c930babf732ddc864a1ab6cd`，包含 B 指定的 `21780c3`；发布核对时远端 main 已前进到 `bff9369a5c7f166344c02095df61e91e1c2f4681`，本返修按原任务分支追加而未改写历史、未合并新 main。返修父 `be3a2ed20d123a37bf79650f3d6a1685fc5d8625`；源码/冻结证据提交 `74306d036ae329a687f24ab8d153c3e2f4375189`；交付分支 `task/member-a-0918-h3-closeout`。发布状态为任务分支非强制推送、作者干净检出复跑通过，最终交付 SHA 由发布回报给出并要求本地/跟踪/远端三方相等；Git 提交无法在自身内容中嵌入自己的 SHA。本包不修改默认 PHAT、原 Tracker、旧录音、RTL、Vivado/Vitis 工程或两项 Skill。

本轮增量身份：B退回的准确提交为 `7ea3de519c1f86832fcb03fc8d852606273a8f8a`；断流修复与run05冻结证据提交为 `cef9c61a6a9aac8e8f0b0d38d56bb82981106d1a`。上段 `74306d...` 是上一轮源码提交，不是本轮评审SHA；最终远端HEAD须以交付消息及B现场核对为准。

## 一页复核入口

| 项目 | 本包事实 |
| --- | --- |
| 申请批准 | 四路 H3 软件候选材料、逐级整数 golden、预算和范围检查可进入限定评审；不申请完整 H3、默认算法替换、RTL/实时/板测通过 |
| 输入合同 | 4 路、48 kHz、signed24 装 int32 右对齐；`mic0..mic3`；1024/512；40 mm 共面正方形；方向为阵列指向声源，+X 到 +Y 为正角 |
| 软件整数链 | PCM→Hann→29 位前向 FFT 候选→S25 适配→PHAT→25 位 IFFT 候选→Q12 lag→Q20 DOA→Q8 角度→跟踪→整数线性 DAS；run05 冻结14组数组、lag/DOA/跟踪及断流事件，并直接检查 automatic PCM |
| 存在门 | 阈值在真实标签评分前冻结；静音、低能量、错误、削顶及端点有测试；但现有 center/quiet 各 61 帧全部过门，说明该候选不能承担正式存在判定 |
| 实际输入 | 主线 center/quiet 只用于诊断，无可信帧级真值；新增 6.005208 s 四路连续输入在远端 `8f708e4`，待 B 单独复核，未复制或先行采用 |
| 三路音频 | 复用已限定批准的同录音单麦/手动+X/自动三路，时间基准与增益共同；复现入口会完整重跑。无独立目标/干扰参考，客观收益 `NOT_RUN` |
| 预算 | 四路每帧 4 FFT+最多6 IFFT；两项历史 OOC 测试槽相加 73900 周期/配置100 MHz，不能当一个混合位宽整链实测；保守未复用缓存清单 91080 B |
| Skill | 两项活动目录自准确批准 SHA 后无变化；SKL-001仍是模块仿真限定，SKL-002仍是离线 static/mock，真实 PYNQ `NOT_RUN` |
| 复现 | 下方一条命令，新输出目录，前后校验 18 份上游输入；不覆盖任何旧结果 |

## 结果摘要

- run05 作者39项 H3 测试通过。新断流反例在旧实现上退出码1、报 `StopIteration`，原始首错日志在仓库外只读保存，脱敏副本与原哈希见 `evidence/run05/README.md`。新增数组篡改负例覆盖目标bank、Q12权重与automatic PCM。
- `evidence/run05/golden/` 的合成宽带 +X 向量仍得到 DOA `ux_q20=1123531`、`uy_q20=0`、角度 `0°`；19°切换、70°拒绝及1441样点断流均为注入控制向量，不是声学精度或实板断流样本。
- 断流发生在tracker样点4513，结果在共同延迟8样点后的4521进入 automatic；目标bank切回0并清空旧TTL，随后480样点淡变。4522权重为 `[9,4087,0]`，5001已等于单麦。第五帧3072方向仍只能自3080起使用，不回填未来角度。14组数组与冻结状态/事件逐级比较。
- 真实诊断：center 61/61、quiet 61/61 都通过当前能量门；center 数值候选36帧、fresh21帧，quiet数值候选35帧但fresh0帧。后者是允许扇区挡住了方向，不是存在门成功，也不能推出误输出率。
- 预算重算：4×7366 + 6×7406 = 73900 个历史测试调度周期；100 MHz 配置下算术为0.739 ms。PHAT、lag、DOA、DAS、DMA、切换、背压仍只有公式，没有整链实测。
- `evidence/run01/` 保留方向符号首错；`run02/` 保留秩不足覆盖问题；`run03/` 的隐私例外见 `run04/PRIVACY-AND-HISTORY.md`；被B退回的 `run04/` 原样保留。此次断流增量证据只写 `run05/`。

## 复现

在仓库根目录，以 Python 3.12 + NumPy 2.3.5 运行，输出目录必须不存在：

```powershell
python -B task-packages/PKG-B-ALG/tasks/h3-complete-20260918/source/reproduce.py --repo . --out ../h3-review-new-run
```

运行环境为 Python 3.12 + NumPy 2.3.5；如本机 `python` 指向其他环境，请换成符合版本的解释器。命令先验包清单，前后按 Git blob/LF 合同校验18项上游输入，运行39项测试，生成新 golden 并另与提交中的 run05 冻结值逐级比较，执行真实输入诊断、预算/Skill检查，再经原批准入口复跑三路音频50项检查。输出目录必须不存在。状态仍是作者复现，不是 B 独立批准。

## 文件导航

- [HANDOFF.md](HANDOFF.md)：给 B 的范围、差异、命令和结论。
- [H3-ADMISSION.md](H3-ADMISSION.md)：可准入、限制、阻断和9/23后续。
- [REAL-INPUT-STATUS.md](REAL-INPUT-STATUS.md)：主线与待审新实录的准确身份。
- [SKILL-SCOPE-CHECK.md](SKILL-SCOPE-CHECK.md)：9/18两项 Skill 增量范围检查。
- `config.json`：输入、几何、存在门、数制和跟踪合同。
- `inputs.json`：18份上游文件SHA-256及待审外部输入版本。
- `PACKAGE-SHA256.json`：除自身外全部任务包文件的字节数和SHA-256，可由 `source/seal_package.py --verify` 核对。
- `source/`、`tests/`：模型、检查器、预算、单命令复现和测试。
- `evidence/run05/`：B退回后的断流修复、首错日志、冻结结果与检查；`run01/`～`run04/`保留旧历史，具体隐私例外见run04说明。
- [WORK-EXECUTION-REPORT.md](WORK-EXECUTION-REPORT.md)：逐项给“拓芙工作执行”的完成/阻断报告。
- `evidence/run04/AUTHOR-VALIDATION.md`：作者复跑、首次失败与脱敏日志摘要；完整原始日志由 B 在其独立检出自行保存。
- `evidence/run05/README.md`：本轮首错原始日志哈希、脱敏副本、4513/4521时序与新冻结证据。

## 不得扩大的结论

本包不证明目标存在门有效、方向 P50/P95、有效输出率、错向率、SNR/SI-SDR/音频收益、AMD 全链 bit-exact、完整 RTL、整板资源时序、持续实时、板端音频、M1、真实 PYNQ、完整 H3 或 V1。B 应按 [REVIEW-PROMPT.md](REVIEW-PROMPT.md) 在干净检出中独立复核后裁决准确范围。
