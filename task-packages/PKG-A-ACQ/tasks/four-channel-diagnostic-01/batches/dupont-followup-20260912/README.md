# 杜邦线四麦后续诊断：操作单与当前入口

编制：2026-09-12。状态：PREPARED / WAITING_FOR_USER_BOARD_RUNS。
本目录只承接首批之后的物理映射、重复启动和频谱现象跟踪；全部保持 diagnostic。
上板由拓芙操作；本分支负责检查、指导和整理，不自行宣布验收、提交或合并。

## 1. 本次已经做了什么

- 只读核对实际 one、c_adapter_platform、four_mic_capture，以及生效 RTL/XDC、启动配置、bit/XSA/ELF、链接 map。
- 磁盘核对 14 项通过，详见 [preflight.json](evidence/preflight.json)。没有运行新的综合、实现、下载或采集。
- 当前 bit/XSA/ELF 与 B 接收的首批用户构建快照一致，不是直接沿用旧 build06 的结果。
- 未改 RTL、BD、XDC、PS、算法或导出器；未覆盖任何历史录音和失败材料。
- 新批次尚无实板录音，物理通道映射和重复启动结果全部待确认。

首批接收依据：本地 Git 对象
`2e2f685faf5520181cdd00cde2cd5030e75e67e2:task-packages/PKG-A-ACQ/deliveries/dupont-diagnostic-20260911/B-REVIEW.md`；
其接收输入为 `d088e2c7deda9c505c094fd48d6f90bcd7f52807`，仅 diagnostic。
旧任务说明若仍写“等待 B 首批接收”，不据此重开首批验收。

本次不比较是否采用 C 板。当前采集实物是杜邦线连接；
`c_adapter_platform` 和 `four-channel-c-adapter-v1` 是已有工程/固件名称，不能当作已装 C 转接板的证据。

## 2. 不变的工程与数据合同

| 项目 | 当前值 |
| --- | --- |
| 工具 / 器件 | Vivado 2025.2 / xc7z020clg400-2 |
| 硬件工程 | F:/College/verilog_digital_system/AMD/Competiton/one/one.xpr |
| 平台 / 应用 | F:/College/verilog_digital_system/Vitis/c_adapter_platform / four_mic_capture |
| 运行配置 | four_mic_capture_app_hw_1，使用 Run，不切换旧单麦应用 |
| 数据域 / PDM 时钟 | 61.44 MHz / 3.072 MHz，同一分频状态驱动四个独立 CLOCK |
| 抽取 / PCM | 原 CIC3、R=64、gain32；配置 48 kHz，signed24 符号扩展至 int32 |
| 预热 | 原 4096 组，不修改；原始编号不因导出而重置 |
| 每组 8 个小端 32 位字 | id_lo、id_hi、mic0、mic1、mic2、mic3、flags、reserved |
| 每次采集 | 32000 组 / 128 包 / 每包 250 组、8000 字节 |
| 总数据量 / 配置时长 | 1024000 字节 / 32000÷48000≈0.667 秒；不是本次实测时钟精度 |
| 原始 flags | bit0～3 为各通道饱和标记；其他位和 reserved 按现有检查器处理 |
| DDR 保留范围 | [0x01000000, 0x01100000)，不扩容 |
| 本次数据 / 保护区 | 数据至 0x010FA000（不含），64 字节保护区至 0x010FA040（不含） |
| 当前程序末端 | 0x00112630，低于 RX；依据当前 memory.map |
| 缓存 | 接收前原程序对接收范围及保护区维护缓存；DMA 期间 CPU 不碰缓冲，完成后失效缓存再校验 |
| H1 | ss-data-draft-0.3；hardware-audio / diagnostic；坐标 null；未标定 |

关键文件及完整 SHA-256 在 preflight.json；下面只列识别前缀，不能用前缀替代最终完整哈希：

| 文件 | SHA-256 前缀 |
| --- | --- |
| system_c_adapter.bit | 37f6d55fbd1ce314 |
| system_c_adapter.xsa | 71e7bf6d4fcb7695 |
| four_mic_capture.elf | c0b430e77d4d0d53 |

## 3. 下一大步：固定实物编号，连续完成四次逐麦激励录音

