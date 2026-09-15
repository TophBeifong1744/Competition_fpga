# 当前采集能力与下一项最小改动（未实施）

依据2026-09-14读取的实际one/PS，路径与哈希见evidence/preflight-01。当前没有新增连续采集测试。

|问题|当前实现与限制|源码依据|
|---|---|---|
|什么一直运行|复位释放后PDM时钟、CIC和组ID持续工作；不等于持续存储|four_mic_top中phase、id/warmup逻辑|
|何时开始/停止保存|PS先挂第一包DMA，再给start约10μs脉冲；capture收满TOTAL_SAMPLES=32000即busy=0，FIFO末组8拍发完后done；约0.667秒有限抓取|main中p==0；capture的captured/sent边界|
|能否持续重启|RTL在ready、空FIFO、无overflow/sync_error时可接受新start，但PS没有重启循环，main成功后retain()永久等待；即使增加循环，批次间缺号/间隙仍不是连续录音|accept_start及retain|
|停止/复位|start拉低不是stop命令；无独立优雅stop入口。当前Run配置做系统复位/PL重新配置/PS初始化/核0复位/ELF加载，不能称只重启采集|launch.json、accept_start|
|DDR所有权|启动前CPU写哨兵并flush/invalidate整个RX+guard；128包由DMA写，期间CPU不碰RX；完成后invalidate，CPU检查，随后XSDB读冻结数据。禁止其他核/DMA占用|main中的cache操作、SimpleTransfer、检查循环|
|导出能否并发采集|当前不能在同一保留区并发覆盖与导出；采后busy已停且PS留存，PDM/CIC虽仍运行但不落入这段DDR；再次Run先覆盖区内哨兵，旧段立即失去保证|retain、busy边界、哨兵初始化|
|错误记什么|DMA逐包SR/长度；源overflow/sync_error sticky、clip_seen、逐路clip；高16位drops只计忙时满FIFO拒绝事件，饱和到65535且首次拒绝会停止busy，不是连续缺样总数|status/drops；PS打印rejected_events|
|错误如何恢复|保留复位前SR/状态、已完成包数和失败原因，再DMA reset；超时则提示DDR不保证稳定；即使DMA复位成功也不能据此清除PL sticky/FIFO，明确要求PS/PL复位后另一次采集|fail分支；PL sticky只在rst_n复位清除|

## 提交工作执行排期的最小连续采集原型

建议独立候选：**PL可停止的连续分包模式 + PS两槽轮转接收与在线计数/校验**，不把“再Run一次”包装成连续。保留现有短抓取模式和可运行版本；本轮不实现。

- PL保留同一PDM/CIC/ID，不到32000组自动停；每250组TLAST。增加明确定义的stop请求，在完整组/包安全边界停并排空；复位/overflow/失效传播有明确状态，不能截半组伪装正常包。
- PS显式维护FREE→DMA_OWNED→CPU_READY/CPU_OWNED→FREE所有权。两个8000字节数据槽各配独立64字节guard，合计16128字节，拟在现有1MiB保留区内规划，不改变现有地址合同直至候选正式审核。元数据/计数另有明确链接范围；不得复用仍在处理/导出的槽。
- 保持缓存行对齐；DMA前清理、DMA后失效，所有权转移和处理完成后才能复用。需检查全部程序/堆栈/槽/guard边界，不只检查end；严禁隐式扩大GROUPS/LIMIT。
- 当前包时间250/48000≈5.208ms，原FIFO1024组约21.333ms容量仅为满容量理论缓冲，不能当确定调度裕量。simple DMA可作为首版候选，但重装载+CPU消费最坏延迟必须实测满足持续吞吐，失败则记录再评估是否需要SG；不预设通过。
- 原记录带宽48000×32=1,536,000字节/秒。有限环形DDR不能无限保留原数据；第一原型可在线计数/校验后回收，只保留短错误快照。若需求是边录边完整保存，必须另定满足持续带宽的消费者/输出接口，不能靠JTAG慢读冻结模型承诺无限连续。不得偷迁移PYNQ/接DAC。
- 最小验证：跨多次轮转ID连续、无槽复用竞争/残留，缓存开关与guard检查，最慢允许消费、随机背压、包边界stop/restart、复位中止、超时/overflow故障注入、计数饱和、失败快照；先实际短运行记录吞吐/高水位/误码，再谈长稳。本轮这些新测试均未执行。

这张表是实现提议，不是新M1/H3准入或扩写整机授权；与本批目标单独数据一起回工作执行决定下一任务。
