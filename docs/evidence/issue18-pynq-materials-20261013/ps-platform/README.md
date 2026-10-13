# 已有平台与 PS 配置查找结果

2026-10-13；只读原件、解包和元数据比对，未运行旧测试、EDA、初始化脚本或板卡。旧角度结果为**电脑 Python** 计算；声音采集由 **Vitis** 完成。这两项均不构成 PYNQ 运行证据，原日志/候选绑定仍未知。

## 原件和适用范围

在既有 Vitis 采集工作区找到 `files/system_continuous_20260915.xsa`，其 SHA256 为 `b84e93631132a3838cc9dadc1ce9037f2685d4d10de0b1655c76291663a8f60b`。该原件也已保存于[固定基线的历史采集目录](https://github.com/TophBeifong1744/Competition_fpga/blob/995fe0a802b572353c45a3669714c1292fe0fa52/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/board-run-20260915-02/runtime/system_continuous_20260915.xsa)。其 13 个成员的尺寸、SHA256、CRC 和提取包身份见 [source-manifest.json](source-manifest.json)。生成器为 Vivado 2025.2，顶层为 `system_wrapper`，器件为历史配置 `xc7z020clg400-2`；当前用户确认和 C 保存的 live-loop 工程为 `xc7z020clg400-1`。历史参数不能替代当前器件的实现/时序结果。

| 文件 | 查找结果 | 使用边界 |
|---|---|---|
| 历史 XSA | 已找到，与固定 Git 原件逐字节身份一致 | 历史 C1 采集设计 |
| 顶层 HWH | XSA 内 `system.hwh`，SHA256 `892fbe060f0d3455245a463ef45b5d04a915f12eaac90c1a30a749ab1bc62eb6` | 包含 PS7、DMA、GPIO 和连线 |
| scoped HWH | XSA 内 `system_axi_smc_1.hwh` | SmartConnect 内部子设计，不含 PS7，不能代替顶层 HWH |
| PS 初始化 | XSA 内及 Vitis 工作区已有 `ps7_init.c/.h/.tcl` | 原件保存；没有执行其硬件写操作 |
| 历史 BSP | 已有 `xparameters.h` | 与 HWH 的 11 项地址/配置元数据比对一致；不是运行测试 |
| 当前 live-loop XSA/HWH/BD | `D:/vavido_project/i17_live_loop` 完整文件清单中未找到 | 仅该搜索范围；不推断 A 机当前产物不存在 |
| 当前 PS/CPU 接合 | C 保存 XPR 仍为 `i17_vio_board_top`，声明中未发现 PS7/BD/DMA/GPIO 文件 | 见原 [XPR 观察](../native-project-observation.json)；不能证明任意 RTL 内没有总线逻辑 |

XSA 的 `xsa.json` 标注 `platformState=pre_synth`，而 `sysdef.xml` 标注 `Post-Synthesis`；两者原样保留。包内含 bit，不据这些标签判定实现或时序通过。完整搜索范围、当前 XPR 身份和本地初始化原件身份见 [search-observation.json](search-observation.json)。

## 从 HWH 读出的历史配置

下表均为**配置值和已声明连线**，不是板上测量或实物 DDR 型号确认。完整 PS7 的 937 项参数、54 个 MIO 分配、九个模块的端口/总线/地址映射见 [ps-config.json](ps-config.json)。

| 项目 | 历史配置/连线 |
|---|---|
| PS | `processing_system7_0`，PS7 5.5；Zynq-7000 |
| DDR | DDR3；配置料号 `MT41J256M16 RE-125`；总线 32 Bit、芯片 profile 16 Bits；频率请求 533.333333 MHz，ACT 参数 533.333374 MHz；DDR3_1066F；ECC Disabled |
| DDR 地址 | PS 配置 `0x00100000..0x3FFFFFFF`；HP0 的 DDR_LOWOCM 地址映射 `0x00000000..0x3FFFFFFF`。这些是地址窗口，不能当作 Linux 可分配范围 |
| MIO | QSPI：MIO1片选、2～5数据、6时钟；UART0：MIO14 RX、15 TX，115200；其余 MIO 在树中为 unassigned |
| 外设 | QSPI、UART0 启用；SDIO0/1、ENET0/1、USB0/1、UART1 禁用 |
| GP/HP | M_AXI_GP0 启用、32位；S_AXI_HP0 启用、32位；其余 GP master、HP1～3、ACP 未启用 |
| CPU 控制路由 | GP0 → `axi_smc` → DMA AXI-Lite / AXI GPIO |
| 地址 | DMA `0x40400000..0x4040FFFF`；GPIO `0x41200000..0x4120FFFF`。只属于历史设计，当前控制/结果 ABI 仍 UNBOUND |
| DMA | AXI DMA 7.1；simple S2MM=1、MM2S=0、SG=0、S2MM DRE=0；长度字段14位；输入 AXIS32位，内存侧64位 |
| 采集路由 | `four_mic_top_0` AXIS → DMA S_AXIS_S2MM → M_AXI_S2MM64位 → `axi_mem_intercon` → PS HP0/32位 |
| IRQ | PS `PCW_USE_FABRIC_INTERRUPT=0`，无 IRQ_F2P 端口；DMA s2mm_introut 未连线；GPIO interrupt=0。没有可引用的 DMA→PS IRQ 映射 |
| GPIO | dual=1；通道1为1位输出，直接到四麦 start；通道2为32位输入，接四麦 status。`start_pulse_0/start` 输出未连线；不能用模块名推断实际控制为脉冲 |
| 时钟 | PS FCLK0 配置100MHz → clk_wiz 输入100MHz → 输出61.44MHz，供四麦及 AXI/GP0/HP0 时钟；不是当前 live-loop 的50→96→61.44MHz链 |
| 复位 | PS FCLK_RESET0_N → clk_wiz/resetn 与 rst/ext_reset_in；rst外部复位低有效；clk_wiz locked → rst/dcm_locked，61.44MHz → slowest_sync_clk；peripheral_aresetn 驱动采集/AXI外设 |

这些连线不证明复位释放、CDC 或 STA 合格。历史 GPIO RUN 电平协议也不是 PR #63 的 CONFIG/RUN/STOP/RECOVER 命令 ABI。当前命令缓存、结果原子快照、原 PCM 导出及 IRQ 绑定仍由实际接合工程确定。

## 原件提取和复核入口

[inspect_platform.py](inspect_platform.py) 仅用 Python 标准库，读取 XSA/HWH 和可选旧 BSP，输出 JSON 与保留原始字节的九文件参考包；不调用 Vivado/Vitis、不执行 init、不连接板卡。将下载的历史 XSA 放到独立输入目录，运行：

```powershell
python docs/evidence/issue18-pynq-materials-20261013/ps-platform/inspect_platform.py --xsa 'C:/path/to/system_continuous_20260915.xsa' --out codex_out/i18-ps-platform-reference
```

本轮额外给 `--bsp codex_out/i18-short-real-delivery-20261006/package/bsp/include/xparameters.h` 做了 11 项元数据比对。预期输出：`ps-config.json`、`source-manifest.json`、`historical-ps-reference.zip`。参考 ZIP 含两份 HWH、init C/H/Tcl、sysdef、BDA、XSA JSON/XML；不含 bit，不是可加载 Overlay，也没有新建工程。B 可从固定 Git XSA 复现提取，无需重跑采集。当前输出保存在本仓库 `codex_out/i18-ps-platform-20261013/`，厂商原件不重复进入活动源码。

PYNQ 启动镜像负责配置 PS 的 DDR、SD、网口、USB、UART 等，Overlay 的 bit/HWH 另需匹配；本历史 PS 配置不能证明当前镜像兼容。依据 [PYNQ 官方 Overlay 文档](https://pynq.readthedocs.io/en/latest/overlay_design_methodology/overlay_design.html)。

下一步：A 在原总工程交当前 PS7/控制与采集桥的同构建 XSA、bit/HWH 和必要报告；B 可先用这些历史配置完成接口核对和离线软件工作。C 当前无需补做旧角度测试或重采音频。实际 PYNQ 镜像及板端运行时仍 UNKNOWN，不能由这些工程原件反推出名称/版本。
