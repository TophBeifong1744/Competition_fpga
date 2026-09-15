# 拓芙这一大步：中心+X方向目标单独短录音

这里只做一段，不重做旧录音。已有接板/映射/几何资料直接复用。若接线或外设发生变化只核对变化，明确错电源/短路/争用先停；不追加仪器测量门槛。

## 摆放和记录一次做完

保持mic0～3及轴向不变。两条对角线交点是阵列中心，模型坐标(.02,.02,0)m。用旁边纸条标中心和+X箭头，不能遮声孔；+X方向平行mic0→mic1，按9/13照片即朝照片下方。不要从mic1出发量距离或把原点改成中心。

用户已选择本次用人直接发声。人位于中心+X方向，优先中心至嘴部1.5m、嘴部与声孔大致同高，面向阵列；通过调整既有摆放/坐姿做到，不要求采购。量距终点是嘴部，不是脚尖/身体中心。说明卷尺/直尺或估计方法及粗略误差。不把计划1.5m/0°/同高直接填入实际记录；做不到就记录可实现条件。不是要求精密找点，也不自动证明远场成立。

用正常音量连续说话几秒，例如“这是一段四麦阵列的语音测试，现在持续说话”。建议不要突然喊叫或来回移动头部；这不是为通过阈值修改数据，而是让短抓取覆盖稳定语音并减少过载。站/坐定后先说再Run，维持到采集完成。若点击鼠标必须离开目标位置，先把鼠标放到可伸手的位置或请身边人帮点一次，不能采完再补说。记录实际所说内容、嘴部位置是否稳定、发声是否覆盖采集；无播放设备/文件如实注明。现场人声不是可同步干净参考。

## 保持现有加载入口

继续four_mic_capture的four_mic_capture_app_hw_1 Run，不Build、不运行旧适配脚本。核对运行配置仍使用：

- F:/College/verilog_digital_system/Vitis/four_mic_capture/_ide/bitstream/system_c_adapter.bit
- F:/College/verilog_digital_system/Vitis/four_mic_capture/build/four_mic_capture.elf
- F:/College/verilog_digital_system/Vitis/four_mic_capture/_ide/psinit/ps7_init.tcl

磁盘核查见evidence/preflight-01。旧单麦W10为输出，新版为DATA2输入；禁止切换旧应用或让SD/QSPI自动加载旧bit。保持此前确认过的JTAG启动方式，无共用IO外设竞争，不重复接线改造。

COM3/115200沿用现有可用连接，Run前打开完整日志保存。目标持续发声，Run一次，等待FOUR_CAPTURE_INTEGRITY_PASS、READY_FOR_DDR_DUMP。32000组/128包/1024000字节，约0.667秒。出现失败也保存完整日志，不静默丢弃，不当干净段导出。

保存新日志：F:/College/verilog_digital_system/Vitis/c_center_target_20260914_01.log。在XSDB选择实际核0，导出：

```tcl
targets -set -filter {name =~ "*Cortex-A9*#0"}
mrd -bin -file F:/College/verilog_digital_system/Vitis/c_center_target_20260914_01.bin -size w 0x01000000 256000
```

数量256000是32位字，不是字节。若还没连接，则沿用已有XSDB连接入口connect -url tcp:127.0.0.1:3121；不为这一步转Debug排查。导出前不复位、不再次Run。名字已存在用02，不覆盖01。

背景明显变化时，目标关闭、阵列和设备位置不动，可再独立Run一次并保存c_center_background_20260914_01.log/.bin；它仍是另一段，不拼接为连续记录，也不是严格同步噪声参考。背景未变时先交一段目标即可。

## 交回即可停止

把新BIN、完整log及实际摆放/发声说明交本任务。可一次回复：设备/内容、音量/音效、中心距离及量法误差、方向及相对高度、Run前后持续发声范围、背景是否变化。无需重复提供旧四边尺寸。

工程实现随后复用原导出器、B读取器检查ID/错误/BIN-CSV/版本，保存主机试听WAV、加载记录与哈希。仅同输入手动指向试听/波形/削顶诊断，无独立参考不报SNR增益；有最小可用新段即交工作执行并停止。
