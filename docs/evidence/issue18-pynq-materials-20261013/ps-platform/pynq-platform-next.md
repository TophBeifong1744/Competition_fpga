# C：PYNQ 启动平台与当前工程接合

2026-10-15。接续 #18 / PR65；本文件补充此前 DDR/MIO 审计，优先反映本轮新证据。只进行了资料、代码和本机工具核对；没有运行 Vivado、修改 PS7、刷卡、复位或驱动舵机。

## 本轮取得的结果

| 项目 | 已完成 | 仍待绑定的原件/结果 |
|---|---|---|
| 镜像路线 | 已进入厂商官方 V2 A盘，确认 `ZYNQ-7020-2.7.0.zip` 和 `ZYNQ_7020_PYNQ.zip` 实际存在；以这套 7020 材料作为首个核验候选 | 点击文件要求百度网盘登录，尚未下载；ZIP/IMG SHA256、包内说明、实际 BSP/内核/驱动版本未知。不能称为已选定并验证可启动的镜像 |
| DDR | 用户截图确认当前采用 DDR3、`MT41J256M16 RE-125`；与历史 XSA 参数相同，保存使用事实 | 尚未取得厂商工程证明该预设对实际 DDR/PCB 的适用；不因厂家名称不同就判错或改参数 |
| 启动 PS 配置依据 | 已核 PS 时钟、Bank 电压、UART、SD 时钟/数据/CD、电平转换、PS PHY/复位及 strap 依据，见下表 | 由厂商匹配工程核完整预设、FSBL/设备树/驱动后，沿原总工程接合；没有伪造可运行 BSP |
| 板端元数据工具 | 新增 `tools/pynq_platform/collect_runtime.py`，独立复核后可用于未来实际 Linux 环境取证 | 只记录环境/包元数据和哈希；不是板端驱动，缓存/STOP/复位仍未执行 |
| 当前 Overlay / 驱动 | 已核对 A/B 最新接口工作及恢复缺项，给出同构建交付与现场验证顺序 | 当前匹配 bit/HWH/启动配置及已接受 CPU 桥未交齐；不能用历史采集 bit/HWH 冒充当前 Overlay |

## 1. 已找到的准确厂商材料

