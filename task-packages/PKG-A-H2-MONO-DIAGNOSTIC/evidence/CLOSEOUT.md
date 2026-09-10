# 单麦离线收尾补证（未宣告完整验收）

最新裁定见 [ACCEPTANCE_STATUS.md](ACCEPTANCE_STATUS.md)：A允许diagnostic文件完整性、导出一致性与材料整理有限收尾；板级完整验收暂停。以下为裁定前的检查依据，新增分析不冒称A独立复现。

日期：2026-09-10。用户确认没有万用表、示波器。未改RTL/BD/PS，未操作板卡，未提交Git。

## 低频与数值检查

low_frequency_check.py / low_frequency_result.json记录两份已验收原始数据的每100ms均值、AC RMS、极值及低频局部峰。运行方式：使用有numpy的Python执行本目录脚本；它读取相邻mono_acceptance_20260910快照，无需板卡。

- 安静低频局部最高峰48Hz，歌曲54Hz；均还有30Hz等其他峰。名义频率分辨率1Hz、使用Hann窗；不能将其直接认定为固定50Hz工频。
- 两份开头100ms均值分别9676.2、10311.49，末100ms为-954.24、-1748.17。存在明显随捕获时间衰减的偏置，可能涉及启动/环境/模拟链，根因未判明，不声称只有稳态窄带噪声。
- 每份10个100ms块均不完全重复；相邻同码率约3.45%、3.50%，此统计不能独立证明无重复采样，连续原始ID已有独立验证。
- 全部PCM都是32的整数倍，与RTL c3左移5位一致，不是右对齐/符号扩展异常；未以24位容器声称24位有效精度。
- RTL审读：PDM映射正负1、三级积分/梳状差分32位模运算一致，R64增益262144，乘32后饱和到signed24。模溢出在等宽CIC中为设计行为；仅审读不替代原始PDM对照仿真。当前没有原始PDM实测，不能据PCM排除一切采样错误。
- FIFO每条128位顺序为id低/高、符号扩展PCM、flags；背压推进按握手，溢出中止，匹配PS四字读法。本次未发现明确数字链错误。

## 实现/版本证据

本目录保留实际impl_1完整rpt、runme.log、clockInfo、启动ps7_init.tcl及BSP xparameters.h；manifest.json给出来源与SHA。报告工具为Vivado2025.2，2026-09-10 14:16左右，routed设计system_wrapper。

- WNS5.319ns、WHS0.041ns、TNS/THS=0，报告时钟61.440MHz、周期16.276ns（显示取整）。只表示已约束路径满足。
- no_input_delay=1、no_output_delay=1；方法学LUTAR-1警告5条及DRC中的警告保留，不能宣称无警告或完整IO闭合。
- 保存BD所有相关AXI时钟、GPIO、DMA、PS GP0/HP0接口时钟、单麦、start_pulse和reset慢时钟均接clk_wiz输出；locked接dcm_locked，PS低有效FCLK_RESET0_N接reset外部输入及clockwiz resetn。
- 所有相关低有效负载共享peripheral_aresetn；未独立使用interconnect_aresetn，未擅自改复位分配。生成reset IP的synth VHDL确认C_EXT_RESET_HIGH=0，匹配PS低有效复位；同域释放依据reset IP与slowest_sync_clk连接，未进行实测释放波形验证。
- XSA内bit与运行配置目录归档bit逐字节一致；XSA内ps7_init.tcl与运行目录初始化文件逐字节一致（脚本断言结果true）。这些是文件间一致性，不倒推旧采集加载身份。

## 采样窗口边界

RTL时序名义核算：61.44MHz周期16.2760417ns；PDM /20=3.072MHz，半周期162.760417ns。phase19下降，phase9上升；phase9消费的同步输出对应phase7的引脚采样，即下降后约130.208ns、下一上升前约32.552ns。

因此需要外部时钟输出延迟、走线、麦克风tDV、DATA输入延迟与建立裕量之和小于约130.208ns，并核实高阻切换之前采样。若按既有手册核验中的tDV最大100ns作假设，仅剩约30.208ns名义预算，不是实际时序裕量；这里没有新增手册实测证据。两级同步器不替代源同步外部窗口闭合。pdm_clk元数据FREQ_HZ也不等价generated_clock/IO约束。

## 仍缺及请求裁定

硬件任务确认未找到VCCO_B13、模块VDD、CLOCK/DATA测量记录或安全测点批准图；用户无仪器。电气/外部时序批准应保持待验证，不能继续指导无依据测量或伪称通过。

请求工作执行裁定当前可接受的功能子项及暂停项；强低频与启动衰减偏置是否需要无改动延后触发捕获的最小复测，请明确必要性。现有较早试听已有用户确认歌曲，最新固定对照试听未再确认。准确版本绑定仍需将已哈希文件与后续用户真实加载记录关联，不能伪造旧记录；在必要安全条件未满足前不安排新的板测。

不主动做高通/FIR、三秒、长稳、四麦或H2；不把阶段中间材料称为完整验收。
