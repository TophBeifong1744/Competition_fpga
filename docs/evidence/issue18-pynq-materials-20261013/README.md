# C 给 B 的 PYNQ 接入材料（任务2 / #18）

**2026-10-15 当前接续：** 两个厂商ZIP已收到，CRC结果复用并重新核对ZIP/IMG及参考原件SHA256。已确认离线镜像为PYNQ2.7.0、NumPy1.20.3、Python3.8、Linux5.4.0-xilinx-v2020.2；厂商PS与历史one均使用已确认DDR预设。厂商FSBL含约766.7MHz配置，须先适配当前 `xc7z020clg400-1`；旧one的1800MHz IO PLL也不能整套照抄。当前A桥JOIN-002已获B源级限定接受，PR66已按离线软件范围合入；均不代表板端通过。详见[厂商核验](ps-platform/vendor-platform-audit.md)、[明确接续与验收缺项](ps-platform/HANDOFF-20261015.md)及[现场操作单](ps-platform/pynq-platform-next.md)。以下注明日期的旧记录保留历史适用范围。

2026-10-13。本批完成已有接口、控制协议、工程记录及现场补述的集中整理；没有重跑旧测试、启动 EDA、加载板卡或安装镜像。PYNQ 接入状态仍为 **NOT_VERIFIED**。本材料回应 [B 的七组缺件请求](https://github.com/TophBeifong1744/Competition_fpga/issues/18#issuecomment-6139186501)，不替代 B 已交的接合方案，也不宣称 B 已读取或接单。

项目基线 `995fe0a802b572353c45a3669714c1292fe0fa52`；任务1控制候选为 [PR #63](https://github.com/TophBeifong1744/Competition_fpga/pull/63)，准确提交 `b529fed84bde1d5d5d6326e0d8870416c738657a`，七源内容 ID `f57493cf6d547d697f8430d3a3afa22a8a84c33d99e188936c46bcb85cd55f5a`。这两个组合分开引用；任务1尚未成为 A 已接入、实现或板测通过的总工程。

## 现场已知事实

| 项目 | 已有记录 / 本轮补述 | 限制 |
|---|---|---|
| 板卡 | 正点原子领航者，标签 `ATK-DF7010P_7020P`；底板 V3.9；核心板正面 `CF7010B/7020B`；芯片族 `XC7Z020` | 2026-09-07 实物照片记录；核心板完整订货型号、背面修订仍未知。用户本轮确认速度等级 `-1`，按 USER_REPORTED 保存 |
| 器件配置 | 用户确认 `-1`，与当前 live-loop XPR 的 `xc7z020clg400-1` 一致，Vivado 2025.2；旧采录工程为 `xc7z020clg400-2` | 采用本轮 `-1` 确认，保留旧 `-2` 历史配置差异；未新增芯片照片核验或修改任何工程，旧 `-2` 报告不能自动用于当前 `-1` 候选 |
| 当前运行方式 | 用户本轮确认：**仍用 Vivado/Vitis 经 JTAG 加载** | 当前已加载 bit/ELF 身份未知；2026-10-14 用户补述“板子没插sd卡”，按 USER_REPORTED 保存；历史装卡/安装及其他启动存储仍未知 |
| 镜像 / 运行时 | 当前 Linux/PYNQ 镜像名称、来源/hash、kernel、device-tree、Python/PYNQ/NumPy、驱动和 allocator 版本均 UNKNOWN | 没有实际 PYNQ 启动、Overlay 加载、MMIO 或 DMA 运行记录；不能选用任意 PYNQ-Z2 镜像 |
| 旧方向测试 | 用户补述：在电脑 Python 测 −90°、0°、90°，计算误差均在 5°以内；声音采集在 Vitis | USER_REPORTED；电脑计算证据，不是板端角度/PYNQ证据；该补述未绑定原日志、候选、次数、角度坐标/误差统计口径。保存结论，不推算平均值、置信区间，也不升级为持续跟随/PYNQ验收 |

板卡资料见 [板级审计](../../../hardware/m0-board-interface-audit.md)、[照片索引](../../../hardware/evidence/board-2026-09-07/README.md)和 [工程身份](../../../document/project-identity.md)。无需用户重复提供已有型号；现场未确认的字段保留未知。本人原答见 [user-report.json](user-report.json)，结构化状态见 [facts.json](facts.json)。


2026-10-14 现场补述：用户确认**当前板上没有插 SD 卡**。当前没有已确认可供查询的 SD 启动 Linux/PYNQ 环境，镜像及板端版本仍 UNKNOWN；不根据这一点断言历史从未安装或其他存储没有系统。本次仅记录事实，未刷卡、启动或查询板端。驱动缓存和写入完成判据待当前平台及 A/B 实际接口绑定，不复用旧裸机行为作为证明。


2026-10-14 操作归属更正：用户指认“电脑 Python 声源方向联调那次”，并确认过程中**没有按复位键、没有重新上电**（USER_REPORTED）。该次是 Vivado 下载 PL bit 后经 PL UART 与电脑 Python 联动；不涉及 Vitis/PS 应用。更早的 Vitis 独立采集记录另行保留，不能把其启动复位配置套到此测试。旧操作、现存日志及结束 STOP 尚无板端确认的边界见 [历史Python联调操作记录](historical-python-board-operation.json)。当前 PYNQ 镜像、DDR/MIO适用、复位/驱动缓存及写入完成判据仍需当前工程依据；不重复向用户索要旧操作。


2026-10-14 板级适用增量：已按原理图逐项核对DDR/MIO/启动与复位，资料中的1GiB/32位结构、PS时钟、Bank电压和UART/QSPI分配相符；南亚DDR与美光profile的等价依据及实际核心板/DDR后缀仍未证。SD/网口/USB在旧PS配置禁用；当前匹配镜像/BSP未识别。详见 [核心板、DDR与PS7核对](ps-platform/board-ddr-mio-audit.md)，包含支持路径、最小材料和具体缺项。本次仅资料核对，不要求重跑旧测试。

## 对 B 七组请求的集中回应

| 组 | 本批可交的准确材料 | 尚缺 / 下一责任 |
|---|---|---|
| M01 板与镜像 | 上表实物标识、本轮 `-1` 确认、旧 `-2` 历史配置差异及 JTAG 事实；照片与来源索引 | 按用户确认的 `-1` 与准确构建绑定；C 提供实际镜像事实，B 根据匹配板级支持确定部署，不把 Windows/Vitis 版本当板端系统版本 |
| M02 匹配工件 | 旧 C1 bit/XSA/init 的准确身份与旧 PCM/SHORT 原件入口；[XSA/HWH/PS 参数提取](ps-platform/README.md)；任务1七源、验证和包身份 | A 在原工程接合并给同构建 bit/HWH/manifest、适用 XSA/LTX/DTBO及必要全板资源/DRC/CDC/routed setup/hold；原综合异常按历史保留；A 后续前置组合的综合资源报告不等于本控制候选的同构建实现/时序验收。旧 C1 工件不能加载成新连续控制 Overlay |
| M03 PS/AXI/DMA | 旧 C1 合同、[原 HWH 的937项PS7参数与连线](ps-platform/ps-config.json)、旧BSP的11项一致性比对；C 本机 XPR 的只读声明见 [native-project-observation.json](native-project-observation.json) | C 保存的 XPR 顶层仍 `i17_vio_board_top`，声明中未发现 BD/PS7/DMA/GPIO CPU 通路。此范围不代表 A 机当前完整工程；A 给实际 PS7/GP/HP、MODULE 路径、地址/range、时钟复位和 DMA 参数。当前 MMIO 地址/中断映射 **UNBOUND** |
| M04 控制/结果 | [control-handoff.md](control-handoff.md)：任务1非 VIO CONFIG/RUN/STOP/RECOVER、上下文、映射、期限、事件、诊断握手与错误终态；对应准确 RTL/原说明 | 这是同域核心合同，尚无 CPU 桥/寄存器 ABI。A/C 集中选择并接合跨域命令、原子快照、结果缓存及 ACK/独占控制；B 沿已选择通路封装软件，不能自造地址或用轮询漏读单拍结果 |
| M05 allocator/cache/退休 | 旧 C1 两槽所有权及 cache 原则；旧实测原件可以引用；B 已列异常保留/退休要求 | 当前 Linux allocator、物理窗口、cache/barrier、actual_length、abort/quiescence及进程退出保护均 UNKNOWN。旧裸机固定 DDR 保留区不能直接用于 Linux |
| M06 原记录/抓取 | 旧 `ss-four-record-0.1` 32B/组、250组/8000B/包、完整包 STOP、原 ID/clip 格式和真实 PCM 原件；任务1五 bank 诊断逐字流 | **任务1新 top 未向外暴露原 PCM AXIS**，内部该口 ready=1，只用于排空；没有证据证明新 top 已向旧 S2MM 送 PCM。A/C 明确并接合当前抓取点与导出通路，B 绑定格式；五 bank 诊断不是旧 PCM 包，也没有现成 DMA TLAST ABI |
| M07 期限/水位 | 控制 RTL 的 61.44MHz 周期期限、状态/首错、饱和计数及任务1有限仿真结果 | PS poll/arm/transfer/stop/abort/export期限、生产TTL/HOLD/audio锚及持续最坏服务界 UNKNOWN；由系统责任给预算，B 按真实驱动记录。不照搬旧2秒、10秒等默认；设计上界不当实测 |

旧 C1 采集 ABI 的 RUN 是 GPIO 电平，旧 short 是 start pulse；任务1的新命令是 valid/ready 交易。这三者不能混接。STOP 的观察也分别属于旧录音完整包排空、新 DSP 义务排空和机械保持；任何一种都不代替另外两种。

## 已有记录直接复用

1. **B 原准备方案**：[PLAN](https://github.com/TophBeifong1744/Competition_fpga/releases/download/b-evidence-space-trial-20261002/i18-b-pynq-ps-prep-PLAN.md)、[INPUTS](https://github.com/TophBeifong1744/Competition_fpga/releases/download/b-evidence-space-trial-20261002/i18-b-pynq-ps-prep-INPUTS.json)。本批读取其四原件并核对 B 公布 SHA256，未改其规格。来源身份见 [source-index.json](source-index.json)。
2. **旧 C1**：[固定合同](https://github.com/TophBeifong1744/Competition_fpga/blob/995fe0a802b572353c45a3669714c1292fe0fa52/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/CONTRACT.md)。`ss-four-record-0.1` 每组8个 LE32：id_lo、id_hi、mic0..3、flags、reserved；PCM 是合法 signed24 符号扩展 int32，flags 低4仅逐路 clip，其余位/reserved为0。clip 不等于 drop；原 ID 不补零或重编号。旧 H1 CSV 是离线交换合同，不能据它推导 DMA ABI。
3. **真实 PCM**：[原 #18 交付](https://github.com/TophBeifong1744/Competition_fpga/issues/18#issuecomment-6012496696)、[原包](https://github.com/TophBeifong1744/Competition_fpga/releases/download/b-evidence-space-trial-20261002/i18-c-pcm-real-evidence-20261006.zip)，包 SHA256 `8d99a0d7a640743695d29cabf07a770794c2f212298d66a149f05aea9a476eaf`。raw 256000B/8000组/32包，SHA256 `cd42ed24b91a86dfd31a8ea7e98bb0941413ea8cfa053c7c2e8e00da8d47802a`；log SHA256 `0732caf05f2bea773bb50647545155315c5e4ac855ec002d84e82af7fb0727c8`。复用原件，不重采、不转换后替换原件；实际刺激/采集日历时间/实测几何仍按原交付限制。
4. **旧 SHORT**：既有本地 `codex_out/i18-short-real-delivery-20261006/package/README.md` 和 B 原方案的准确 SHORT 源码包/收件记录。旧日志两块各两段，程序自报 STOP/drained 不等于硬件 ACK 或实物停止；不是保存的完整连续音频。B 已有准确来源索引，不重复上传整套 BSP/工程。
5. **任务1**：[固定接入说明](https://github.com/TophBeifong1744/Competition_fpga/blob/b529fed84bde1d5d5d6326e0d8870416c738657a/docs/evidence/issue19-continuous-control-20261013/README.md)、[验证摘要](https://github.com/TophBeifong1744/Competition_fpga/blob/b529fed84bde1d5d5d6326e0d8870416c738657a/docs/evidence/issue19-continuous-control-20261013/validation-summary.md)。有限 XSim 自然 PDM/正式 FFT/IFFT 路径通过；未证明活动 FFT/IFFT 中 STOP、默认4096预热全链、9M耐久、声学真值、实物动作、全板实现或 PYNQ。
6. **#22**：B 已绑定 `beceee335d5c6d0ce96a2150f4a2ad107854e3a9` 的 receive-only 静态入口与有限接受范围；不运行主树旧 full-loopback 入口来补造 MM2S。mock 核心和拒绝硬件的 probe 不因本资料成为板端驱动。

旧 bit `b15991bc0f8595970361be553b542e334dbb7dca268c01864ecd80fcffbbffaf`、XSA `b84e93631132a3838cc9dadc1ce9037f2685d4d10de0b1655c76291663a8f60b`、init `a158fcc7d723b21003864159006e781ffaf5e8df24ec9b1d9279f9d14ff3ee5e` 仅绑定历史 C1；XSA 内 HWH 不自动成为当前可加载 Overlay 的匹配 HWH。

## 平台配置补充

已从现有历史采集工作区找到 XSA 及内嵌顶层 HWH，保存原件身份、937项PS7参数、MIO/DDR、GP/HP、DMA地址与连线、时钟复位及旧BSP比对。详见 [平台与PS配置材料](ps-platform/README.md)。当前 C 保存的 live-loop 目录仍未找到 XSA/HWH/BD；旧 `-2` 的 GPIO/DMA 地址不能当成新 `-1` 控制 ABI。实际镜像及板端运行时仍 UNKNOWN。

## 下一接续与完成范围

A 继续在 `F:/AMD/p/i17_live_loop/i17_live_loop.xpr` 给准确 PL 组合和实际 CPU 接合，不搭第三工程；C 现场入口仍为 `D:/vavido_project/i17_live_loop/project/par/i17_live_loop/i17_live_loop.xpr`。任务1新增 core 已供接合，但本资料不选择新的公共 AXI ABI、DMA 架构、镜像或 part。B 可以立即沿既有授权完成离线合同/格式/所有权/缺件拒绝及软件组织；真实 API/地址绑定依赖 M01～M05，持续抓取依赖 M06～M07。

当前最小剩余集中输入：**匹配板级镜像事实；按本轮 `-1` 确认绑定的 A 同构建工件/必要报告；当前 CPU 控制、结果缓存、原 PCM 导出及实际 DMA/cache/恢复合同**。这些缺件不要求重跑旧角度、旧矩阵或重新采集已有 raw。用户可直接补未知现场事实；新镜像选择和实际安装由对应后续任务处理。

“镜像”指可供开发板启动的系统安装映像，常见交付是写入 SD 卡的 `.img`；“板端系统”指运行在 Zynq ARM/PS 上的 Linux、内核和 device-tree；“驱动信息”指 PYNQ/Python 使用的 DMA、缓冲分配及外设访问软件版本与来源。它们属于板上软件环境，电脑上的 Vivado/Vitis 2025.2 和 PL 的 `.bit` 不能提供这些版本。用户目前确认的是 JTAG 加载；当前材料尚无实际镜像/板端运行时记录，保留未知即可，不要求为填写材料先安装或运行 PYNQ。参考 [PYNQ 官方入门](https://pynq.readthedocs.io/en/latest/getting_started.html)。

比赛要求 PYNQ on Zynq，以 2026-10-13 用户决定为准；旧指南中的备用后端描述只保留历史工程边界，不能自动把比赛交付切回 standalone。任务2材料整理已完成；#18 整体、B 实现、PYNQ 准入及任务3现场联调保持原状态。资料校验仅为来源/哈希/引用核对，见 [validation.json](validation.json)。
