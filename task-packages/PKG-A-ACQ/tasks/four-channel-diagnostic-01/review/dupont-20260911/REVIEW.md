# 杜邦线四路短录音：A 交接前复核

复核日期：2026-09-11。结论：**通过本次诊断材料完整性复核，可以交 B 独立诊断；B 尚未接收/复核，H2 四路交接与本阶段最终验收尚未关闭。**

输入为本机未提交文件，不以 main `9878ccafdda6cd5a522cc9de95c1277bcee70f08` 冒充数据提交版本。实际版本由 `run02/integrity.json`、`run02/listening.json` 和 `build-snapshot/manifest.json` 的逐文件 SHA-256 固定。原始 captures 未改写；本复核由 A 侧工作执行任务完成，不冒充 B 独立验收。

## 1. 实际完成与核查结果

| 检查 | 安静 dupont-quiet-01 | 人声 dupont-speech-01 |
| --- | --- | --- |
| 原始数据 | 1,024,000 字节，32,000 组四路 | 同左 |
| 配置时长 | 32,000 / 48,000 = 0.666667 秒 | 同左 |
| 原始编号（含端点） | 17544～49543 | 15798～47797 |
| FNV-1a32 重新计算/串口 | A34F540B / 一致 | 7B1E2B16 / 一致 |
| BIN→CSV逐值比对 | 全部编号、四路数值及错误列一致 | 一致 |
| 串口传输记录 | 128 包×8,000字节，DMA_SR=0x1002 | 同左 |
| 最终源状态 | 0x0A，done/ready，未报告溢出/同步错误/削顶 | 同左 |
| CSV错误/缺号 | 0行/0处 | 0行/0处 |
| 原始饱和flags/保留字 | 均0 | 均0 |
| 恒定通道/完全相同的通道对 | 无/无 | 无/无 |

四路去均值 RMS（PCM码值，mic0～3）：安静 `[6844.03,7398.05,7275.09,6596.69]`；人声 `[145620.36,138723.20,147402.37,162700.80]`。这是两个独立片段的幅度统计，不是信噪比改善、声压测量或通道增益标定。没有发现阻止首轮诊断的数据格式故障。

原始 BIN SHA-256：

- 安静：`38d3a75b352efd25a23afd82c2838cd83685c9167351d8edb09c297f2e801d8a`
- 人声：`78db105ab1fa216bafbb06b7fe73d989e88e0cd0be95f419b967e61637af272c`

H1读取器在同一进程读取两段，返回 `PASS_FORMAT_ONLY`，与提交日志解析后的 JSON 相等。原日志为带BOM的 UTF-16，而新日志为 UTF-8；字节不同不构成数值或语义差异。`run01/`保留首次复核脚本仅按UTF-8读日志而失败的记录和脚本；改正BOM识别后在新目录 `run02/`复跑通过，未改录音或原日志。

## 2. 来源、缩放与未知项

- 实际为杜邦线连接四只麦，不是 C 转接板实物。配置名 `four-channel-c-adapter-v1` 和串口中 `C adapter` 是固件接口名称/固定文字，不能作为使用C实物的证据。
- 拓芙声明：大致共面、约40mm正方形四顶点，两次之间未移动。此为操作者描述，不是测量值；`coordinates_m=null` 保持不变。
- `mic0..3`是逻辑数据列；未证实每只物理麦对应哪一个几何顶点。声源方位、距离、高度、精确录制时间及室内混响参数均未知。不凭文件时间或名义40mm补写。
- 共同61.44MHz数据域，配置PDM=3.072MHz，CIC3/R64后配置采样率48kHz。PDM位映射±1，CIC增益64³，输出乘32并饱和到signed24，存为符号扩展int32；BIN/CSV导出不再缩放。24位是交换范围，不是已测有效精度。
- 抓取点为 PDM→CIC3→八字AXIS记录→DMA S2MM→DDR→JTAG BIN。记录格式小端 `<IIiiiiII>`：id低/高、mic0～3、饱和flags、保留字。
- 两次是不同 acquisition，不能拼成一段或把较小的第二段起始编号误判为段内倒退。没有段内重启迹象，但不据此声称完成系统停止/重启专项验证；两次之间的具体复位操作未提供。

## 3. 当前 one / c_adapter_platform / four_mic_capture

只读检查当前磁盘及启动配置，已保存21份实际文件快照。本轮未重建或重新上板。

