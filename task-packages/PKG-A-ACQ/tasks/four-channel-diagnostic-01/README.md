# 四路诊断采集：首轮 RTL 与导出自检

## 2026-09-11 后续决定：适配已选 C 转接板

拓芙已决定采用C板，执行[当前接口及15:50实际记录](../../../../hardware/microphone-adapter-decision.md)。四CLOCK候选顶层/XDC已修改，功能仿真及合成导出检查通过；有效BD/约束与构建仍在修正，未板测，不宣称适配整体验收通过。已有四路PS/导出器不重做，原“SoundSight｜工程实现”任务继续执行。下方[提示词](adapter-handoff-prompts.md)是历史交接文本，不重复派发。非阻塞风险只在[统一清单](../../../../docs/deferred-acquisition-risks.md#c-adapter-risks)记录。

本次main仅发布文档；下列source、recovery、运行脚本和evidence是本机待审工作目录中的实现/历史记录，未随此次文档提交一并公开，不代表从main可直接复现完整四路工程。后续获准交付再按项目规则纳入源码与证据。

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