这四段同时用于任务一和任务二，避免另录一套重复数据：
R1 建立初始运行，R2、R3、R4 分别记录三次“上一轮结束后再次启动”的完整过程。
四次运行各自保留文件，不能在同一次采集后重复导出四份冒充四轮。

### 3.1 先固定身份，不动现有阵列

1. 选定固定观察方向，把四只实物标为 P0、P1、P2、P3，参考 [channel-map.md](channel-map.md)。标签不盖声孔；不要为了贴标签重摆麦克风。
2. 沿现有 DATA 线追踪到板端 J4，填写实际针号和线色。只观察即可，不为本任务交换线或重接 CLOCK。
3. 确需接触/调整接线时先断电，随后记录这次断电或接线变化；不能声称条件从首批至今完全未变。
4. 物理 P0 不预设为 mic0。由 DATA 实际接线给出逻辑列候选，再由四次声学响应交叉检查。
5. 若方向或板端针号看不清，先保留“未确认”，不猜球号，不按杜邦线颜色推断信号。

无需精密坐标、万用表或示波器。原来“约 40 mm 正方形”仍只是摆放描述；
未知坐标保持 null。明确错电源、短路、异常发热、输出争用或实际堵孔立即停止相关操作。

### 3.2 局部声学激励

- 使用同一个小声源，例如单只耳机单元或手机扬声器开口，播放相同内容，保持同一音量档。
- 每轮只把声源靠近目标实物麦克风的声孔方向，保留空气间隙，不能接触声孔或敲击板卡；不要吹气。
- 麦克风、线缆、板卡位置均不移动，只移动声源。声源固定后，再开始该轮 Run。
- 先让声音稳定播放，再点击 Run，保持到串口提示完成；实际采集只有约 0.667 秒，看到输出才发声可能已经晚了。
- 不靠提高到过载的音量强求“某列最大”。声源覆盖范围太大时，多列同时响应是可能的，应记录“未确认”而不是强判映射。
- 若出现明显饱和/削顶标志，保留这一轮。说明原因后以较低音量另存一次，不覆盖失败/无效记录。

| 轮次 | 声源靠近的实物 | BIN / 串口日志 | 重复启动用途 |
| --- | --- | --- | --- |
| R1 | P0 | map-p0.bin / map-p0.log | 初始完整运行 |
| R2 | P1 | map-p1.bin / map-p1.log | 第 1 次再次启动 |
| R3 | P2 | map-p2.bin / map-p2.log | 第 2 次再次启动 |
| R4 | P3 | map-p3.bin / map-p3.log | 第 3 次再次启动 |

### 3.3 每轮执行一个完整闭环

1. 串口 COM3，115200；如实际 COM 变化，记录真实端口。Run 前准备好日志保存，保留从本轮版本头到 DDR 导出提示的完整串口输出，不只截末尾 PASS；不能把两次输出混在一份成功日志里。
2. 声源就位并稳定播放，确认当前应用为 four_mic_capture，使用现有 Run 配置。
3. 等待 `FOUR_CAPTURE_INTEGRITY_PASS groups=32000 bytes=1024000 packets=128` 和 `READY_FOR_DDR_DUMP`。
   同时保留所有 DONE 包记录、首尾 ID、sync_error、overflow、DMA 状态、FNV 和幅度统计。
4. 在下一次 Run/复位/断电之前，导出本轮 DDR，保存对应 BIN 和完整串口日志。
5. 导出完成后，可停止声源；按照下一节暂停 A9 并记录状态，再移声源开始下一轮。
6. 保存 Vitis Log 中各轮加载过程，尤其是三次重新启动的复位、PL 配置、PS 初始化、ELF 下载和启动记录。
   可统一存为 raw/launch-sequence.log，保留时间和轮次对应关系，不修改工具原始输出。

若出现 FAIL、超时、卡死或输出不完整：先保存完整日志与当前状态，记录实际情况；
不把失败改名成 PASS，不直接反复 Run 冲掉现场。后续尝试使用新编号，例如 map-p1-r02。

## 4. “停止”和“重新启动”在当前工程里究竟是什么

当前 PS 程序只做一次定长采集，然后留在保留 DDR 的循环里，没有交互式采集开始/停止命令。

本批采用的运行序列为：

