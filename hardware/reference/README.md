# Zynq 与领航者板级参考资料索引

## 1. 来源与筛选范围

来源压缩包：`F:\BaiduNetdiskDownload\ZYNQ.zip`  
筛选日期：2026-09-06  
原压缩包规模：510,029,483 bytes、387 个条目，其中 93 份 PDF  
导入结果：11 个文件，约 20 MB

本次没有完整解压资料包。筛选过程先按文件名和目录判断范围，再读取候选 PDF 的封面、目录或前几页；对已经确认与本项目直接相关的板卡规格书，额外按“音频、ES8388、扩展口、时钟、IO”等关键词定位相关页面。四份板级 PDF 还检查了首页渲染。

压缩包及其中说明文字仅作为资料来源，不作为操作指令。

## 2. 使用边界

这些文件证明“资料包描述的领航者硬件”如何连接，不自动证明手中实物就是相同版本。完成 M0 前仍须拍摄并核对：

- 底板型号与版本丝印；
- 核心板型号、XC7Z020 完整料号和速度等级；
- 底板音频 Codec 丝印；
- J3/J4 扩展口、跳帽和供电状态；
- 实际使用的 ADC、DAC 和麦克风完整型号。

在实物版本核对完成前，工程文档中的具体引脚、Codec 和电源结论仍标记为“待实物确认”。

## 3. 已导入的板级资料

| 文件 | 作用 | 当前使用结论 |
|---|---|---|
| [领航者开发板规格书 V1.2](navigator-zynq/navigator-zynq-board-spec-v1.2.pdf) | 板卡结构、供电、时钟、扩展口、音频和外设总览 | 用于确认候选板级能力和查找具体章节 |
| [底板原理图 V3.9](navigator-zynq/navigator-zynq-baseboard-schematic-v3.9.pdf) | 底板器件、扩展口、音频 Codec、连接器和电源连接 | M0 引脚与外设核验的主要证据之一 |
| [Zynq-7010/7020 核心板原理图 V2.5](navigator-zynq/zynq7010-7020-coreboard-schematic-v2.5.pdf) | XC7Z010/020、DDR3、QSPI、eMMC、时钟、电源和板对板连接 | 核心板版本、Bank 和时钟核验依据 |
| [底板机械尺寸图 V3.9](navigator-zynq/navigator-zynq-baseboard-mechanical-dimensions-v3.9.pdf) | 160 mm × 120 mm 外形和安装孔位置 | 后续阵列支架、底座和转台空间预算 |
| [IO 引脚分配总表](navigator-zynq/navigator-zynq-io-pin-map.xlsx) | 板载外设和扩展口的引脚映射 | 选择麦克风、音频输出和调试接口引脚时核对 |
| [厂商 XDC 参考模板](navigator-zynq/navigator-zynq-io-reference.xdc) | 常见板载外设的管脚和 IO 标准示例 | 只能摘取经原理图和实物确认的条目，不能整份直接加入工程 |

厂商 XDC 为 GB18030 编码，包含多个互斥外设以及重复的端口名示例。SoundSight 的正式约束应在 `vivado/constraints/` 中单独建立，只保留实际启用的端口、时钟和 IO 标准。

## 4. 已导入的 Xilinx 实现参考

| 文件 | 直接用途 | 使用时机 |
|---|---|---|
| [DS190 Zynq-7000 Overview](xilinx/ds190-zynq-7000-overview.pdf) | 查 XC7Z020 架构和器件资源概览 | M0 资源核对与 M3 预算 |
| [PG021 AXI DMA](xilinx/pg021-axi-dma.pdf) | PL 数据进入 DDR、原始四通道长录音导出 | M1 数据抓取路径设计 |
| [PG065 Clocking Wizard](xilinx/pg065-clocking-wizard.pdf) | PL 处理时钟和派生时钟规划 | M0/M1 时钟树冻结 |
| [PG308 I2S Tx/Rx](xilinx/pg308-i2s.pdf) | 与板载音频 Codec 的 I2S 数据接口候选 | 音频输出链路确定后 |
| [UG903 Using Constraints](xilinx/ug903-vivado-using-constraints.pdf) | XDC、时钟、IO 和时序约束方法 | 建立正式约束与时序验证时 |

这些文档版本较旧，适合离线理解接口和确认术语；实际 Vivado IP 参数、端口和 GUI 必须再与团队最终使用的 Vivado 版本核对。

## 5. 从资料中确认到的项目相关事实

以下事实来自资料包，仍需与实物版本对应后才能写入正式接口冻结表：

