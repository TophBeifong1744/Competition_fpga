# 四路诊断采集：首轮 RTL 与导出自检

## 2026-09-12 当前入口（覆盖以下历史时点）

四路杜邦线实录已经 B 独立诊断接收：[主线交付及回执](../../deliveries/dupont-diagnostic-20260911/B-REVIEW.md)。本页历史实现材料已发布到 `codex/toph/four-channel-engineering-review-20260912`，主线不直接接入待审 RTL/BD/XDC；工作副本、完整包复核入口、旧恢复档案见[整理说明](../../../../docs/maintenance/local-materials-2026-09-12.md)。下列“未提交/未收到 B 回执/先录同一段”不再是当前动作。既有实际 one 工程未移动或改写。


## 2026-09-11 晚间最新：杜邦线四路实录完成，A检查通过，待B独立诊断

`captures/dupont-quiet-01`、`dupont-speech-01`均为真实四路短录音，各32000组/1024000字节；原始BIN、串口校验、CSV逐值及H1读取复核通过，64项软件回归通过。实际连接为**杜邦线，不是C转接板实物**；大致共面约40mm正方形、两次未移动，坐标未测，保持null。拓芙已试听人声清晰；8份WAV与共同增益12的转换逐点一致。已有四路实板可听成果，不等于定位、波束或正式M1通过。

