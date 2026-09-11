# A：2026-09-10 20:00 阶段复盘证据摘要

性质：接口与已有工程成果复盘，不是完整 M0、四路 H2 或 H3 验收。本轮只查记录并汇总，不重跑实验、不改工程、不提交推送；不代表会议已经召开或 B 已签署。

## 1. 检查版本与来源

- 本次共享工作区 HEAD：9878ccafdda6cd5a522cc9de95c1277bcee70f08，包含他人未提交增量。已读 docs/current-status.md、work-packages.md、phase-review-2026-09-10.md 及 project-plan.md 统一日历，不以旧 README 覆盖新状态。
- 单麦发布：93a12aab1eb5d2e70e118761a35d2d654845424b，分支 codex/toph/mono-diagnostic-delivery；合并：6647eb8acfceb5734f02f475168e5d09371c8f38（PR #6）。本轮在 C 发布副本直接读取该合并提交：C:/Users/Toph Beifong/.codex/visualizations/2026/09/08/01a0811f-97d1-7e00-baba-38cf26de948d/c-review-002。未联网刷新，不能据此声明远端当前 HEAD；共享工作区缺文件不等于未交付。
- 单麦包：上述副本的 task-packages/PKG-A-H2-MONO-DIAGNOSTIC/。原件另在 C:/Users/Toph Beifong/.codex/visualizations/2026/09/09/01a086de-c5a0-7ee2-b46c-c0bd5b6d3dfd/PKG-A-H2-MONO-DIAGNOSTIC/，本轮未搬动或回写。
- A 独立复算与工程补证已随发布包 publication/ 归档；工程原件位于 C:/Users/Toph Beifong/.codex/visualizations/2026/09/05/01a06ff9-0287-7e00-b73d-abf12e6b3035/mono_acceptance_20260910/ 及相邻 mono_closeout_20260910/。

## 2. 今晚可展示及通过范围

**H1 软件约定完成，不再重做。** [A/B 确认](../../REVIEW.md)绑定 ss-data-draft-0.3 同一清单 SHA-256：ef09838face445cc4f2a87d56245ad64574fa3e9f4d12032e4b0723a7f1eca96；B 审核对象 5f0dc36fce2328ade672dd949778bc5a91f506dc。既有七文件哈希/大小及两个样例检查通过。四通道顺序、坐标、格式、编号、配置和错误语义已有软件约定，实物映射、坐标与实际采样参数仍按暂定项记录。

实际工程入口：F:/College/verilog_digital_system/AMD/Competiton/one/one.xpr；PS 工作区 F:/College/verilog_digital_system/Vitis/。当前可审计对象是发布包中的采集后快照，不推定上述活动目录此刻与快照完全相同。

单麦路径：麦克风 DATA → single_mic_top 同步/采样 → pdm_cic3（CIC3/R64）→ pcm_capture_axis（编号/标志/FIFO/分包）→ AXI DMA S2MM → PS DDR/缓存处理 → JTAG 导出 BIN → 独立单麦 CSV/metadata/WAV 检查。配置 PL 61.44 MHz、PDM 3.072 MHz、PCM 48 kHz；不是实测频率。

配置标识 mono-capture-v1；串口转录 build Sep 10 2026 14:48:35。准确采集后文件 SHA-256：

| 对象 | SHA-256 |
|---|---|
| single_mic_top.v | 47cfa7f59ab3a1fa1c52ee502133ed03dd32da5f76d29faa5101a131d9f8448c |
| main_mono_capture.c | c8dcf209829c45a3aeb27e4e2ef1f627a8419c15ec21a1777d76af65ac382034 |
| bit | ef73331e9a699a5b65fe3ee04b0b0914df2c3f1fbaa37055c7e09681f37576c5 |
| ELF | 2c4b0e0f17ae65c4ca586cb6c9e7d5baac25d0f325b06cf2a7001e11ab89fd6e |
| XSA | e1cf7b504d637860eee5c6b1a6cd8a5b5d022f6b09858d63c61500776dd15d46 |

这些是快照身份，不倒推实际加载身份；完整源码列表及哈希在原 snapshot-manifest.json 和数据 metadata 中。历史教学码型/test_source 不冒充麦克风输入；snapshot 内存在参考文件不证明其处于实际声学路径。

| 录音 | 原始编号 | 已有检查 |
|---|---|---|
| quiet_03 | 14223～62222 | 48000 条、768000 字节；FNV EFFF882A |
| music_04 | 13352～61351 | 48000 条、768000 字节；FNV C7762DD9 |

两段各自连续、flags 全零，BIN/原幅度 WAV/CSV 一致；A 曾独立复算原件，上传前重跑 10 项测试、41 项原包哈希，70 个包内暂存文件字节一致。以上引用既有记录，本轮没有再次运行。串口是用户粘贴转录；用户试听歌曲较清楚，无明显嗡声/断续/失真，未指定具体 WAV/增益，不能当客观音质指标。

