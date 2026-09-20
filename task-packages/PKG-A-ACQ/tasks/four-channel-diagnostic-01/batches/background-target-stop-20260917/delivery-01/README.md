# 交工作执行／B：同次连续背景—人声—停声输入

2026-09-17；A作者自检完成，**diagnostic，待工作执行检查发布及B独立诊断**。不是M1/H3、目标存在判断、误锁或停止响应验收。用户操作上板，Codex仅离线检查/导出；不提交、推送或合入。

## 输入与实际条件

- [原BIN](c-scene-20260917-01/raw.bin)、[完整串口](c-scene-20260917-01/serial.log)、[metadata.json](c-scene-20260917-01/metadata.json)、[samples.csv](c-scene-20260917-01/samples.csv)。H1 ss-data-draft-0.3，四路signed24/int32、48kHz配置值、原编号及flags保留。
- 一次Run连续 **288250组、1153包、9224000字节，6.005208秒**；原编号17246～305495，无缺号/重复/错误行。FNV **9494D645** 与UART一致，四路min/max/zeros/饱和标志逐项一致。显式停止后排空，槽均FREE，SOURCE=C100000A、DMA_SR=00001002；无段内重启或拼接。
- 用户实际：现场说“**就让我忘了这一切**”；嘴部在 **mic0的+X方向约5cm，与声孔同高**；大致安静2秒→说话3秒→停声1秒。测量方法/误差、精确声学起止时间未知，[操作记录](actual-record.json)保留未知项。
- 阵列沿用操作者既有40mm共面正方形模型，mic0为原点，+X朝mic1、+Y朝mic3，并非新增精密测量。在此近似模型中嘴部相对中心约(0.03,-0.02,0)m，约3.61cm／−33.7°，**仅模型推导，不是远场或角度真值；不能标作阵列中心0°、1.5m**。

## 检查与实际观察

[结果](RESULT.json)：BIN/CSV逐行一致、四路WAV读回一致；[现有B读取器](logs/h1-reader.stdout.json)返回 **PASS_FORMAT_ONLY**，不代表B已独立接受。[复用导出器8项＋新增数据关联9项测试](../evidence/export_20260917_172248_f2182396/result.json)通过；保留了截断、重复ID、signed24越界、校验值、统计、成功游标、导出长度和混入其他Run的负例。

**末段尚不能当作声学确认的纯背景。** 按操作者近似边界计算的原幅度RMS如下，末段仍高于开头；可能的声音来源没有被独立判定，不据此宣称目标未停、误锁或硬件故障。

| 近似分段 | mic0 | mic1 | mic2 | mic3 |
|---|---:|---:|---:|---:|
| 0～2秒，背景 | 7878 | 8512 | 8253 | 7965 |
| 2～5秒，人声 | 10591 | 11508 | 11296 | 10284 |
| 5秒～末尾，报告停声后 | 11662 | 12343 | 13128 | 11570 |

单位为原PCM整数码；[完整统计](phase-statistics.json)。这些分段只用于摘要，**不是波形检测出的起止，也不是精确样本标签或独立噪声参考**；B可结合完整波形/试听作近似复核。不声称SNR收益。

试听：[mic0](c-scene-20260917-01/mic0.wav) · [mic1](c-scene-20260917-01/mic1.wav) · [mic2](c-scene-20260917-01/mic2.wav) · [mic3](c-scene-20260917-01/mic3.wav)。四路及整段统一 round-to-nearest-ties-to-even(PCM24×12/256) 转16位、48kHz，额外削顶0；不分段归一化、不去直流、不滤波，原BIN/CSV不变。WAV为PC试听入口，不是板端DAC。

## 版本、入口与变化

- 原four_mic_endurance／continuous_platform；PS Cortex-A9 #0 standalone。S1新增六秒单段、CPU原字节留存；原两槽DMA、DDR RX范围及PL/PDM/CIC/格式不变。计时和实际ELF内存边界由用户构建及只读检查核对，不重跑旧耐久或综合实现。
- [匹配构建记录](versions/build-result.json)、[源码](versions/src/)、[ELF](versions/build/four_mic_endurance.elf)、[map](versions/build/memory.map)、[Run配置](versions/_ide/launch.json)、[硬件哈希及冻结引用](versions/hardware-reference.json)。ELF SHA-256为 `4b7823bdefa3776a910a3359b5851fa52c6f4ce89432cc3ee0072dee52ca06a6`。
- 用户Run four_mic_endurance_app_hw_1，等待READY后导出，不在采集中JTAG读存储。本次数据起点0x00112AC0，2306000个32位字；提供的导出入口：

```tcl
targets -set -filter {name =~ "*Cortex-A9*#0"}
mrd -bin -file F:/College/verilog_digital_system/Vitis/c_scene_20260917_01.bin -size w 0x00112AC0 2306000
```

导出文件及FNV已核对，但未收到完整JTAG下载/导出交互实录；版本依据是匹配的主机文件/Run配置和UART build，不宣称FPGA回读证明。上式只绑定本次录音，不能拿来读取将来的未知Run。

## 离线复跑及清单

在上一级批次目录执行，输出目录必须不存在；这是本次实际导出命令，不重跑硬件：

```powershell
& 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B .\finish_scene.py --raw 'F:/College/verilog_digital_system/Vitis/c_scene_20260917_01.bin' --serial 'F:/College/verilog_digital_system/Vitis/c_scene_20260917_01.log' --out .\delivery-01
```

已有delivery-01会拒绝覆盖，复现须另选新目录。[检查命令](commands.json)、[依赖哈希](dependencies.json)、SHA256.json为导出阶段清单；FINAL-SHA256.json含本交接页及整包最终清单。原BIN SHA-256：`4bc12f0033e00508100ce5f70ed7bf2025236f3800ff14523feec8eacee37e83`。

**到此停止本批采集扩展。** 交工作执行检查完整性并发布准确待审SHA，再由B诊断；近场/近似时间边界和末段较高能量如实保留，不补样、不改golden、不伪造纯背景，也不为本批新增长稳/精密仪器前置条件。