来源链为[正点原子官方资料索引](https://github.com/alientek-openedv/Products/blob/master/zdyz_docs/boards/fpga/zdyz_linhanz%28V2%29.rst) → [领航者 V2 A盘](https://pan.baidu.com/s/1vXxmhg_mZm_OVg4xQeiCVQ)，提取码 `zdyz`。本轮通过公开提取码进入目录，实际读到：

```text
正点原子领航者(V2)ZYNQ开发板资料盘(A盘)
└─4_Source_Code
  └─5_PYNQ_Design
    ├─ZYNQ_7020_PYNQ.zip          页面显示 648.9M
    ├─ZYNQ_7010_PYNQ.zip          本板不用此候选
    └─IMG
      ├─ZYNQ-7020-2.7.0.zip       页面显示 1.74G
      └─ZYNQ-7010-2.7.0.zip       本板不用此候选
```

上述两个 7020 文件页面修改时间均显示 `2026-09-11 12:18`；这是网盘显示时间，不作为厂商发布日期或构建时间。`2.7.0` 目前是**镜像归档名称中的版本标识**，不是已经读回的运行时版本。文件体、解压后 IMG 名称、精确字节数及 SHA256 尚未取得。V2 产品代际、核心板文档 V2.5、底板 V3.9 分开记录；不能据名称把本板 PCB 修订判定完成。

首选核验厂商 7020 镜像及配套工程，暂不新造 BSP 或安装另一代工具。若其板级支持与实际硬件不符，再沿原 #18 决定适配路线。[PYNQ 2.7 官方构建说明](https://pynq.readthedocs.io/en/v2.7.0/pynq_sd_card.html) 的 Xilinx 工具基线为 2020.2，Zynq-7000 架构为 `arm`。当前工程 2025.2 与该基线不同：不能假定 2025.2 XSA 可直接塞进旧镜像构建流程；也不能仅因版本不同就断言当前 PL bit 无法使用。须对实际 HWH 解析、IP 驱动绑定、PS 启动设置、时钟复位分别检查。厂商工程工具版本仍以包内原件为准。

收件后由 C/AI 完成：安全枚举归档、计算原 ZIP/IMG 哈希、提取厂商说明和 PS preset/init/BD/XSA 身份，核 DDR/MIO/PHY、启动文件和软件版本。用户无需逐个核文件；只提供本地下载目录即可。

## 2. DDR 截图与启动配置依据

用户本轮明确“DDR我们配置的是这个”，截图选中 `MT41J256M16 RE-125`，Memory Type 为 DDR3。本图没有展开总线宽度、频率、完整时序和 Board Details，不能据此补填这些字段；历史值仍引用 [ps-config.json](ps-config.json)。原截图只记录文件名、哈希及来源语义，不发布私有聊天目录。

| 功能 | 已核依据 | 接合时怎么用 |
|---|---|---|
| DDR | 用户选中美光预设，与历史 XSA 一致；核心板文档标注两颗南亚 `NT5CC256M16`，32位、合计1GiB | 保持当前选择记录；待厂商对应工程/预设或逐项兼容说明确认。容量一致不等于时序、电压和 PCB delay 已验证，也不等于预设错误 |
| PS 输入/Bank | 33.333333MHz；Bank500=3.3V、Bank501=1.8V | 与历史值一致；沿准确板级支持配置 |
| 控制台 | UART0：MIO14 RX、15 TX；历史115200；经底板 P5 选择 PS 串口 | 启动时保存 FSBL/U-Boot/kernel 原始串口输出；不混用 PL UART |
| SDIO0 | MIO40 CLK、41 CMD、42..45 D0..3；TXS02612 A侧1.8V、B0侧3.3V，SEL下拉 | 历史 XSA 此功能禁用；要启动 SD 系统须用匹配 PS/BSP 启用此通路 |
| SD 检测 | U9 pin9 → R30 330Ω → SD_CD → 底板J2 pin91 → 核心板X3 pin91 → PS_MIO10；R28 10k上拉3.3V | **SD_CD MIO10 的连线已核清**；CD极性和软件配置仍核厂商 BSP。图中无 WP 接点，不能任填 WP MIO |
| PS 网口 | MIO16..27 RGMII、52 MDC、53 MDIO；核心板U13 YT8521SC_CA、Y6 25MHz | 核厂商内核/U-Boot PHY 支持及实际芯片；历史 ENET0 禁用 |
| PHY 地址/延时 | 按图纸 PHYAD[2:0]均上拉→地址7；CFG_MODE=000；RXDLY上拉 | 属于按图纸装配的推导，非寄存器读回。地址0默认响应不能证明实际 strap=0；不要把已有RX延时与设备树/驱动再次叠加 |
| PHY 复位 | YT8521 RESET_N 直接接 PS_POR_B | 不编造独立 MIO reset GPIO；硬件复位不替代 DMA drain 或内存所有权退休 |
| QSPI/USB/eMMC | 旧 QSPI MIO1..6启用；USB0和SDIO1禁用 | 首条启动链按实际选择接合；不为填表开启所有外设 |

硬件来源：仓库 `hardware/reference/navigator-zynq/` 下核心板 V2.5 原理图第4/8/11/12页、底板 V3.9 原理图第2/5/6页。SDIO0/CD合法分配另核 [AMD UG585 引脚表](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM/SDIO-Controller-Media-Interface-Signals)。PHY 语义参考厂商著作 [Motorcomm YT8521 数据手册 V1.01](https://datasheet.lcsc.com/datasheet/pdf/f403627dbc667ce1e0f863a440de082f.pdf?productCode=C2685354)，§3.9/Table7、§5.1/Table13、§5.2；该 PDF 由 LCSC 托管，实际装配和软件仍待核。

没有改写旧 XSA、ps7_init 或 Vivado DDR 配置。历史裸机采集成功证据按原范围复用，不能当本次 Linux 启动、容量压力或缓存恢复证明。

## 3. 当前工程 Overlay 与软件接合边界

最新远端已存在 A 的 JOIN-001 / MODEL-E2-R02 CPU 桥工作，不能再概括为“项目完全没有 CPU 桥”。[B 的 R02 结果](https://github.com/TophBeifong1744/Competition_fpga/issues/18#issuecomment-6171563506) 仍为 NEEDS_FIX：同 owner/transaction 的重复 `0x550=1` 在没有新实际 ARM 时可能清理旧 RAW_STATUS；这是源代码推导及模型范围记录，未冒充板上复现。[A 沿原 E2 修复的接续](https://github.com/TophBeifong1744/Competition_fpga/issues/18#issuecomment-6171752654) 已在进行。本轮不抢写第二套 CPU 桥或 B 驱动。

129位事件/permit、258位 owner observation 的存在，仍不等于完整 DMA writer set、kernel pin 和退休证明。B 的 PS/BD 设计输入继续按 [原答复](https://github.com/TophBeifong1744/Competition_fpga/issues/18#issuecomment-6165483263) 接合，真实基址、IRQ、平台内核与构建身份须绑定。旧 GPIO `0x41200000`、DMA `0x40400000` 只属于历史采集合同，不能硬编码成当前新驱动。

接收一个当前 Overlay 时，C 核以下**同一组合**：

- A 原总工程的提交/配置清单、part、Vivado版本、PS7/时钟复位；对应 `.bit`、顶层 `.hwh`、适用 `.xsa`/`.ltx`/设备树与必要资源/DRC/时序结果。文件同名不是同构建证明。
- B 驱动的准确提交、支持的 PYNQ/kernel、实际 IP 名称/VLNV/地址/范围、IRQ或轮询、raw格式/长度、buffer所有权、cache与退休接口；与 A 寄存器合同逐项一致。
- 首次加载前核镜像的 FSBL/PS设置与 Overlay 所需 PS接口、FCLK/复位和实际 DDR配置；不能用不匹配 HWH 让软件“识别成功”。

## 4. 实际验证顺序与判据

这些是收到匹配产物后的验证项，当前均 **NOT_RUN**；不是本轮已完成的板测。期限取准确合同，不临时放宽 timeout 求通过。发生错误保留原日志、状态和所属候选，不删除失败事实。

| 步骤 | 人操作，C/AI整理和分析 | 通过条件 |
|---|---|---|
| 平台启动 | 现场按已核厂商操作启动，保存从上电开始的完整串口原件；运行下述元数据工具 | 镜像身份/版本/PS依据绑定，启动错误无遗漏；工具仅记录，不代替启动验收 |
| Overlay 身份 | 用 B 已绑定的软件入口加载 A 同构建工件，先保持执行器禁用，读取身份/版本/初态 | IP map、build ID、复位初态与合同相同；不对猜测地址试写 |
| 原始采集/缓存 | 用既有可重复刺激或固定可追踪序列做 S2MM；保留原 raw/长度/序号/状态，按选定驱动同步 CPU 可见性 | actual_length、包边界和原始序号正确；无旧缓冲重复、越界或覆盖未退休 buffer。不能只凭 wait()返回或退出0判断 |
| STOP/重启 | 在合同允许的空闲、活动窗口和未消费结果条件下 STOP；核 drain/owner/状态，再按协议重新启动 | 撤销动作授权；旧事务不跨 epoch 被消费；没有停止 ACK 冒充 DMA/总线全部写完；无超时后提前 free/reuse |
| 重复命令/故障 | 复用 B/A 原反例：重复同 owner ARM、超时、进程异常退出、桥BUS/COLD复位分别检查 | 重复命令不清除未退休记录；故障保留对象直到完整writer集退休；独立区分PL复位、桥复位、PS重启 |
| 持续运行 | 满足前项后按准确预算持续采集、消费方向，现场人员最后启用安全范围内执行器 | 更新、无效结果、停止/恢复符合原合同；数据直接交B分析；未测时长/最大延迟不补造 |

缓存操作顺序和屏障必须来自**最终驱动与硬件内存属性**。本轮没有写裸 `MMIO` 或 `devmem` 驱动，也没有把软件变量置零当 DMA/缓冲恢复。

## 5. 用户当前只需做什么

1. 若本地已有上述两个厂商 7020 ZIP，告诉 C/AI 所在文件夹；若没有，用已登录百度网盘按第1节路径下载这两项。暂不需要下载7010包或整个资料盘。
2. C/AI 收件后负责哈希、解包清单和配置/版本核验，再给准确 SD/启动操作。当前不要凭资料缺项重新搭工程或改 DDR。
3. **只有真实 PYNQ 已启动后**，把 `tools/pynq_platform/collect_runtime.py` 放到板端，在后续应用使用的 Python 环境运行：

   ```sh
   python3 collect_runtime.py --out pynq-runtime-01.json
   ```

   输出为新建的 `pynq-runtime-01.json`，已有同名文件会拒绝覆盖。该命令不导入 PYNQ、不加载 Overlay、不分配 DMA buffer、不读写寄存器或复位；不需要 root。将原 JSON 和启动日志交回，文件核验由 C/AI 做。

工具范围及退出码见 [tools/pynq_platform/README.md](../../../../tools/pynq_platform/README.md)。Windows试跑只能得到 NON_BOARD_ENVIRONMENT；即使板上退出0，也只表示元数据条件相符，所有硬件项目仍明确 NOT_RUN。