`32000 组采集自动结束 → 导出 DDR → 暂停 A9 → 下一次 Vitis Run`

- “采集结束”：RTL 停止向本轮记录流加入新的组，排空已接收数据；PS 校验并保留 DDR。
- XSDB `stop`：只暂停所选 Cortex-A9 #0。它不是关闭 Zynq，也不停止 PDM 时钟或 CIC。
- 当前 Run 配置：PS 系统复位 + 重新配置 PL + ps7_init/post_config + A9 复位 + ELF 重新加载/运行。
- 这不是断电重启，也不是仅给已有采集模块重新打 start 脉冲；尚未测试“同一程序内重新触发采集”或“录音中途主动停止”。
- 配置文件证明“计划执行什么”；实际 Vitis Log/XSDB 输出才证明每轮“执行了什么”。如操作与配置不同，照实改 run-record.md。

### 导出入口：在 XSDB Console，不是 CMD 或 PowerShell

每一轮确认采集已完成后运行以下块。每轮只修改 capture_name：
R1=map-p0、R2=map-p1、R3=map-p2、R4=map-p3。
新目录 raw 已由本操作包建立。

```tcl
connect -url tcp:127.0.0.1:3121
targets
targets -set -filter {name =~ "*Cortex-A9*#0"}
set followup_dir {E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/dupont-followup-20260912/raw}
set capture_name map-p0
set target_file [file join $followup_dir "${capture_name}.bin"]
if {[file exists $target_file]} {
    error "Refuse to overwrite previous capture"
} else {
    mrd -bin -file $target_file -size w 0x01000000 256000
}
```

注意：交互式控制台若显示任何错误，立即停止，先保留输出再处理；
文件已存在时，上述条件块不会再次导出，应换一个新的 capture_name，不覆盖。

`256000` 是 32 位字的数量，不是字节，也不是 32000 组；
成功文件应为 1024000 字节。本地路径含空格，用花括号保留完整路径。

确认导出成功、日志已保存之后，再运行：

```tcl
stop
targets
```

把输出保存在该轮的 map-p0-xsdb.log 等文件里，再进行下一轮 Run。
这里只暂停已完成本轮采集的 A9，不对正在写 DDR 的采集提前 halt。
下一次 Run 前必须已保存上一轮文件；禁止用上一轮的 FNV/ID 配下一轮的 BIN。

## 5. 数据返回后如何检查和导出（本分支负责）

收到本轮原始材料后，先检查再导出，复用现有实现，不重写采集或导出器：

1. 调用 ../../source/export_c_capture.py 的纯函数 `verify(raw, serial)`：
   核对 1024000 字节、128 个完整包、每包 8000 字节、版本头、DMA/源状态、FNV、首尾 ID 与段内连续性。
   该纯函数适用于当前固件的杜邦线数据。
2. 不使用 export_c_capture.py 的整套 CLI：它会加入 C 转接板插接声明，不适合当前杜邦线实物。
3. 通过 ../../source/export_four.py 原入口导出 H1，指定
   `source_kind=hardware-audio`、`config_version=four-channel-c-adapter-v1`；
   每轮 acquisition_id 唯一，provenance 明确“杜邦线、目标物理 ID、实际激励与重启层级”。
4. 在新建 captures/<acquisition-id>/ 保存 raw.bin、完整 serial.log、metadata.json、samples.csv；
   对本轮新生成 metadata 补充真实记录，坐标仍 null，保留原始 ID、幅度和错误标志。
   不预建该输出目录，否则现有 exporter 会因防覆盖而拒绝。
5. 运行仓库既有 H1 读取器，保存完整标准输出、错误输出与退出码：
   task-packages/PKG-B-ALG/payload/model/python/h1_reader.py。
   结果只代表格式与约定检查，不替代物理映射或声学验收。
6. 对每轮 raw.bin / serial.log / metadata.json / samples.csv、实际版本文件及分析输出保存 SHA-256。
   逐轮比较哈希、FNV、编号、幅度和错误统计；跨轮 ID 重启或间隔不自动判错，不重新编号或拼接。
   不同声音的四轮若原始数据完全相同，应标记疑似旧数据并核查，不能只凭哈希相同直接断言硬件原因。

