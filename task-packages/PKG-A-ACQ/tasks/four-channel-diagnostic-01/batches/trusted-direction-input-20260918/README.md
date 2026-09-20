# 可信四路开发输入：方向、目标存在与停声诊断

状态：**准备完成，等待拓芙录制首段预检查；本批真实录音 0/8。** 不是验收通过，不提交、推送或合入。

## 范围及复用判断

- 依据 `deliverables/phase-2026-09-18/README.md`、`CLOSEOUT.md`；本次只读共享 HEAD 为 `085dbdbb4f369bd40b0459513cbe909e9acf5acc`，不以本地 HEAD 推定远端状态，未切换或同步工作区。
- 9/14 阵列中心 +X/1.5m 人声只有32000组、约0.667s，缺固定播放及活动对齐；9/17 S1 六秒为 mic0+X约5cm现场人声，约2/3/1秒标签非精确。9/13背景/歌曲为旧近场条件。本轮引用但不改写这些证据，不能代替同场景八段输入。
- 现有 `four_mic_endurance` 实际已为 **S1_6S_RAW**，复用 `continuous_platform`，不是重跑E1耐久程序。通过原 `check_scene.verify(stage=load)` 只读核对源码、实际对象/ELF、map、BSP、硬件及Run引用，见 `evidence/preflight-01/result.json`。仅把新检查输出路由到本目录；原检查器及历史回执不改。
- ELF SHA-256：`4b7823bdefa3776a910a3359b5851fa52c6f4ce89432cc3ee0072dee52ca06a6`；bit：`b15991bc0f8595970361be553b542e334dbb7dca268c01864ecd80fcffbbffaf`；XSA：`b84e93631132a3838cc9dadc1ce9037f2685d4d10de0b1655c76291663a8f60b`。完整路径与源码/对象哈希见检查回执。不是实际FPGA回读证明。
- 48kHz、四路signed24存int32、每组8字/32B；两槽RX `[0x01000000,0x01100000)`，每槽8000B数据+64B保护。**另有既存CPU归档缓冲**：data=`0x00112AC0`，容量9600000B/300000组，前后各64B保护；程序end=`0x00A400C0`，仍低于RX起点。不是让1MiB RX直接容纳六秒，也不新增DDR或更改内存合同。
- 每次连续采集至少288000组/约6s，包边界排空后实际组数略增，以本次串口及BIN为准；容量上限6.25s。4.8s播放文件留约1.2s启动余量，最终须凭首尾标记和波形确认完整。

## 已准备 / 尚未完成

| 项目 | 状态 |
|---|---|
| 手机播放方案 | 用户确认手机扬声器、关闭全部可见音效、固定音量；型号和具体档位未知，内部DSP仍未知 |
| 固定源文件 | `playback-v1/soundsight-target-v1.wav`，48kHz/16bit/mono/4.8s；文字“清风吹过树林。”；源语音、时间表及哈希同目录 |
| 离线自检 | `evidence/test-offline-01.log`：10个测试方法通过，含缺标记/歧义/短输入/覆盖拒绝等负例；旧S1 BIN+UART回归仅为复用输入，不是本轮录音 |
| 工程变更 | 无。未改one、RTL、BD、XDC、Vitis源码/配置/产物，未构建、下载或运行 |
| 首段播放/抓取 | 未执行；手机播放兼容性、完整性、可辨识度、四路幅度及现场对齐待预检查 |
| 八段资料、B读取器 | 未取得新BIN/串口，未对新数据运行；新导出包装器完整流程待首段验证 |
| 活动标注 | 尚无声学对齐，不能用播放文件时间表充当精确真值 |

完整操作见 `操作单.md`。实际记录从 `operator-record-template.json` 复制填写；unknown保持null，计划位置不得写入实际位置。每次独立Run按现有配置会复位并重新加载，段内不复位、不重启；各段不拼接。

## 对齐、试听与证据边界

源文件：0.20–0.35s上扫标记；1.00–约2.201s语音；4.45–4.60s下扫标记；其余为数字零。开始/结束标记用于确认完整播放及时间映射，不计入算法评分；初始排除每个标记前后0.2s，若实际混响更长需扩大并记录。语音前后的可用背景区不包含标记及其尾音。源文件数字静音不等于房间无噪声。

离线对四路分别做绝对归一化匹配相关和两个标记的仿射映射，保存峰值、歧义峰及间隔。归一化仅用于标记定位，**不修改BIN/CSV幅度**。算法阈值仅为工具启发式、非B的存在判断阈值；返回候选位置而非自动确认为真实声学边界。需要结合波形/试听检查多径、拖尾、截断及起停；不确定性未知保持null，不填±1样本。源文件也不是阵列处同步干净参考。

四通道所有八段试听统一 `round-even(PCM24×12/256)` 转int16，48kHz，不去直流/滤波/AGC/逐段归一化。如转换新增削顶则保留失败，不静默限幅；协商降低**整批统一**试听增益，原BIN/CSV不改。现有PDM/CIC3 R64 gain32及signed24处理仍然存在。

数据为**开发试验集**：一旦用于调整阈值，同批结果不能再宣称独立性能验证。不据两段RMS相减宣称降噪/SNR收益；不宣称方向精度、正式M1/H3、声学收益或实时闭环通过。客观音频对照待B合同，当前不扩展。

## 离线复跑入口（不操作板卡）

以下在本目录 PowerShell 执行。路径含空格须引号；保留失败输出，新一次选择新目录。

```powershell
$py = 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $py -B ./scripts/prepare.py preflight --out ./evidence/preflight-02
& $py -B ./scripts/test_offline.py
# 原始log先完整保存；此命令只打印本次正确XSDB导出命令，不执行：
& $py -B ./scripts/process_capture.py dump-command --serial 'F:/College/verilog_digital_system/Vitis/trusted_bg_pre_20260918_01.log' --bin-output 'F:/College/verilog_digital_system/Vitis/trusted_bg_pre_20260918_01.bin'
# 取得原始文件及对应真实record后，工程实现运行（每段独立out）：
& $py -B ./scripts/process_capture.py process --raw '<本次BIN>' --serial '<完整串口>' --record '<本次实际记录JSON>' --out '<新的交付子目录>'
```

复用 `background-target-stop-20260917/finish_scene.py::verify` 的BIN/UART逐字段关联校验、`source/export_four.py`、B的 `payload/model/python/h1_reader.py`。新包装器先保存原始输入，失败也保留；检查编号、signed24、flags/reserved、FNV、计数、DMA、保护区和排空等，逐行核对CSV与BIN。当前单独主机版本检查不替代用户的实际Run记录。每段结果仍需人工看异常和标签，不仅凭PASS归结场景有效。

本地语音生成不是板卡工作；失败与安全环境限制见 `evidence/FAILURE-HISTORY.md`。后续使用冻结WAV即可，不依赖语音引擎逐次生成。入口/依赖/文件清单见 `SHA256.json`；获取新数据后增量新清单，不覆盖旧清单。

## 停止点

首个目标预检查可用即沿相同设置完成其余；若缺尾标记、无法完整播放、严重过载或版本错配，先保留失败并定位，不改固件碰运气。明确电源/短路/输出争用立即停机。八段数据及操作、标签、哈希和未知项齐备后回工作执行；当前不得称“完整输入包已交付”。
