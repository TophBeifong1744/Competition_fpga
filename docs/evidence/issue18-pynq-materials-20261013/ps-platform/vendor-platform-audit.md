# C：厂商 PYNQ 镜像、PS 配置与现有工程接合核验

日期：2026-10-15。接续 #18 / PR65。依据用户下载的两个原 ZIP、镜像内部原字节及现有工程文件；未运行 Vivado/Vitis，未启动镜像、刷卡、复位或驱动执行器。

**收件和离线核验完成；当前镜像需要先适配已确认的 `xc7z020clg400-1` 启动时钟，不能作为本板可直接启动的合格发布。** 当前 SoundSight 匹配 Overlay、实际硬件 adapter、缓存/退休/复位实测仍未完成。完整机器可读事实见 [vendor-platform-20261015.json](vendor-platform-20261015.json)。

## 原件身份与完整性

原 ZIP 均由用户放在 `D:/BaiduNetdiskDownload/`。来源为此前核过的[正点原子官方资料索引](https://github.com/alientek-openedv/Products/blob/master/zdyz_docs/boards/fpga/zdyz_linhanz%28V2%29.rst) → 领航者 V2 A盘 → `4_Source_Code/5_PYNQ_Design`。CRC和本地哈希证明本次文件完整性/身份；没有厂商签名，不能把自行计算的哈希当厂商认证。

| 原件 | 精确字节数 | SHA256 |
|---|---:|---|
| `ZYNQ_7020_PYNQ.zip` | 680414199 | `cbe2a09fdf2efaa262463b20c3fe745dd2536ccefb3d93a397ca7660de85676b` |
| `ZYNQ-7020-2.7.0.zip` | 1869237643 | `40a1d904e2e2809bc173d0a3aaac40e57ace3c5cef533b4be11e87ddfb71dfe8` |
| 解出的 `ZYNQ-7020-2.7.0.img` | 8090591232 | `a9a486753b8aa61239c745b258311b795d665f69cca0e9ee12a1127e51eb107a` |

两个 ZIP 全成员读取/CRC 通过，归档成员路径检查通过。IMG 保存在仓库 `codex_out/vendor-pynq-7020/`。采用只读 FAT/ext4 解析，未挂载或执行镜像内容；没有重写 IMG。临时解析器为 dissect.extfs 3.15、dissect.fat 3.13，局部安装在本次 `codex_out`，不改变全局 Python 环境。

参考原件保存在 `codex_out/i18-vendor-inspection-20261015/reference-package/`，含原 PS XCI/BD/HWH/XSA/init、镜像启动文件及相关软件源码。它是证据摘取包，**不是完整可打开的 Vivado 工程，也不是当前 SoundSight Overlay**。完整厂商工程仍以用户原 ZIP 为准。未把厂商 base 整套导入现有总工程。

## 已从镜像内部确认的版本

以下是离线镜像内容，不是板端运行读回。

| 项目 | 原件证据与结论 |
|---|---|
| 系统 | `/usr/lib/os-release`：PynqLinux 2.7 Austin，基于 Ubuntu 20.04 |
| PYNQ / NumPy | 镜像虚拟环境 METADATA：PYNQ **2.7.0**、NumPy **1.20.3** |
| Python | dpkg：python3.8 **3.8.2-1ubuntu1 / armhf**；环境目录 `/usr/local/share/pynq-venv/` |
| 内核 | 从 `IMAGE.UB` 内核载荷解压得到版本字符串：**5.4.0-xilinx-v2020.2**；模块目录同版本。内核字符串含 2025-08-27 构建时间，不据此改称另一 PYNQ 版本 |
| U-Boot | `BOOT.BIN` 原字节包含 **U-Boot 2020.01 (Aug 27 2025 - 08:06:35 +0000)** |
| 厂商镜像修订 | `REVISION` 原文：`Release 2025_08_27 59515a9`，Board 同标识；该短标识不单独证明完整源码/构建可复现 |
| 分区 | FAT32 启动分区：sector 8、266240 sectors；Linux 分区：sector 268288、15533648 sectors；sector=512B |
| 启动文件 | FAT 中有 `BOOT.BIN`、`IMAGE.UB`、`BOOT.SCR`、`BOOT.PY`、`REVISION`；FIT 内核和 FDT 的 SHA1 均与 FIT 内记录一致 |
| 设备树 | DDR 地址窗口 `0..0x3fffffff`（1GiB）；UART0控制台115200；根文件系统 `/dev/mmcblk0p2`；此窗口不等于Linux可分配内存 |
| 网络 | 镜像文件配置 eth0 DHCP，同时有静态别名 `192.168.2.99/24`；只是配置，未验证实际网口或地址可达 |
| 完整 BSP | 工程 ZIP 没有 PetaLinux `.bsp`、`project-spec`、镜像构建配方或完整系统源码。已有镜像/示例工程不能称为可复现完整 BSP |

启动文件 SHA256：

```text
BOOT.BIN  b27be32e9b1548a503f570d072a1d1fc0ac5556c5ec69d103d431e9a9a050be6
IMAGE.UB  b502ca462cb57a43834c5cd0756ac38c6a28d6760cf27e942ea97dacd36c91f1
system.dtb fccff7706a23c8b46a5ecc7e131f02ec92fb35fa065596230e219f2241456d55
```

## 厂商 PS 配置与既有工程的关系

厂商 `base/base.xpr` 为 **Vivado 2020.2 / xc7z020clg400-2**。源 PS XCI 的878项参数与 `ready_to_test/base.hwh` 全部一致；该 HWH 与 `system.xsa` 内 `base.hwh` 字节相同。以下配置不是从文件名猜测。

| 项目 | 厂商 base | 可复用范围 |
|---|---|---|
| DDR | `MT41J256M16 RE-125`，DDR3_1066F，32位总线，533.333333MHz | DDR参数组与历史四麦采集 XSA 一致，也与用户截图的预设一致；预设选择已有厂商工程依据。实物颗粒后缀/PCB修订、训练及稳定运行仍未读回 |
| PS输入/电压 | 33.333333MHz；Bank0 3.3V、Bank1 1.8V | 与已有图纸及历史配置相符 |
| UART0 | MIO14..15、115200 | 与历史采集一致；用于后续启动日志 |
| SD0 | MIO40..45、CD=MIO10；WP禁用 | 与已有SD/CD图纸依据相符；历史采集XSA禁用SD0，不能整套照抄旧配置启动SD |
| ENET0 | MIO16..27，MDIO52..53，125MHz | 图纸路由相符；镜像DT为rgmii-id，但实际PHY识别/延时/驱动仍待板上核验，不能由HWH确认PHY芯片 |
| USB0 | MIO28..39，reset=MIO9，低有效 | 是厂商配置事实；非本批已验证外设 |
| PS主频 | CPU约766.7MHz，IO PLL 1000MHz | CPU需要按本板 `-1` 重新生成；不能直接照抄 |
| PL接口 | GP0 master启用，S_AXI_GP0启用，HP0=64位；FCLK0..3启用 | 属于厂商base用途。A须按当前实际CPU桥/DMA选择必要接口，不将全部示例外设导入SoundSight |

本机现有 `D:/vavido_project/i17_live_loop/project/par/i17_live_loop/i17_live_loop.xpr`：2025.2、`xc7z020clg400-1`、top=`i17_vio_board_top`。45个登记文件均存在，38个HDL中未发现PS7/DDR/FIXED_IO；无登记BD/XSA/HWH。其外部U18 50MHz经MMCM得到96/61.44MHz，是现有PL依据，**不能提供不存在的PS DDR启动设置**。此检查不代表A本机后续工程没有PS工作。

用户补充 `C-RTL-004/submission/` 中有相关one工程后，已追查本地历史与远端main。历史提交 `6443e50` 的submission包含包装RTL/测试/BD复现材料，并未包含one；远端main `85045c0f2dcd904a31efafdd6875a3e65c705a08` 也没有该目录。实际可读的 [one工程快照](https://github.com/TophBeifong1744/Competition_fpga/tree/85045c0f2dcd904a31efafdd6875a3e65c705a08/task-packages/PKG-A-ACQ/deliveries/dupont-diagnostic-20260911/payload/build-snapshot/one) 含 `one.xpr`、`system.bd`、`system_c_adapter.xsa`；以它作为新增准确配置来源，不冒称已证明它就是用户记忆中的submission工程。

这份one为2025.2 / `xc7z020clg400-2` / `system_wrapper`；PS7 rev8，CPU666.666687MHz（ARM PLL FDIV40、div2、6:2:1），IO PLL1800MHz（FDIV54）。DDR型号/32位/533.333374MHz/1GiB地址配置与历史基线一致；UART0 MIO14..15/115200；SD0/SD1、ENET0/1均禁用。仅FCLK0=100MHz，GP0 master启用、HP0=32位。XSA内HWH和ps7_init.tcl对此一致。

**复用方案：以one已有DDR、UART与约666.7MHz CPU配置为参考，以厂商SD0/网口引脚分配补启动外设；按已确认 `-1` 重算IO PLL和全部相关分频，建议采用厂商1000MHz IO PLL路线。** 不整包照搬任一旧工程。USB0/SD1及示例FCLK/GP/HP不因厂商启用就自动加入当前设计；当前控制和原始数据通路仍按A/B实际接口绑定。

## 首次启动前必须处理的具体时钟差异

[AMD DS187 v1.21](https://docs.amd.com/api/khub/documents/uaBd8Qxmf_K1~~tiVnOxrw/content) 第15页表17规定 `-1C/-1I/-1LI` 的6:2:1 CPU上限667MHz；表18的DDR3上限1066Mb/s；第16页表21的PS PLL上限1600MHz。

厂商 `ps7_init.c` 三个silicon revision数组均为 ARM PLL FDIV46、ARM divisor2、6:2:1。镜像 `BOOT.BIN` 中找到这三组匹配初始化表：

| 寄存器/语义 | mask / value | BOOT.BIN 内匹配偏移 |
|---|---|---|
| `F8000100` ARM_PLL_CTRL FDIV46 | `0007F000 / 0002E000` | `10F1C,117B8,12068` |
| `F8000120` ARM_CLK_CTRL source0/div2 | `1F003F30 / 1F000200` | `10F78,11814,120C4` |
| `F80001C4` 6:2:1 | `00000001 / 00000001` | `11140,119D8,12288` |

每组匹配包含 `EMIT_MASKWRITE` 编码 `0x33` 和 addr/mask/value 四个LE32字。独立按[AMD UG1283 Boot Header表](https://docs.amd.com/r/en-US/ug1283-bootgen-user-guide/Zynq-7000-SoC-Boot-Header)解码：FSBL偏移`0x1700`、长度`0x18008`，范围`[0x1700,0x19708)`；头校验重算一致。全部九处匹配均在FSBL区域；完整的三组384字节PLL初始化数组也逐字节匹配。镜像DT CPU OPP为766666和383333kHz，PS输入时钟33333333Hz。这些是**镜像FSBL区域确含约766.7MHz初始化配置的静态证据**；未做机器码控制流或板上执行验证，没有宣称实物已运行超频或整个FSBL同构建。

以已确认 `-1` 为目标，建议沿既有约666.7MHz CPU目标重新生成PS初始化、匹配FSBL/BOOT.BIN，并同步Linux DT的最高OPP、重新打包FIT；完整检查PS PLL/分频和外设时钟。历史四麦配置虽CPU约666.7MHz，但IO PLL为1800MHz，不能整套复制到 `-1`。**不手工十六进制补丁，不依赖启动后再降频，不改变PL 61.44MHz以绕开这个PS问题。** DDR533MHz本身不因这条CPU差异而超限。

## 给 A/E 和 B 的可执行接续

**A/E：沿原总工程接合。** 使用上述PS原件为板级依据，按实际 `-1` 重新生成配置/初始化；交匹配BOOT.BIN/DT或经验证的替代启动组合。接入当前CPU桥/PL源时保留准确时钟、复位、生产参数和物理引脚，生成同候选bit/HWH/适用XSA及必要物理报告；不是让C另建一套base工程。`prepare_bd.tcl` 当前仍为主动报错占位文件，不作为用户执行入口。

**B：平台版本现已可绑定到这份离线候选。** 镜像内 PYNQ DMA `start/stop/wait` 含无超时循环；接收完成后调用 `invalidate()` 并读回transferred；发送前flush。`PynqBuffer` 的cache同步由coherent/device决定；XRT后端源码调用 `xclSyncBO`。这给出源码依据，**不证明当前allocator、缓存一致性、总线写入完成、kernel pin或缓冲退休已验证**。不能把默认 `stop()` 返回当成全writer退休证明，也不能在失败时直接free/reuse。真实adapter继续按已接受合同绑定地址/IRQ/owner/epoch/超时与恢复，沿原任务实现。

当前原Issue的新状态已读：JOIN-002重放清RAW_STATUS残留获[B源级限定接受](https://github.com/TophBeifong1744/Competition_fpga/issues/18#issuecomment-6182845366)，不再写JOIN-001仍NEEDS_FIX；它不等于RTL/整桥/板测通过。[A接续](https://github.com/TophBeifong1744/Competition_fpga/issues/18#issuecomment-6182799968)仍要求实际工程、PS/BD、匹配产物。B PR66候选`12b2dcbc44da93dc5b5dcf227d81cca1fc90f556`已按OFFLINE_PS_SOFTWARE_ONLY范围合入，公共ABI和硬件adapter仍未激活。完整PS参数/差异见[vendor-one-ps-parameters.json](vendor-one-ps-parameters.json)，下一责任与接收判据见[接续交付](HANDOFF-20261015.md)。

## 完成与未完成

- 已完成：两ZIP完整性/身份、IMG提取、启动文件/FIT、系统与包版本、PS源/HWH/XSA一致性、DDR/MIO、PS主频差异、镜像相关驱动源码和当前任务接续核对。
- 未完成：适配后镜像构建与启动、实物DDR/PHY稳定性、当前SoundSight Overlay、真实DMA/cache/退休与STOP/reset恢复。没有以资料或退出码替代这些结果。
- 用户操作按更新的 [pynq-platform-next.md](pynq-platform-next.md)，不再要求用户核哈希或逐文件对照。