| 当前产物 | SHA-256 |
| --- | --- |
| one实现bit、XSA内置bit、应用启动路径bit（三者字节相同） | `37f6d55fbd1ce314245d189fbe2fa984477c6b61d26a2a23736b71305654605b` |
| one导出XSA、c_adapter_platform输入XSA（二者字节相同） | `71e7bf6d4fcb769582e5485660515b8f615b2027aa2ff18c1f8d3f67f9457baa` |
| four_mic_capture/build/four_mic_capture.elf | `c0b430e77d4d0d53d4ca0b4399fe69e0cd7865e5815ac3549b5d209d39e7192a` |

ELF包含 `Sep 11 2026 18:23:59`，两份串口日志一致。启动配置指向该应用、该平台bit与PS初始化脚本；PS初始化脚本与XSA内版本相同。链接end=0x00112630，与日志相符；DMA区为 `[0x01000000,0x01100000)`，数据加guard止于0x010FA040。

当前实际top、打包器、CIC、PS C源码和有效XDC与任务source对应文件逐字节相同。XPR关闭旧单麦XDC，启用 `one.srcs/constrs_1/imports/c_adapter/c_adapter_io.xdc`；打包器实际活动路径是 `one.srcs/sources_1/imports/four_mic/pcm4_capture_axis.v`，不是凭另一个同名文件推断。现有HWH对应32000组、250组/包、预热4096、单S2MM DMA和双通道GPIO，地址0x40400000/0x41200000。

以上支持操作者所述当前配置，**不是事后对FPGA已加载状态的密码学证明**。旧build06的 `9e1a84...` 不用于本次版本绑定。当前bit文件时间16:46:58，XSA18:10:40，ELF18:23:59；不得把18:23:59说成bit构建时间。

本次读取当前工程既有路由报告：WNS=4.640ns、WHS=0.056ns；4路输入、4路输出外部延迟未完整约束。没有重跑RTL仿真、综合或实现，旧功能PASS不计成本轮新结果；外部裕量、同步标定与长稳仍未验收，按统一风险清单暂缓，不阻塞短数据诊断。

## 4. 试听补充

拓芙于2026-09-11反馈：“已试听 WAV，人声清晰，试听效果良好”。这是操作者主观试听证据，本任务没有代替其声称亲自听过。

`captures/listening-01/`的8份WAV均为48kHz、单通道PCM16、32,000帧。逐点验证与对应原始PCM按 `round(PCM24*12/256)` 转换一致；所有文件共同增益12，无新增饱和。`listening-info.json`来源哈希与BIN相符。WAV是放大后的试听副本，不是原始H1输入，也不能用其响度宣称增强收益。

**用户实板采集声明、匹配串口/原始数据和试听反馈共同表明：四路采集到文件、可听人声已经有实板成果。** 不再记为“尚无四路录音”，但定位精度、波束形成、C转接板实物与正式M1均不在通过范围。

## 5. 复现入口

仓库根目录，Python环境需NumPy（本次版本见run02/integrity.json）。输出必须选新目录：

```powershell
$task='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01'
$review="$task/review/dupont-20260911"
python -B "$review/audit_capture.py" --captures "$task/captures" --reader task-packages/PKG-B-ALG/payload/model/python/h1_reader.py --output "$review/recheck-new"
python -B "$review/audit_listening.py" --captures "$task/captures" --output "$review/recheck-new/listening.json"
python -B task-packages/PKG-B-ALG/payload/tb/python/test_h1_reader.py
python -B "$task/source/test_export.py"
python -B "$task/source/test_c_capture_gate.py"
```

本次重新执行47项读取器、8项导出器、9项日志配对测试，全部通过（64项）。测试中的码型仅用于软件回归，不替代两段真实输入。独立逐字解码检查另见audit_capture.py；没有修改B读取器或算法。

## 6. 交接与阶段收尾

准许范围：将这两段真实四路数据和试听副本作为 `diagnostic` 输入交B；不直接送入六麦定位入口，不猜坐标。本机未找到B本人可连接任务，交接包及 `B-HANDOFF.md`待拓芙转交，**尚未通知B本人或收到回执**。

按docs/phase-closeout.md核对：本次是A交接前检查，不是9月16日阶段最终通过。当前无新增获B批准源码，故不迁入活动rtl/ps目录、不覆盖9月10日冻结快照；B回执/包级批准后由主流程按准确范围做活动归位和阶段归档。未提交、未推送、未合并；不自审自合。原件被Git忽略的问题由完整ZIP交接包及逐文件清单规避；未来Git发布须显式纳入原BIN/日志，不能只提交CSV。
