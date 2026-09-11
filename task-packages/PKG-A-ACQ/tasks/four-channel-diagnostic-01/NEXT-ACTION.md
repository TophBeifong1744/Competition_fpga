# 拓芙开工单：从现有单麦链路扩为四路

15:50主流程核对：四路RTL/PS已有，四CLOCK候选顶层/XDC已修改，功能自检通过；不能按以下历史单重复实现。C板适配仍在原任务进行，保存的BD/有效约束与构建尚未通过，无板测，详见当前决定页。本次只发布说明，不把待审源码、原epro2或旧运行产物一并提交。

## 2026-09-11 当前优先动作

用户已决定采用 C 转接板，执行[当前接口与适配说明](../../../../hardware/microphone-adapter-decision.md)。不再讨论是否采用、不以旧 J4-19 CLOCK / J4-20～23 DATA 表接 C 板；在现有进度上适配四个同源 CLOCK 物理输出及新 DATA 针表。一个共同内部时基、采样使能、复位/预热与组编号的原则不变。先读最新实际源码/BD/XDC，避免把下面初始开工步骤重复实施。非阻塞风险只在[暂缓清单](../../../../docs/deferred-acquisition-risks.md#c-adapter-risks)跟踪，明确针脚/供电冲突不可暂缓。

## 以下为首次开工记录，不作为 C 板接线单

2026-09-11；本轮仅只读核对与下达动作，未修改工程、运行新仿真、上板或提交 Git。主责 A，B 复核；H2 支持任务只协助导出格式。阶段依据为 docs/phases/2026-09-11-to-09-16/README.md、A.md；精细补证遵循 docs/deferred-acquisition-risks.md，暂缓，不新增测量门槛。

## 首个实际动作

**先扩展 `single_mic_top.v` 的采集前端与 `pcm_capture_axis.v` 的成组打包，并通过四路自检；不要先接四只麦或重建工程。** 在本任务目录保留原件来源及改动源码，稳定后由 A 接回原 one。004、FFT 待审内容不集成。

先保留一个共同 PDM CLOCK、一个采样使能、共同复位和预热计数，将 DATA/同步寄存器扩为四路，复用四个不改算法的 pdm_cic3 实例。四路 valid 同拍才组成一组，共用一个原始 uint64 sample_id；不为各通道分别编号。valid 不一致要显式报异常并中止，不能混入不同采样时刻。现有 CIC 数值及相位不在这一步优化。

## 已核对的实际入口

- Vivado：`F:/College/verilog_digital_system/AMD/Competiton/one/one.xpr`，引用 `one.srcs/sources_1/imports/rtl/{single_mic_top.v,pdm_cic3.v,pcm_capture_axis.v}`，不是仅引用仓库外教学文件。
- BD：同工程 `one.srcs/sources_1/bd/system/system.bd`，实际实例 `single_mic_top_0`；m_axis 接现有 DMA，aclk 接 clk_wiz_0/clk_out1。保留现有 61.44 MHz 数据域，不接入 100 MHz FFT 候选。
- 约束：`one.srcs/constrs_1/new/single_mic_io.xdc` 当前仅 W10 CLOCK、W9 单路 DATA；新增三路必须显式扩端口/约束，不能以旧 XDC 假装四路已接入。
- PS：`F:/College/verilog_digital_system/Vitis/single_mic_capture/src/main_mono_capture.c`，目前每样本4字/16字节，DMA包4000字节，DDR范围 `[0x01000000,0x01100000)`，采后 JTAG 导出。
- 本轮实际读取的 top/capture/PS SHA-256 分别为 `47cfa7f59ab3a1fa1c52ee502133ed03dd32da5f76d29faa5101a131d9f8448c`、`a057c119227e071230eaf2f157a5c9263e20a72acb55c4fe6faf54daeefeebc6`、`c8dcf209829c45a3aeb27e4e2ef1f627a8419c15ec21a1777d76af65ac382034`，与已发布单麦快照一致。此为磁盘核对，不证明当前板上加载版本。

## 打包与导出：一起改，避免只扩 DATA

建议本任务采用内部记录候选：8×32 bit，依次 `id_lo,id_hi,mic0,mic1,mic2,mic3,flags,reserved`；PCM24逐路符号扩展，reserved=0。继续32位 AXIS，只将FIFO记录拓宽、beat计数及pop/TLAST末拍从3改为7。这是内部格式建议，不修改 H1 CSV 合同；源码、PS、导出器必须同时采用并标明新 config_version。

原每包250组可变为8000字节；PS修改 PACKET/BYTES、遍历步长、四路范围/错误检查和导出提示，不遗漏缓存范围及保护区。**48000组×32=1536000字节，超过旧1 MiB保留区，不能只把单路乘四继续写。** 首次可用32000组（128包、1024000字节，另64字节保护，仍在旧区间内），名义约0.667秒，作为短诊断允许，不冒称1秒。若需1秒以上，先明确扩展保留区与链接/其他访问者边界，不暗改LIMIT。

flags须记录实际异常含义；饱和等没有 H1 专用词的情况可映射 `stream_error=1,error_flags=unknown` 并保留原始逐路位图解释，不能静默清零或发明H1错误枚举。溢出保留失败BIN/状态，不输出“干净完整录音”。

首次交付路径：四路PCM组 → 原DMA S2MM/DDR → 原始BIN → 四路转换器 → `captures/<acquisition_id>/{metadata.json,samples.csv}`。CSV严格 H1 ss-data-draft-0.3，保留真实ID和异常；坐标未知填null及原因，不报告角度。真实录音标 hardware-audio/diagnostic，同时记录操作者、实际声音与抓取点；码型只作功能测试。

## 可复用测试与本轮通过条件

已有 `C:/Users/Toph Beifong/.codex/visualizations/2026/09/05/01a06ff9-0287-7e00-b73d-abf12e6b3035/single_mic_v1/sim/tb_single_mic.sv`：包含CIC卷积参考、PDM相位/预热、负值/边界、64位ID进位、背压稳定、TLAST及溢出中止。复用测试逻辑，不把单麦旧PASS当四路新PASS。旧 test_decoder.py/单麦包 source/test_delivery.py 可复用边界测试思路，但不能直接解析四路新记录。

新增自检至少覆盖：四路互不相同输入防串列；同拍valid与共享编号；每路正负/饱和值；8拍背压稳定与包尾；FIFO溢出/中止；采集中复位与重新启动不残留旧组；原编号高32位进位；原BIN到CSV逐组逐通道一致。当前实现没有独立优雅stop接口，不宣称具备；第一轮明确以复位中止、丢弃失败段和新 acquisition_id 验证恢复，未实现项列明。

本次动作完成时交：修改源码、四路TB/输出及打包字段说明即可，未板测就明确未板测。之后再由用户更新原BD/XSA/PS并上板；一段可解析真实四路数据拿到就给B，不等一小时长稳。语言/包装统一按 docs/rtl-language-and-bd-integration.md，保持纯 Verilog BD 入口。

## 接线依据与真正阻塞项

已有方案：共享CLOCK J4-19/W10；mic0～3 DATA分别J4-20/W9、21/V11、22/V10、23/Y13；各模块LR接GND、NC不接，DATA不并联。来源：PKG-A-ACQ/payload/hardware/microphone-wiring-candidate.md及用户既有确认。其历史“单麦未开始/先完成全部测量”不覆盖最新阶段安排。

- 代码/TB当前没有已确认的外部阻塞；先实施上述改动。
- 上板前须确认三根新增DATA与端口/实物贴签一致，无其他外设占用，并具备可靠的CLOCK/VDD/GND分配，不能猜线或将多根线强塞一个端子。当前只确认资料，不声称四路实际已接好。
- DDR容量与包布局不一致是必须修正的软件问题，以上短段方案可避免先扩大DDR区。
- 精细电平、示波器时序、历史加载追溯继续记账暂缓，不再要求先补四项才能开工；明确接错电源、短路或异常发热仍立即处理。

9月16日检查目标：真实四路短片段、H1元数据、导出命令、功能测试和B反馈；不是完整M1/H3通过。本次不持续执行后续所有步骤，不新增任务包、不动冻结证据或主流程状态页。