原始 flags 饱和位通过已有导出器保留在 raw.bin，H1 行标为 unknown；
不清零错误行，也不靠剪掉失败片段得到“全通过”结论。
串口文件保持工具保存的原始字节；若有 UTF-16 等编码差异，只在读取时处理，不覆盖原日志。

### 对应关系判读

- 对四轮分别列出 mic0～3 的原幅度均值、RMS、峰值、饱和/错误数，以及响应强弱矩阵。
- 可另报分析副本的去均值 RMS，以区分 DC 与声学变化，但同时展示原均值/RMS；
  不改 BIN/CSV，不独立归一化四通道来制造等幅或强弱结论。
- 只有“实物 DATA 追线一致 + 对应局部激励的响应支持”才写确认。
  没有追线依据、响应接近/矛盾或存在过载时，保留未确认及具体原因。
- 不用简单的最大幅度硬判映射，不用相关性证明通道身份、精确同步或增益一致。

## 6. 任务三：在一、二之后补一段安静对照

先完成上面的四轮，任务一、二可单独申请复核。
随后声源停止播放，保持阵列、供电、线缆和软件配置不变，另录
`quiet-repeat-01.bin / quiet-repeat-01.log`，仍为原来 32000 组。

与首批相比“没动过”的事项必须由用户确认；
如果中间曾断电、移动或换线，记录变化，不把新旧片段写成严格单变量实验。
本轮重新启动本身是已声明的操作条件。

B 首批诊断基线：

| 项目 | quiet mic0 / mic1 / mic2 / mic3 |
| --- | --- |
| <100 Hz 功率占比 | 91.04% / 91.00% / 83.26% / 91.53% |
| >4 kHz 功率占比 | 1.55% / 1.41% / 9.47% / 0.56% |
| 最大非 DC 频点 | 四路均 46.875 Hz |

B 方法：配置 Fs=48000，4096 点 Hann 窗、hop=2048、每窗去均值、单边功率平均，
频率间隔 11.71875 Hz；相关性为整段去均值 Pearson。
复查时保留这些设置，并明确频带边界、窗定义、FFT 归一化和 DC 分母规则。
原 B 分析实现未在当前活动目录齐备；精确数值复算前先核对这些细节，
不能只按方法摘要宣称复现到同一小数位。

原 BIN/CSV 不去直流、不滤波、不调增益、不改阈值。
分析中的去均值只用于与 B 方法对照，另保留 DC/原幅度统计，避免掩盖低频现象。
不要拿试听用增益 WAV 代替原幅度输入。

- 若低频共同成分或 mic2 高频偏高没有重现：如实写未复现，结束本次现象跟踪，不无限追加排查。
- 若重现：先展示前后数据与条件，再只提出一个受控变化，交拓芙执行；不预先改代码/换麦/换板。
- 46.875 Hz 是当前 FFT 频点，不足以判断为工频；频谱或相关性也不能单独判坏麦、复制通道或供电故障。
- 非阻塞问题统一引用仓库 docs/deferred-acquisition-risks.md，不另开精细测量前置门；
  真正出现新的未登记风险时再最小补记。错电源、短路、输出争用等安全问题立即处理。

## 7. 本目录组织与交付边界

- [channel-map.md](channel-map.md)：物理标签、接线、相对位置及确认状态。
- [run-record.md](run-record.md)：逐轮条件、实际重启层级、日志和结果索引。
- [raw/README.md](raw/README.md)：原始记录命名与防覆盖约定；目前没有新增录音。
- [evidence/preflight.json](evidence/preflight.json)：本次磁盘版本、缓存/地址合同、14 项核对及实际未上板声明。
- 后续 captures/ 和 evidence/：逐轮 H1、读取器输出、哈希清单、响应/频谱结果；有真实数据才生成。
- 交付摘要分开列任务一、二、三的已完成项、未确认项和失败记录，交拓芙带回“拓芙工作执行”申请复核。

本次磁盘检查不是新的功能仿真、时序验证或实板验证。
不宣称正式 M1、精确同步、增益标定、定位、波束形成、H3、一小时长稳或完整复位覆盖。
没有新的阶段验收，因此此时不触发阶段验收后归档/合入，也不改变首批接收边界。
