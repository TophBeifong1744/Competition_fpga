# 核心板、DDR 与历史 PS7 配置适用核对

**后续证据（2026-10-15）：** 用户截图确认实际选用 DDR3 / `MT41J256M16 RE-125`，与本文件的历史配置一致；SD_CD 已沿原理图核到 MIO10，PS PHY strap/复位依据和厂商 7020 PYNQ 2.7.0 镜像候选已找到。见 [平台接续](pynq-platform-next.md)。以下保留2026-10-14核对范围；旧“未找到镜像”“CD未核清”不代表最新状态。

2026-10-14；只读已有原理图、规格书、照片、XSA 参数及工程记录，没有运行旧测试、EDA、初始化程序或板卡。本核对沿 [PR65 的原平台接续](https://github.com/TophBeifong1744/Competition_fpga/pull/65#issuecomment-6171010767)，只补资料依据，不修改硬件或选择镜像。

**结论：资料中的 DDR 容量、位宽、地址线数量与历史 PS7 配置相符，PS 输入时钟、MIO Bank 电压及已启用 UART/QSPI 分配相符；完整实物版本及 DDR profile 电气/时序适用仍 UNVERIFIED。** 原理图为南亚 `NT5CC256M16`，历史 PS7 为美光 `MT41J256M16 RE-125`。不同料号不能凭容量一致就视为参数兼容，也不能据此断言旧配置一定错误。当前尚无本板匹配镜像、BSP 或运行时的准确原件身份。

结构化结果、来源 SHA256、原始配置值和检查边界见 [board-ddr-mio-audit.json](board-ddr-mio-audit.json)。完整历史参数保留在 [ps-config.json](ps-config.json)，不回写历史 XSA。

## 来源及身份边界

| 来源 | 本次读取的位置 | 可支持的事实 |
|---|---|---|
| 核心板原理图 `hardware/reference/navigator-zynq/zynq7010-7020-coreboard-schematic-v2.5.pdf` | 第4页 PS MIO/时钟/复位、第5页 DDR Bank、第7页电源、第8页 DDR、第9页存储、第11页 PS PHY | 文件标题 `ZYNQ_CORE_2V5_240425`；这是文档版本，不能当实际核心板 PCB 版本 |
| 底板原理图 `hardware/reference/navigator-zynq/navigator-zynq-baseboard-schematic-v3.9.pdf` | 第2页 SD/启动选择、第6页串口选择 | SD 电平转换、启动开关、CH340C 与 P5 路由；当前开关/跳帽位置未确认 |
| 规格书 `hardware/reference/navigator-zynq/navigator-zynq-board-spec-v1.2.pdf` | 第13页电源、第14页 DDR、第18页复位、第26页启动 | 7020 文档配置为两颗 `NT5CC256M16`、合计1GB/32位；7010 的512MB配置不能混用 |
| 已有核心板正面照片 `hardware/evidence/board-2026-09-07/baseboard-front-core-xc7z020.jpg` | 本次原图查看 | `CF7010B/7020B`、XC7Z020 与两颗 DDR 位置可见；DDR 完整后缀与核心板修订看不清 |
| 历史 `system_continuous_20260915.xsa` 内顶层 `system.hwh` | 已提取的937项 PS7 参数 | 配置值及连线，不是实物读回、内存训练或 Linux 实测 |

用户确认当前速度等级为 `-1`，与 C 保存 live-loop XPR 的 `xc7z020clg400-1` 一致；历史 XSA 是 `xc7z020clg400-2`。保留两者来源，不把旧 `-2` 的报告用于新 `-1`。底板 V3.9 与核心板文档 V2.5 是两个对象。

本轮用户又提供核心板元件位置示意图：文字标为 `XC7Z010CLG400-1`、`4Gbit DDR3（两片）`，并标出DDR位于Zynq左侧。该示意图有助定位元件，不能替代已有XC7Z020实物识别，也没有提供当前DDR完整丝印或核心板版本。来源仅保存附件文件名、尺寸与hash，不重新发布图片或私有聊天目录。

后续第二张示意图标为 `XC7Z020CLG400-2`、`8Gbit DDR3（两片）`，芯片族与已有实物照片一致；按配套规格书，两片总计8Gbit=1GiB，每片4Gbit，不把该括注读成每片8Gbit。`-1/-2` 为SoC速度等级，不用于识别外接DDR型号或核心板PCB修订；它仍需供准确构建/时序核对单独记录。第二张图未覆盖此前USER_REPORTED的`-1`，也没有补齐DDR后缀或实际PCB版本。

## DDR 核对

| 项目 | 本板资料 | 历史 PS7 配置 | 本次判断 |
|---|---|---|---|
| 颗数/位宽 | U3、U4 各16位，PS DQ0..31、4组DQS/DM | 总线32 Bit，profile 16 Bits | 资料结构一致；未确认实际两颗完整型号 |
| 容量 | 每颗4Gbit，两颗合计1GB | 每颗4096 MBits；行15、列10、Bank3 | `2^(15+10+3) × 16 × 2 / 8 = 1,073,741,824` 字节，即1GiB；与文档“1GB”及历史地址窗口一致，不表示 Linux 全部可分配 |
| 地址/片选 | A0..14、BA0..2、共享 CS0 | 行15、列10、Bank3 | 资料级一致；DQ字节内部重排不作为错误证据 |
| 料号 | `NT5CC256M16`，未给完整后缀 | `MT41J256M16 RE-125` | **不同厂家/料号，兼容性未证** |
| 电源 | DDR VDD/VDDQ 与 VCCO_DDR 标注+1.35V；VREF/VTT网络见第8页 | 参数摘录未发现直接给出 DDR 电源电压的字段 | 不能推断 profile 配置了1.5V，也不能判定1.35V适用已经满足；待准确器件/预设依据 |
| 频率 | 规格书上限533MHz/1066Mbps | 请求533.333333MHz，ACT533.333374MHz，DDR3_1066F | 在文档标称等级附近；不是实际频率、温压裕量或时序通过证明 |
| 延时/时序 | 未找到实际 PCB 走线延时或等价参数说明 | CL7/CWL6，tRAS35.0、tRC48.91、tRCD7、tRP7、tFAW40.0；四路 board delay均0.25、DQS-to-clock均0.0 | 保存参数原值，不凭此补填单位或实测结果；封装延时与板级延时分开，待对应PCB依据 |
| 训练 | 无新板端查询 | write/read/data-eye training配置开启 | 开启不等于训练通过，未执行训练或重测 |

`hardware/evidence/vivado-2025-2-environment-check.md` 既有“DDR兼容预设”称谓，旧 BD 配方 `system_c_adapter_bd.tcl` 第338行也确实选择美光料号；本次未找到南亚与美光预设的逐项等价依据。保留旧使用事实，把“已验证兼容”继续标为 UNVERIFIED。已有 Vitis/DDR/DMA 采录证据按原范围复用；用户指认的电脑 Python 舵机联调则是 PL UART 流程，不证明 PS DDR 或缓存。

南亚官方 [NT5CC256M16ER-DIB 产品页](https://www.nanya.com/en/Product/4251/NT5CC256M16ER-DIB) 可确认该完整型号例子为4Gb/x16/DDR3L，但 **ER-DIB 后缀未由实物确认**，不能用它替代板上器件或据此生成新预设。

## MIO、启动和复位依据

第4页按引脚连线及最右侧端口标号逐行核对；中间网络文字跨行排版不能作为 MIO 编号依据。

| 功能 | 核心板/底板文档映射 | 历史 PS7 状态 | 接续边界 |
|---|---|---|---|
| PS 时钟/电压 | 33.333333MHz；Bank500=3.3V、Bank501=1.8V | 晶振及Bank电压相同 | 配置与文档一致，没有实测电压/时钟 |
| QSPI | MIO1 CS，2..5数据，6时钟 | 启用，同映射 | 资料一致；不推断 Flash 当前内容 |
| PS UART | MIO14 RX、15 TX，经BTB与底板P5到CH340C | UART0启用，同映射、115200 | P5选择PS/PL通路；底板UART1/UART3是网络命名，不替代PS控制器编号。当前位置未知 |
| microSD | MIO40 CLK、41 CMD、42..45 D0..3；底板TXS02612由1.8V转换至3.3V | SDIO0/1禁用 | 可支持SDIO0的40..45引脚组；未选定CD/WP配置，不能猜卡检测MIO或直接认定已可SD启动 |
| PS 网口 | MIO16..27 RGMII，52 MDC、53 MDIO；核心板文档PS PHY为YT8521SC_CA | ENET0/1禁用 | 待核准确PHY/地址/延时/复位与驱动。底板PL PHY不同，不能混用 |
| PS USB OTG | MIO28..39，ULPI接口 | USB0/1禁用 | 仅有文档连线；不能按CH340串口代替USB控制器支持 |
| eMMC | MIO46 D0、47 CMD、48 CLK、49..51 D1..3 | SDIO0/1禁用 | 文档有其他启动存储；当前无SD不等于其他存储没有系统 |
| BOOT_CFG | 底板文档JTAG=ON/ON、SD=OFF/OFF，对应MIO4/5启动strap | 不由HWH代替strap | 本次仅保存文档，未查看当前位置或发出切换操作 |
| PS 硬件复位 | 核心板KEY1→HX811T→PS_POR_B；PS_SRST_B另行上拉 | HWH没有证明硬件时序 | 不与PL reset、FCLK_RESET0_N或RECOVER混同 |
| PL 外设复位 | 历史FCLK_RESET0_N→clk_wiz/rst；locked参与外设复位 | 原HWH连线已保存 | 仅历史设计；当前CPU/缓存/事务恢复合同待准确接合 |

SDIO0 40..45映射另与 [AMD UG585 的 SDIO 引脚表](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM/SDIO-Controller-Media-Interface-Signals) 核对一致。该静态对应不证明启动链、板级时序或驱动运行。

## 可核的 PYNQ 支持路径与最小准备材料

在本机 `hardware/document/software/task-packages` 的文件名清单内未找到本板匹配的 `.img`、`.bsp`、board XML/preset 或 device-tree 源；资料、旧采集 XSA 及接口指南已找到。公开官方资料检索也未识别与**本核心板修订**准确匹配的现成镜像；不据该有限搜索断言厂商没有提供镜像。

建议先取得厂商或已有归档中针对准确核心板版本的 **DDR/PS preset、Linux BSP或镜像说明**。若有本板匹配 PYNQ 镜像，核来源/hash、PCB与DDR支持、UART/SD/PHY及发布工具版本后复用；只有普通 Linux BSP时，作为PYNQ板级适配输入；确无匹配BSP时，才在原权威工程完成必要PS7启动配置并导出匹配XSA供板级适配。当前没有选择或安装任何镜像。

可参考 [PYNQ v3.0.0 官方自定义板流程](https://pynq.readthedocs.io/en/v3.0.0/pynq_sd_card.html) 和 [v3.0.1 源仓库说明](https://github.com/Xilinx/PYNQ/blob/v3.0.1/sdbuild/README.md)：Zynq-7000采用`arm`根文件系统，板相关BSP/启动产物与通用根文件系统分别准备。本例仅给可核支持路径，**不是选定3.0镜像**；v3.0.0文档工具基线为2022.1，本项目已有XSA来自2025.2，两者兼容未确认。当前`latest`文档的4.0示例是`aarch64`/ZCU104/Versal流程，不能直接套到XC7Z020。

下一可交付材料为：准确PCB/DDR识别；可追溯的DDR preset或逐项等价依据；原工程PS7中SD/UART及选用联网外设的完整配置；同构建XSA与init；对应FSBL/BOOT.BIN、U-Boot、kernel、DTB、rootfs/PYNQ版本清单；运行时Overlay bit/HWH和缓存/退休合同。前五项属于启动平台材料，Overlay接口接合继续原任务，不另搭同功能工程。现在不要求用户刷卡或运行尚不存在的板端查询。

需A/系统责任选择的事项集中为：①有匹配厂商镜像/BSP时是否复用，否则采用哪条支持Zynq-7000的PYNQ与工具版本路线；②准确DDR预设及是否需要有依据的参数修订；③实际联网通路与CPU/DMA缓存、持久所有权和复位恢复接口。此资料不冻结公共ABI，不以旧裸机固定内存区替代Linux allocator。

## 本次具体缺项

- **用户只需在已有资料或可见丝印里补两项**：核心板PCB版本、两颗DDR完整型号及后缀。DDR在已有照片中Zynq大芯片左侧；版本在小核心板边缘/背面，不是底板V3.9。看不清则保留UNKNOWN，不要求拆板。
- **工程资料待补**：对应核心板版本的厂商preset/BSP或DDR参数适用说明、实际板级走线延时，以及将采用的PYNQ/工具版本和匹配启动配置。这些需要原件或设计依据，不让用户凭记忆确认电气兼容。
- **现场运行仍未知**：当前没有SD卡（USER_REPORTED）；镜像/kernel/PYNQ/驱动/cache/write-completion信息仍UNKNOWN。首次匹配平台真正启动后再保存原始事实。

用户对旧电脑Python联调“没有按过复位键，没有重新上电”的陈述已保存于 [historical-python-board-operation.json](../historical-python-board-operation.json)，仅作用于该次测试。旧主机串口写出STOP也不等于板端drain/停止ACK或DMA写入完成。旧测试继续复用，本次没有重跑。