当前ELF构建18:23:59，bit SHA为37f6d55f…，完整版本与[复核记录](https://github.com/TophBeifong1744/Competition_fpga/blob/codex/toph/four-channel-engineering-review-20260912/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/review/dupont-20260911/REVIEW.md)绑定，不套用下方build06旧哈希。当前下一步是[转交B独立诊断](https://github.com/TophBeifong1744/Competition_fpga/blob/codex/toph/four-channel-engineering-review-20260912/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/review/dupont-20260911/B-HANDOFF.md)，不是重新采同一批数据。B尚无回执，H2四路交接/阶段最终验收未关闭；未提交推送。以下早先“待录音”内容仅记录当时进度。

## 2026-09-11 早先状态（历史）：C 板工程适配和构建完成，待实板短录音

原 one 的顶层、BD、有效 XDC 已适配 C 板，Vivado 2025.2 综合/实现/bit/XSA 生成完成，配套 ELF 已编译。四 CLOCK 共用分频状态，DATA1～4→mic0～3；PS、DMA、GPIO、时钟/复位、地址、CIC、打包和原解码器保留。完整接口表、恢复办法、产物和上板/导出命令统一见 [C-ADAPTER-RUN.md](https://github.com/TophBeifong1744/Competition_fpga/blob/codex/toph/four-channel-engineering-review-20260912/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/C-ADAPTER-RUN.md)。

功能仿真通过；RTL→BIN→H1 的57组/456字一致；17项软件检查与 [结构/BSP/IO核查](https://github.com/TophBeifong1744/Competition_fpga/blob/codex/toph/four-channel-engineering-review-20260912/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/evidence/c-adapter-closeout01/build-audit.json)通过。内部 WNS=4.640 ns、WHS=0.056 ns；外部4路输入/4路输出延迟未完整约束，实板未做，仍无本版真实四路录音。不宣称 B 复核、H2/H3或阶段验收通过。下一步由拓芙按运行单采一段真实四路数据，不再重做已有PS/打包/导出器。非阻塞风险只在[统一清单](../../../../docs/deferred-acquisition-risks.md#c-adapter-risks)记录。

此前15:50的main发布只包含文档；本次适配源码、恢复副本和新证据仍是本机待交付工作，未在本轮提交/推送，不代表远端main已有完整四路工程。下方[旧提示词](adapter-handoff-prompts.md)和首轮记录仅保留历史，不重复派发或用于C板接线。

## 首轮交付记录（历史保留）

2026-09-11。状态：待审候选，未接入 one、未修改 PS/BD/XDC、未综合实现或上板；没有四路真实录音，不宣称 H2/M1 通过。仅本任务目录新增文件，无 Git 提交/推送。

## 已实现

- source/rtl/four_mic_top.v：纯 Verilog 入口，共同61.44 MHz时基，四个CIC、一个采样相位/预热计数/组编号。
- source/rtl/pcm4_capture_axis.v：四通道同拍组装、32位AXIS八拍输出、FIFO、按组TLAST、溢出和valid失配中止、复位恢复；不串用单麦模块名，不覆盖旧源码。
- source/rtl/pdm_cic3.v：从现有 one 的 imports/rtl 原样复制，SHA-256 a80c176053688662cd8bb47f98edcadeb9b758d514365724fd8b6ffd2120573d；CIC3/R64、乘32、signed24饱和不改。源工程位置及前轮哈希见 NEXT-ACTION.md。
- source/export_four.py：内部BIN导出H1 ss-data-draft-0.3；保留原始BIN、编号/错误、未知坐标与配置频率说明。source_kind/provenance必须调用者明确提供，不凭格式猜音频来源。

## 内部记录合同 ss-four-record-0.1

每组32字节，小端8个32位字：id_lo、id_hi、mic0、mic1、mic2、mic3、flags、reserved=0。mic0位于打包PCM输入最低24位，四路均符号扩展，不额外缩放。flags[3:0]分别表示各路饱和，其他位必须0；饱和在H1映射unknown并保留原始位图，跳号另标drop。不支持新错误码时拒绝转换，不静默抹除。

status位：0 busy、1 ready、2 overflow、3 done、4 clip_seen、5 sync_error；[31:16] FIFO拒收事件饱和计数，并非精确丢失样本数。valid部分有效时置sync_error，中止并要求复位；FIFO满时overflow亦要求复位。发生fatal时允许已排队数据继续排出，但整段无效，PS必须观察status中止DMA，不能以收到部分包宣称完成。

start仅在ready且idle/FIFO空且无fatal时有效；busy时忽略。done在最后一组最后一拍握手后置位，开始新段清零。不支持独立优雅stop命令；中止用前端复位，旧段记录为失败，下一段新acquisition_id。原始sample_id包含预热/空闲PCM输出，不因start清零。

默认32000组×32=1024000字节，250组/8000字节每包，共128包；加64字节保护仍在旧1MiB区间内。名义0.667秒；此阶段不扩DDR区。参数使用正数，FIFO_LOG2>=1；本轮TB用19组/4组包测试非整包尾，尚未穷举参数。

## 实际验证与复现

先在仓库根运行（输出目录必须不存在，保留旧日志）：

```powershell
& './task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/run_sim.ps1' -OutDir 'C:/temp/ss-four-run-new' -VivadoBin 'F:/AMD/2025.2/Vivado/bin'
python -B task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/source/test_export.py
python -B task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/source/check_sim_export.py C:/temp/ss-four-run-new/accepted_words.csv C:/temp/ss-four-export-new
```

预期ALL_FOUR_TESTS_PASS、8项Python测试通过及3次运行57组/456字的RTL→BIN→H1检查通过。证据见evidence/run02。run01初轮将.v作为SV编译；run02改用纯Verilog编译RTL，仅TB用SV，为本轮最终测试口径。测试是功能仿真，不证明BD可添加、综合资源、时序、供电或实录来源。

覆盖：四种不同PDM密度与100ns延迟/高相X模型、预热、四路顺序/符号边界/饱和位、64位ID进位、背压稳定、非整包TLAST、busy重复start、正常完成后再次采集、FIFO溢出、valid失配、中途复位及恢复。未覆盖任意背压/任意参数、物理同步标定、全部复位相位或PS中止恢复。原CIC完整随机卷积测试本轮未重跑，不冒称新覆盖。

## 首轮后续计划（历史保留，已有进展不重复执行）

15:48核对已有source/ps/main_four_capture.c，不能再将以下PS工作视为全部未开始。继续以决定页最新进度为准。原计划：在现有Vitis应用的待审源码副本中匹配八字布局：BYTES/PACKET/步长、四路范围与flags、status bit5、guard及串口导出长度。旧main_mono_capture.c绝不能直接驱动这个新格式。之后A安排原one的模块/四路端口更新、Validate Design、构建新XSA与PS测试，再由用户上板；新RTL/BD按docs/rtl-language-and-bd-integration.md。004和FFT未集成。

首批真实录音放captures/<acquisition_id>/；当前仅有仿真数据，不能补单麦凑四路。新运行记录实际配置即可，不追溯历史加载，不把精细测量重新设为前置。已有NEXT-ACTION是开工时计划，本README记录本轮实际完成范围。