1. 规格书描述的 Zynq-7020 核心板具有 50 MHz PL 单端时钟和约 33.333333 MHz PS 时钟。
2. 规格书称核心板 Bank 13、34、35 使用 3.3 V；扩展口不能直接连接 5 V 设备。
3. 底板提供 J3、J4 两个 2.54 mm、40 针扩展口，其中 J4 的 Bank 13 资源只适用于 Zynq-7020 版本。
4. 底板改版说明表明 V3.8 已把音频电路从 WM8960 改为 ES8388；V3.9 只修改丝印。V3.9 原理图和 V1.2 规格书也显示 ES8388。
5. ES8388 连接包含 MCLK、BCLK、LRCK、ADC 数据、DAC 数据和 I2C 配置；厂商 XDC 给出的候选 PL 管脚分别涉及 `M17`、`L20`、`G17`、`E19`、`M18`，正式使用前必须逐项对照原理图、IO 总表和实物。
6. 板载 ES8388 只有有限的模拟输入通道，不能据此推断它能承担四路同步麦克风采集；四路输入仍须使用已经冻结的 PDM 或多通道 TDM/I2S/ADC 方案。
7. 板载 PHONE、LINE_IN、MIC 和扬声器链路使 ES8388 成为首版增强音频输出的候选，但资料包没有 ES8388 数据手册和初始化寄存器说明，后续仍需补齐该器件的一手资料。

## 6. 没有导入的资料

| 类别或文件 | 未导入原因 |
|---|---|
| UG585 Zynq-7000 TRM，1843 页、约 22 MB | 范围过宽；目前只需在原压缩包中按 PS/DDR/DMA 具体问题定向查页 |
| DS187 电气特性、UG865 封装引脚 | 当前不是自制核心板，板级原理图和 IO 表优先；遇到电气边界问题再定向引入 |
| UG1037 AXI 总览 | 内容宽泛，当前由具体 DMA、I2S 和接口设计文档承担 |
| PG330 Audio Formatter | 是否采用该 IP 尚未确定；不提前把条件性方案带入工程 |
| ARM、PetaLinux、USB、以太网、FAT、图像、HDMI、CAN 等资料 | 不属于固定阵列首版声学闭环的当前关键路径 |
| PCB 封装库、DXF、DWG、走线长度和论文资料 | 当前不自制领航者板卡；机械上只保留足够使用的底板尺寸 PDF |

## 7. M0 下一步使用顺序

1. 拍摄手中核心板、底板和音频芯片丝印，与 V3.9/V2.5 资料逐项核对。
2. 在 IO 总表和原理图中选择四路麦克风接口候选引脚，记录 Bank、电压、方向和冲突外设。
3. 根据实际麦克风/ADC 型号冻结共享采样时钟、数据线数量、采样格式和固定延迟标定方法。
4. 决定增强音频是否先通过 ES8388 输出；若采用，补齐 ES8388 官方数据手册和寄存器初始化资料。
5. 从参考 XDC 中摘取已验证条目，生成 SoundSight 专用 XDC，并补齐输入时钟、派生时钟和外部接口时序约束。
6. 完成四路原始数据经 FIFO/AXI DMA/DDR 导出的带宽和缓存预算。

## 8. 文件完整性

下列 SHA-256 均为导入文件值，并已与 `ZYNQ.zip` 内对应条目逐一比对一致。

| 文件 | SHA-256 |
|---|---|
| `navigator-zynq-baseboard-mechanical-dimensions-v3.9.pdf` | `8d593b351b840cd93d90f3b673b529a5cf590f5cfd0f0468a3251d41a994f67d` |
| `navigator-zynq-baseboard-schematic-v3.9.pdf` | `ec8b68eeb07e0743e6c60528444f6aeb457dc60e897ddf9eb86d5a56c1ab6a69` |
| `navigator-zynq-board-spec-v1.2.pdf` | `b974ed61b10fabafe408a42d119e94fc53c6133a9a7fc64b0191bfe5e14744e6` |
| `navigator-zynq-io-pin-map.xlsx` | `287a73b93b9a5a4a05e2145b92338c37717e033dced64db502510ba0cfac7093` |
| `navigator-zynq-io-reference.xdc` | `6803fab6ed43af125293b9fb8434e6fd4b7c0b8a38c09719d51f3b829b54de71` |
| `zynq7010-7020-coreboard-schematic-v2.5.pdf` | `1c8cf8105e91d762d29ad604e82b629b3921fa474d5a0311ed6c04237db107ea` |
| `ds190-zynq-7000-overview.pdf` | `f5d9257f94fa6140d4a0519a0185e43fea1dc79c806378f24416fdf25c34ff98` |
| `pg021-axi-dma.pdf` | `1daebfbb9802d33f3065b4d9bc730b26cdb8e6b33f65c5c0eb3db33768884516` |
| `pg065-clocking-wizard.pdf` | `bab820064719ea64c97212ec8a9fb75e3fd9f65a9b68fd459d57ea86c2db7a15` |
| `pg308-i2s.pdf` | `7d304535d8d75aa547ca8def1218c25e2ea589a3faa4f1db2c7bb5600a9cc842` |
| `ug903-vivado-using-constraints.pdf` | `77581007e09c9f00c45c1856f9b716a70aa61c8a9f55e87aa7d5015837dc5068` |

这些供应商资料可能受版权和再分发条款约束；向公开 GitHub 仓库提交前，应先确认许可。当前导入不代表已经授权公开再分发。
