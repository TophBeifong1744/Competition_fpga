# 给“拓芙工作执行”：中心参考目标输入交接

2026-09-15。输入回执、最小新数据、M1下一改动清单已整理完成，请检查完整性后发布待审SHA交B独立复核。工程实现没有提交、推送、合入或自行验收。本批达到来单停止点，不继续扩展录音库/连续模式/DOA/DAS。

## 1. 可直接交B的新输入

路径：delivery-01/c-center-target-20260914-01/。包含原始raw.bin、完整serial.log、metadata.json、samples.csv、mic0～3.wav、listening.json。文件名保留用户使用的20260914编号；收到/处理日期为9/15，实际录制时刻未知，不从文件名推造精确日期时间。

|核对项|本轮新执行结果|
|---|---|
|数量|32000组，128包×8000字节，总1024000字节|
|采样率/时长|配置48000Hz，32000/48000≈0.666667秒；非仪器测频|
|编号|17413～49412连续，无跳号/重复/倒退|
|数据配对|BIN重算FNV=F55CC8CE，与完整串口一致|
|DMA/源|各包SR=0x1002，最终SOURCE_STATUS=0x0A，sync_error=0、overflow=0|
|幅度/flags|四路非恒定，无完全相同的通道对；逐路min/max/零值/饱和计数与串口相符，饱和标志0|
|CSV|全部32000行七列与BIN解码逐值相同，无补样、重编号、额外滤波或去直流|
|读取器|原B读取器PASS_FORMAT_ONLY；与9/13旧C板两段同会话读取也通过，无配置冲突|
|回归|原export/test_c_capture_gate共17项正负例通过；不是新RTL仿真|
|试听|4份48kHz PCM16，固定共同增益12，round(PCM24×12/256)，逐样本验证一致、无新增削顶；没有以旧批用户试听反馈冒充本段主观试听结果|

原BIN SHA256：22e51534d0b95ed22f0472c4b92d8a9081ed5537dadc6eff9defb40c8bd37f43。

原串口 SHA256：3711337834fb5992bd6023dc94087d8e304483a056f9c1deb56c1fac518446df。

逐文件哈希见delivery-01/SHA256.json和本批PACKAGE-SHA256.json；原命令及返回码在delivery-01/commands.json，原始检查输出在logs，结果在RESULT.json。

## 2. 声源参考与完整输入回执

见INPUT-RECEIPT.md及actual-record-20260915.json。保持mic0为原点、+X向mic1、+Y向mic3，模型中心(.02,.02,0)m不改为元数据原点。拓芙报告嘴部实际位于中心+X、中心距离1.5m、与声孔大致同高、“误差微小”。该描述为操作者提供，不是未执行的计划，也不是精密方位真值。

现场人声取代来单优先的设备播放，具体所说内容/声级、头部运动、精确发声起止及样本活动区间未提供，不填造。量法与数值误差未知，不自行赋予±1cm/±1°；原始近似位置用于手动指向诊断，不证明远场适用。未提供独立干净/噪声参考或本批背景片段，不报SNR收益。播放文件不存在于该现场人声来源，不要求采购设备或补齐完整演示场景。

旧9/13近距离输入追加说明仅写入本批回执：手机扬声器播放歌曲、中偏小音量、开启超重低音；型号/曲名/AGC/限幅等未说明保持未知。旧录音和冻结metadata不改。

H1仍ss-data-draft-0.3，signed24/int32、hardware-audio/diagnostic。本批只改变声源场景和acquisition_id，完整配置字段及geometry_version与9/13用户几何版一致，经同会话读取实测无冲突。固件仍four-channel-c-adapter-v1；不会把H1扩展版本当新固件版本。

## 3. 版本、数据流及M1缺口

evidence/preflight-02保存9/15再核查，已批准current_build的check返回CHECK_PASS_NOT_BUILD；当前bit/ELF/XSA/init/launch/PS源/ld/map的8项SHA与先前匹配记录一致，XSA内bit/init也匹配。仅磁盘+日志配对证明，没有本次FPGA读回或完整JTAG加载逐步日志，不把相同版本字符串当充分身份依据。

delivery-01/versions保存bit/XSA/ELF/init/launch/PS源/ld/map和loading-record；evidence快照保存实际活动RTL/BD/XDC及原导出器。实际启动仍four_mic_capture_app_hw_1的系统复位、PL配置、PS初始化、核0复位和ELF加载。未执行新的综合、实现、时序或连续采集测试。

PS仍A9 #0 standalone，simple S2MM→DDR，采后XSDB导出。RX=[0x01000000,0x01100000)，数据到0x010FA000，guard64到0x010FA040，程序end日志为0x00112630。已有PDM/CIC3/R64/乘32/饱和处理不是“无DSP”；主机原PCM不额外处理。音频输出入口是PC WAV，无本批板端DAC或PYNQ迁移。

M1-NEXT.md逐项说明：前端一直运行但只保存32000组；start拉低不是stop；完成后retain保留DDR，不能同区边导出边覆盖；FIFO拒绝事件不是连续丢样总数；失败保留复位前状态再DMA reset，重试需PS/PL复位。下一最小建议为PL可停止连续分包+PS两槽所有权/在线校验，明确现有DDR范围、缓存和吞吐/恢复测试要求，**本轮未实施，仅交工作执行排期**。

## 4. 范围与待复核

本批仅新增/更新center-target-20260914内文件；实际one/PS/RTL/CIC、导出器核心、两项Skill、B包、根索引及旧批次均未改。共享HEAD仍57c50e6，其他任务脏改动保留；未为本任务同步/重置共享目录，也未重新核实远端。

无新失败录音提交，不虚构失败段；脚本失败会保留FAILURE及日志，已存在输出拒绝覆盖。测量精度、独立通道/增益/延迟/极性标定、远场/定位/SNR收益、实时音频闭环、长稳、正式M1/H3均不在本批通过范围。当前结论为作者离线自检完成，不是B独立复核批准。
