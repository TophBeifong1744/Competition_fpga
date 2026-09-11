# C 四麦转接板：工程与首批短录音入口

## 2026-09-11 晚间：本次录音的事实与版本覆盖说明

实际首批录音使用杜邦线，不是C板实物；固件仍为four-channel-c-adapter-v1。两段原始数据与8份试听WAV已完成A侧检查，拓芙反馈人声清晰，待B独立诊断。详见[当前复核](review/dupont-20260911/REVIEW.md)与[交接提示](review/dupont-20260911/B-HANDOFF.md)。坐标保持null、geometry_version=four-physical-unmeasured-v1；不要用下方C板导出参数覆盖本次metadata。

本次实际bit SHA=37f6d55fbd1ce314245d189fbe2fa984477c6b61d26a2a23736b71305654605b，ELF构建18:23:59；当前one/XSA/启动文件关系在review/build-snapshot中固定。当前XPR活动打包器位于imports/four_mic/pcm4_capture_axis.v，有效XDC位于constrs_1/imports/c_adapter/c_adapter_io.xdc。下方build06产物、旧路径及“未上板”描述仅为早先记录，不作为本批录音的加载依据。此次不修改工程、不重复上板、不宣称C板通过。

2026-09-11。本页只对应已选 C 板和 `four-channel-c-adapter-v1`，不是旧单 CLOCK 接线单。不采购/制造、不自动上板、不宣称 B 验收或 H2/H3 通过。

## 本轮范围与统一接口

原 `one` 增量适配，保留 PS、DMA、SmartConnect/Interconnect、GPIO、61.44 MHz 数据域、复位及地址分配。顶层 `four_mic_top` 中一个 PDM 寄存器/20分频器扇出四个物理 CLOCK；无四套独立起相分频器。CIC3/R64/乘32/signed24、打包、缓存/DDR约定不改。逻辑同源不代表实际引脚零偏斜。

| 通道/模块插座 | CLOCK端口 | C针号→J4针号 | 球号/Bank | DATA端口 | C针号→J4针号 | 球号/Bank |
|---|---|---|---|---|---|---|
| mic0，U3/U4 | pdm_clk1 / CLK1 | 21→21 | V11 / 13 | pdm_data[0] / DATA1 | 17→17 | Y9 / 13 |
| mic1，U5/U6 | pdm_clk2 / CLK2 | 23→23 | Y13 / 13 | pdm_data[1] / DATA2 | 19→19 | W10 / 13 |
| mic2，U7/U8 | pdm_clk3 / CLK3 | 29→29 | U14 / 34 | pdm_data[2] / DATA3 | 33→33 | W14 / 34 |
| mic3，U9/U10 | pdm_clk4 / CLK4 | 31→31 | V12 / 34 | pdm_data[3] / DATA4 | 35→35 | V15 / 34 |

机器可读版本：[source/c_adapter_mapping.json](source/c_adapter_mapping.json)。每组小端8个32位字仍是 `id_lo,id_hi,mic0,mic1,mic2,mic3,flags,reserved`；四路24位码符号扩展到32位，不再缩放，组号共同且原样保留。flags低4位分别表示四路饱和。

依据：C原 `.epro2`（SHA与当前决定页一致）的 PCB PAD_NET/封装记录；[底板v3.9](../../../../hardware/reference/navigator-zynq/navigator-zynq-baseboard-schematic-v3.9.pdf)第5页 J4→J1/X4；[核心板v2.5](../../../../hardware/reference/navigator-zynq/zynq7010-7020-coreboard-schematic-v2.5.pdf)第6页Bank13、第3页Bank34。Bank34的VCCO接VCCIO，第10页U8为SPX3819M5-3-3，支持名义LVCMOS33配置，不是电压实测。GPIO/DMA寄存器地址及PS时钟保持原配置。

## 插接方向和上板前一次检查

