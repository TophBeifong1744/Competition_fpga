# C 转接板首次实录：操作与事实记录

2026-09-13 建立并更新。状态：已收到拓芙两段C板实录、整体照片、尺寸和接板/加载确认，完成离线交付自检，待工作执行检查及B独立复核。用于9/14检查及B后续diagnostic，不自行宣布正式M1通过。

## 当前交付入口

- [交接摘要与实际结果](HANDOFF.md)、[几何说明](GEOMETRY.md)、[复现/运行入口](REPRODUCE.md)。
- [安静数据](delivery-01/c-adapter-quiet-20260913-01/metadata.json)、[人声数据](delivery-01/c-adapter-speech-20260913-01/metadata.json)：各目录含原BIN/完整日志/H1 CSV/四路试听WAV。
- [结果](delivery-01/RESULT.json)、[逐文件哈希](delivery-01/SHA256.json)、[加载版本](delivery-01/versions/loading-record.json)、[操作者记录](operator-record.json)。
- received-01保留首次接收、当时未知几何的检查记录及原哈希，不修改旧结果。新几何仅用于delivery-01；旧杜邦线数据不动。

下方为首次操作单及当时磁盘核查；其中“待反馈”描述由上述新交付覆盖，不代表当前仍未录音。

## 本次磁盘核查

现有 Vitis four_mic_capture/_ide/launch.json 指向以下文件，当前SHA与此前杜邦线交接归档对应；不代表已经在本批板上加载。不重建，不运行历史迁移脚本。

- bit：F:/College/verilog_digital_system/Vitis/four_mic_capture/_ide/bitstream/system_c_adapter.bit
  SHA256：37f6d55fbd1ce314245d189fbe2fa984477c6b61d26a2a23736b71305654605b
- ELF：F:/College/verilog_digital_system/Vitis/four_mic_capture/build/four_mic_capture.elf
  SHA256：c0b430e77d4d0d53d4ca0b4399fe69e0cd7865e5815ac3549b5d209d39e7192a
- PS初始化：F:/College/verilog_digital_system/Vitis/four_mic_capture/_ide/psinit/ps7_init.tcl
  SHA256：a158fcc7d723b21003864159006e781ffaf5e8df24ec9b1d9279f9d14ff3ee5e

沿用Cortex-A9 standalone PS程序、DMA→DDR→XSDB导出路径。试听在电脑由导出WAV完成，不是PS音频输出/DAC或PYNQ。32,000组、48kHz名义约0.667秒；每组32字节，总1,024,000字节。RX从0x01000000至0x01100000（不含），数据终点0x010FA000，64字节保护区终点0x010FA040。此合同引用已有归档，不称为本轮新编译验证。

## 操作者一次完成的大步

1. 全部断电。按C板和J4的1脚标记核对同号直通，复核远端38=3.3V、37/39=GND、40=5V贯通；禁止镜像、偏排、倒插。麦克风不用40脚供电。无相机或其他共用IO竞争驱动，四CLOCK不可短接，模块插稳且声孔未堵。
2. 断电设置已知JTAG启动模式，防止SD/QSPI旧镜像加载；不确定启动拨码含义则先核对板上标记/实际资料，不猜拨码。旧单麦W10为输出，新版W10为DATA2输入，属于必须处理的冲突。
3. 打开four_mic_capture的现有运行配置，核实上述bit/ELF/PS初始化路径；仅运行该配置，不运行single_mic_capture或hello_world。采集前开启完整串口保存。
4. 固定阵列，安静背景Run一次，出现READY_FOR_DDR_DUMP后立即单独导出BIN；未导出前不复位、不再次Run。再固定声源位置持续播放，另存新的完整日志，Run并导出第二次。记录每次实际是否由Run执行系统复位/重新加载，不能称作无复位连续录音。
5. 失败和异常保留；不要覆盖重试，使用递增后缀。两个片段不拼接、不重编号。

建议暂存文件名：c_adapter_quiet_20260913_01.bin/.log 与 c_adapter_speech_20260913_01.bin/.log；暂存在F:/College/verilog_digital_system/Vitis/，收到后归入本目录独立子目录。文件已存在就用02，不覆盖。

XSDB选择实际Cortex-A9 #0后，mrd使用起点0x01000000、-size w、数量256000。数量是32位字而非字节。导出器沿用source/export_c_capture.py；未获得操作者插接确认前不传入numbered-mating-confirmed声明。

## 接口及待填实物记录

|列|模块插座|CLOCK：连接器针/球|DATA：连接器针/球|实际位置|
|---|---|---|---|---|
|mic0|U3/U4|21/V11|17/Y9|未知|
|mic1|U5/U6|23/Y13|19/W10|未知|
|mic2|U7/U8|29/U14|33/W14|未知|
|mic3|U9/U10|31/V12|35/V15|未知|

针表来自当前C-ADAPTER-RUN.md及hardware/microphone-adapter-decision.md，不是本轮重新测通或声学映射确认。实际插接方向、供电检查、启动模式、相机移除、实物通道标签、实际加载和录音均待操作者反馈。

建议在声孔朝向一侧拍本次整体装配/摆放记录，纸上标+X、+Y、mic0～3；俯视角度从+X朝+Y为正。不要用照片透视长度当实际尺寸。用尺测声孔中心位置，记录单位、量法、估计误差；声源距离说明相对于哪个参考点，相对高度说明参考平面。暂未测坐标和角度保持未知，不用名义40mm填充。原始数据先交，不因几何未知阻塞诊断。

## 待完成交付

每段原BIN、完整UART、加载记录、H1 metadata.json/samples.csv、试听WAV及其增益说明、读取器/逐值检查、SHA256；实际几何单及异常。现有风险仅引用docs/deferred-acquisition-risks.md，不另增精细测量门槛。正式M1、同步/增益标定、定位和波束均未由本轮验证。完成后交拓芙工作执行及B复核，不提交推送合入。