整机单麦实现报告已有 WNS 5.319 ns、WHS 0.041 ns，但 no_input_delay=1/no_output_delay=1，不能声称外部 IO 已闭合。低频及启动偏置原因未明；本轮不加高通/FIR掩盖，也不要求重录已有两段。

## 3. B 待确认与其他待审交付

已检查本机任务列表、当前主流程记录及发布副本的 DELIVERY-REVIEW；未定位 B 对新单麦包的明确读取/诊断结论，标为**待 B 确认**，不是断言 B 没做。PR 合并不替代其技术结论。

B 从单麦包根目录运行：

```text
python -B source/file_manifest.py verify
python -B source/mono_delivery.py verify
python -B source/test_delivery.py
```

请 B 回传实际提交、运行输出、问题和接收结论。该包是 ss-mono-diagnostic-0.2，只供单麦诊断，不补列凑四路，也不输入六麦定位。完整四路 H2 尚缺。

| A 交付 | 准确提交/分支 | 已有结果与限制 |
|---|---|---|
| FFT 候选 | ac0ff38e954dac094fd84e28b329dcb24dded7fb；codex/toph/fft-ip-budget-01 | 1024 点共享 FFT、100 MHz 候选；22 次变换/22528 个复输出，OOC 1292 LUT、2148 FF、6 DSP、6 RAMB18；待 B 复核，不是整板布局布线或位精确链通过 |
| H3 工程约束 | 794ca230d11dfde980b9446b9ff8fd6a981e7c14；codex/toph/h3-fpga-integration-constraints | task-packages/PKG-A-H3-INTEGRATION/；执行任务报告 47 项来源哈希、11 项测试及历史 FFT 复算通过；本轮仅核对提交身份，未重跑；待 B 复核 |
| DDR 五模式 | 9c3301e2a8564d454fa9a3d2b034334f18fbe055；codex/toph/pkg-a-acq | 三轮通过为用户报告，逐轮原日志/加载身份不足，未定位新的正式复核，不重测或补造 |
| DDR/DMA 任务一至三 | 4bfaeb36977ea61201b6b78803351cdb9cc9d239；codex/toph/ddr-dma-delivery | 接口 TB 与数字码型/DDR 导出证据已发布，不能当声学录音或完整长稳通过 |

H3 包入口：payload/H3-CONSTRAINTS.md、payload/B-SUBMISSION-CHECKLIST.md；仓库根运行 python -B task-packages/PKG-A-H3-INTEGRATION/source/verify.py --out h3-constraints-review-run01（选择未存在输出目录）。100 MHz FFT 候选不等于现有 61.44 MHz 整机已准入；首次五帧 64 ms 不等于刷新 50 ms。端到端音频硬上限和整机 DSP/BRAM 仍未知，B 可继续软件预算，不等待硬件补证。

## 4. 最小缺口与补检安排

**用户已明确今晚可使用实验室的万用表/示波器，不能继续写“仪器不可用”。** 实际测量尚未发生，具体开始时刻/操作单批准待定；不自动安排今晚必须完成，更不把这些后续门槛追溯为今晚短复盘失败。

| 缺口 | 已有依据 / 尚缺 | 负责人、条件与时间 |
|---|---|---|
| 模块 VDD | 资料/接线候选已有；缺安全测点下实测读数 | A 技术判断，用户按单测，C 可协助；万用表、明确 VDD/GND 测点；仪器今晚可用，补检时刻待定 |
| PL Bank 电压 | Bank 13 资料与选择电阻依据已有；不能代替 VCCO 实测 | A/工程任务核对测点，用户按单测；万用表，不探 BGA、不盲夹地；时刻待定 |
| CLOCK/DATA 外部时序 | 配置分频、名义采样窗口及内部实现报告已有；缺外部时序闭合依据与波形核对 | A/工程任务给安全操作单和分析，用户操作示波器；CLOCK/DATA/GND 确认及探头接地安全；时刻待定 |
| 实际加载关联 | bit/ELF/XSA/init 快照哈希与部分文件一致性已有；缺加载时记录 | A 固定版本与记录方式，用户在后续必要运行时记录确切加载文件和日志；不补造旧记录、不为今晚复盘重复录音；时刻待定 |

这些缺口限制相应电气/实板完整批准，不阻塞 B 读取已有数据或离线预算；暂无新事实证明必须重录原件。本轮不扩四麦、不改变正式分工。后续 RTL 指导统一引用 docs/rtl-language-and-bd-integration.md（rtl-bd-policy-1.0），不翻写历史核心。

## 5. 今晚建议判定

**A 的接口与工程起步成果已具备展示条件；H1 完成，单麦诊断材料已归档，接收/技术复核待收口。** 建议与主流程一致记“阶段推进有效、关键交接待收口”，不签完整 M0、四路 H2、H3 或全包通过。

下一步：B 留下单麦接收/读取反馈并复核 FFT/H3 约束；A 确定上述最小补证操作单与时间。下一计划检查日为 9 月 16 日，具体补检时间不虚填、不自动顺延 10 月 7 日目标。此次只新增本目录汇总文件，不修改主流程状态文档。