- 图中U1为排母、U2为排针；两者同号同网络，封装1脚均为方焊盘，PCB同为顶层270度放置，针序没有互镜像。接到J4时必须保持 **C针N→J4针N**；不能以器件顶视图和排母背视图中的“左/右”代替编号。
- 从方焊盘/1脚标记确定1→1、2→2，再复核远端 **38→38=3.3V、37/39=GND、40=5V贯通**。不允许180度倒插、错一排、镜像跨接。40不是麦克风电源。
- 29/31/33/35同时关联底板CMOS_D4/D6/PCLK/PWDN。断电确认相关摄像头/其它外设未连接，不能因BD没有相机就假设物理上没有争用。四个CLOCK输出各走各线，绝不并接。
- 各模块LR接GND，NC悬空。已有2.0mm针距与声孔照片不重拍；只看实际装配是否插稳、声孔无遮挡，无短路或错误电源。
- **禁止带C板运行旧单麦/旧针表比特流**：旧W10输出CLOCK，新W10是DATA2输入。断电接板，使用JTAG启动而不是自动启动旧SD/QSPI镜像，再加载本版bit/ELF。

这些是实际接板的基本检查，不追加精细仪器门槛。其它风险只参见[统一记录CBR-01～05](../../../../docs/deferred-acquisition-risks.md#c-adapter-risks)。实物插接尚须用户确认，不把图纸核对写成装配已通过。

## 当前产物与恢复

- 实际工程：`F:/College/verilog_digital_system/AMD/Competiton/one/one.xpr`。
- 实际适配源码/有效约束：`one.srcs/sources_1/imports/c_adapter/`；旧 `single_mic_io.xdc`禁用保留，顶层仍为`system_wrapper`。
- 本轮前备份：`recovery/before-c-adapter-20260911/one/`（完整原工程）及`source/`（改前任务源码）。更早的单麦程序/BSP备份在`recovery/mono-before-integration/`。
- 恢复时先关闭Vivado，将当前one另存保留，再把完整备份复制回原one位置，不直接覆盖仍需保留的新版本。优先保留两套，恢复后不得用旧bit连接C板。恢复动作没有自动执行。
- `integrate_one.tcl`是旧单CLOCK中断尝试，**不再作为运行入口**。本版为`adapt_c_one.tcl`；第一次接入用`integrate`，已经接入后重建用`build`，不会新建整个工程。
- 构建报告位于`evidence/c-adapter-build06/`，PS产物在`evidence/c-adapter-ps01/`。是否完整通过以同目录实际报告和本页后附结果为准，不能仅凭目录存在判断。
- `c-adapter-build01～05`保留端口缓存排查失败；旧生成缓存目录改名保留为`one.gen/sources_1/bd/mref/four_mic_top_stale_20260911`。正确刷新入口是生成的IP对象 `update_module_reference [get_ips -all *four_mic_top*]`，不是BD单元，也没有`-force`选项。

复建命令（仓库根PowerShell；输出用新的目录，关闭Vivado后运行）：

```powershell
$task=(Resolve-Path 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01').Path
$out=Join-Path $task 'evidence/c-adapter-rebuild-new'
New-Item -ItemType Directory -Path $out -ErrorAction Stop
& 'F:/AMD/2025.2/Vivado/bin/vivado.bat' -mode batch -source "$task/adapt_c_one.tcl" -log "$out/vivado.log" -journal "$out/vivado.jou" -tclargs "$task" "$out" build
& "$task/build_ps.ps1" -OutDir "$task/evidence/c-adapter-ps-new"
```

重建不会自动下载。PS沿用既有BSP；须通过`source/audit_c_build.py`核对原BSP XSA与本版PS/DMA/GPIO参数无差异，若不一致停止复用并在新平台副本重新生成BSP。旧单麦应用不覆盖。

本次可复用的PS初始化文件是 `F:/College/verilog_digital_system/Vitis/dma_platform/export/dma_platform/hw/ps7_init.tcl`，已与新XSA内的 `ps7_init.tcl` 逐字节比较相同。此一致性仅适用于当前这组产物；以后修改PS/DDR配置必须重新核对，不能只凭文件名复用。

## 你下一大步：一段真实四路短录音

1. 按上面的编号/电源/无相机争用完成断电接板检查，再上电至JTAG模式。打开COM3、115200串口日志保存，从程序启动前开始保留完整输出。
2. 优先使用本次已编译且BSP兼容核对通过的 `evidence/c-adapter-ps01/four_mic_capture.elf`，明确指定 `evidence/c-adapter-build06/system_c_adapter.bit` 和原兼容平台的PS初始化文件；无需重写PS或重编译才能开始。若要在Vitis保存独立工程配置，再建立C板平台副本导入本版XSA，应用复用现成 `source/ps/main_four_capture.c` 和 `lscript.ld`，不要覆盖单麦应用。**不要让旧平台的Run配置偷偷加载旧单麦bit**。
3. Run一次，在采集开始前持续说话/播放声音。默认32,000组，128包，每包8,000字节，总1,024,000字节，名义约0.667秒。只取一段，不等安静/播放两段齐全、不等长稳。
4. 成功日志应含`FOUR PDM capture four-channel-c-adapter-v1`、128个完整包状态、`FOUR_CAPTURE_INTEGRITY_PASS`、首尾ID、各路极值/零值/饱和数、`sync_error=0 overflow=0`及FNV校验值。饱和标志保留供诊断，不自动算音质通过。失败保留完整日志，不把半段转换成干净录音。
5. 出现`READY_FOR_DDR_DUMP`后不要复位/再Run。选择实际Cortex-A9 #0，在XSDB导出（路径示例是新文件，不覆盖前一段）：

```tcl
connect -url tcp:127.0.0.1:3121
targets
targets -set -filter {name =~ "*Cortex-A9*#0"}
mrd -bin -file F:/College/verilog_digital_system/Vitis/c_adapter_capture_01.bin -size w 0x01000000 256000
```

接收区仍为`[0x01000000,0x01100000)`；数据到`0x010FA000`，后64字节保护区到`0x010FA040`，不扩DDR保留区。启动前清理整个RX+guard的缓存，DMA期间CPU不访问该区，完成后失效缓存再检查；不允许其它核/DMA占用该区。

## 导出给B：复用原解码器，附本版映射

将完整串口文件另存为`F:/College/verilog_digital_system/Vitis/c_adapter_capture_01.log`，UTF-8。然后仓库根执行下例；仅在你确实确认了编号插接、无争用且来源是真实麦克风时使用确认参数，并把场景文字换成真实情况：

```powershell
python -B task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/source/export_c_capture.py F:/College/verilog_digital_system/Vitis/c_adapter_capture_01.bin F:/College/verilog_digital_system/Vitis/c_adapter_capture_01.log task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/captures/c-adapter-01 --acquisition-id c-adapter-01 --operator Toph --scene "填写本次真实场景" --numbered-mating-confirmed
python -B task-packages/PKG-B-ALG/payload/model/python/h1_reader.py task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/captures/c-adapter-01
```

`export_c_capture.py`只加BIN/完整日志/长度/编号/FNV校验及映射元数据，实际解码复用原`export_four.py`。拒绝旧版本、截断、混合多次运行、缺包日志、fatal状态或错误BIN，不覆盖旧导出。原BIN和完整串口均保留，H1七列不变，`hardware-audio/diagnostic`仅基于用户真实采集声明，不靠文件格式推断。

坐标仍`null`，`c-adapter-unmeasured-v1`；不把名义40mm填成测量坐标，不给DOA结论。B读取器`PASS_FORMAT_ONLY`是格式结果，不是H2验收。由拓芙发给“拓芙工作执行”验收后交B，本分支不自行批准。

## 2026-09-11 实际结果与文件入口

工程实现任务完成原one适配和构建；工作执行任务只读核对实际原理图、BD、网表、BSP和产物，并补齐此处记录。不是B独立复核、阶段验收或合入批准。

| 验证层次 | 实际结果 | 证据 |
| --- | --- | --- |
| RTL功能 | ALL_FOUR_TESTS_PASS；四CLOCK逐拍相等、20分频、高相位复位、通道顺序及既有打包/异常检查通过 | `evidence/c-adapter-sim01/simulate-console.txt` |
| 合成数据导出 | 3次运行、57组、456字逐值一致；不是录音 | `evidence/c-adapter-sim-export01/result.json` |
| 软件 | 原解码器8项及日志配对门9项，共17项通过 | `evidence/c-adapter-closeout01/software-tests.log` |
| Vivado构建 | 2025.2，xc7z020clg400-2；综合、布局布线、bit与XSA完成 | `evidence/c-adapter-build06/` |
| 内部时序 | WNS=4.640ns，WHS=0.056ns，TNS=THS=0，未约束内部端点=0 | `evidence/c-adapter-build06/timing_summary.rpt` |
| 外部时序 | 4个DATA无input delay、4个CLOCK无output delay；不宣称最坏外部保证，按CBR-01暂缓 | 同上及统一风险文件 |
| 已实现引脚/同源性 | 八信号方向、LVCMOS33及球号与映射一致；4个FDRE输出副本C/D/CE/R/S/INIT相同 | `io.rpt`、`clock-registers.tsv`、下方audit JSON |
| 保留边界/BSP | 8个保留BD组件与地址不变；原BSP XSA与新XSA的PS/DMA/GPIO参数无差异；程序end=0x00112630，数据加guard末端0x010FA040 | `evidence/c-adapter-closeout01/build-audit.json` |
| 实板/声学 | 未执行、暂无本版四路真实录音；不宣称H2/H3或音频收益通过 | 等用户操作并交原始数据 |

布局优化复制CLOCK输出寄存器是实际实现结果：源RTL仍只有一个共同分频状态，不是四个独立分频器；逻辑等价不代表板端零偏斜。工具的PDCN-1569/RTSTAT-10/REQP-165/LUTAR-1提示保留原报告，统一风险记录CBR-06，不在这里再开催办清单。

有效源码清单：原one的 `one.srcs/sources_1/imports/c_adapter/{four_mic_top.v,pcm4_capture_axis.v,c_adapter_io.xdc}`，继续引用 `imports/rtl/pdm_cic3.v`；这两份RTL连同保留CIC的内容与任务 `source/rtl/` 对应文件的SHA相同。BD为 `one.srcs/sources_1/bd/system/system.bd`。任务中的CIC、打包器、原 `export_four.py` 与适配前备份逐字节相同；PS只改配置版本及一条映射日志。未接入FFT、六麦或其他待审RTL。

bit的SHA-256：`9e1a84ce3a7fd4c599ef95bb6c0d7f30a90abddd6ac769e1a9587133e1408630`，4,045,690字节；任务bit、新XSA内置bit及原one实现产物逐字节一致。XSA/ELF/源码/有效XDC/BSP输入的SHA详见audit JSON。本轮原件和失败记录不删除；文档收尾前版本另存 `recovery/before-record-closeout-20260911/`。

复查命令（仓库根；审计输出必须是新文件）：

```powershell
$task=(Resolve-Path 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01').Path
python -B "$task/source/audit_c_build.py" "$task" 'F:/College/verilog_digital_system/AMD/Competiton/one' "$task/evidence/c-adapter-build06" "$task/evidence/c-adapter-ps01" 'F:/College/verilog_digital_system/Vitis/dma_platform/export/dma_platform/hw/system_single_mic.xsa' "$task/evidence/recheck-new.json"
Push-Location "$task/source"
python -B -m unittest -v test_export test_c_capture_gate
Pop-Location
```

当前只完成工程适配、自检和交付准备；没有采购、制造、自动上板、提交、推送、自审自合。本次不是阶段验收，因此不提前更新已冻结的阶段验收快照或宣称完成阶段收尾。
