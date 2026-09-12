# 当前四路安全构建入口：本轮结果

日期：2026-09-12。状态：**实施自检完成，待工作执行提交给 B 独立复核**。
本项为等待转接板期间的工程化改进，不新增 9 月 16 日诊断验收门槛。

## 完成范围

- 新增参数化 check/build 入口、隔离构建 Tcl、34 项安全/回归测试和本批证据。
- 未运行单麦→四麦迁移脚本，未修改实际 one、BSP、PS 源码、RTL、BD、XDC、CIC、H1 或算法。
- 不下载上板、不重做历史录音/DDR验收、不提交、推送或合并。
- 使用 xilinx-suite 指南核对工具链与阶段边界；具体命令以实际 AMD 2025.2 帮助和本机工程验证为准。
- 原任务包 189 份冻结文件按原 DELIVERY-MANIFEST-20260912.json 校验，大小与 SHA-256 全部一致。

工作副本只在原待审分支的 pub 下新增 current_build；不向共享 main 混入待审改动。
工作执行后续只提交这项增量，仍须按准确 SHA 复核；本任务未进行阶段发布或收尾合入。

## 可复现入口

阅读 [README.md](README.md) 的参数和 check → tests → build 命令。
实际第四次调用见 [run04-command.json](evidence/run04-command.json)。
工程、Vivado、GCC、BSP、BSP 对应 XSA、PS 源目录和新输出目录均由参数提供。
每次输出必须使用一个尚不存在的目录；不允许复用本次成功或失败目录。

本次实际依赖：

| 项目 | 路径或版本 |
| --- | --- |
| 工程 | F:/College/verilog_digital_system/AMD/Competiton/one/one.xpr |
| Vivado | 2025.2，Build 6299465，xc7z020clg400-2 |
| 工具启动 | F:/AMD/2025.2/Vivado/bin/vivado.bat |
| GCC | 2025.2 安装内 arm-none-eabi-gcc；Vitis/gnu 安装器链接解析到共享 gnu 目录 |
| BSP | F:/College/verilog_digital_system/Vitis/c_adapter_platform/export/c_adapter_platform/sw/standalone_ps7_cortexa9_0 |
| BSP 对应 XSA | F:/College/verilog_digital_system/Vitis/c_adapter_platform/export/c_adapter_platform/hw/system_c_adapter.xsa |
| PS 源 | F:/College/verilog_digital_system/Vitis/four_mic_capture/src |
| 成功隔离目录 | F:/College/verilog_digital_system/four_diagnostic_work/current_rebuild_20260912_04 |

上述个人路径只是本次参数记录，不是新程序中的默认依赖。
[preflight.json](evidence/run04/preflight.json) 保存实际输入位置与逐文件哈希；
[tool-version.txt](evidence/run04/reports/tool-version.txt) 和 [GCC 输出](evidence/run04/logs/gcc-version.log) 保存实际版本。

## 验证结果

| 检查 | 本次结果 |
| --- | --- |
| check 只读模式 | CHECK_PASS_NOT_BUILD；不创建目录、不启动工具 |
| 安全/回归测试 | 34/34 PASS，覆盖空/非空输出、路径重叠、缺依赖、并发占用、输入改变、旧单麦拒绝及等价规则反例 |
| 实际 one 路径保护 | 指向 one 内部的新目录被拒绝，目标目录未创建 |
| 成功输出防覆盖 | 再次 build 指向 run04 返回原生退出码 2；594 个输出文件前后哈希一致 |
| Validate / 生成 | 当前副本强制 Validate Design、重新生成完整产品；不依赖旧缓存 |
| 综合 | 完成；未解析黑盒为 0 |
| 实现 / bit / XSA | 完成，完整日志保留 |
| PS 编译 | 完成，生成 ELF 和 map；复用匹配 BSP，未重建平台 |
| 输入保护 | 实际 one、所用 BSP/PS 输入及受保护旧产物前后哈希一致 |
| 产物核对 | 本次清单内 28 个日志/报告/产物逐项哈希核对一致 |
| 实板结果 | NOT_RUN，不产生新的采集或板测通过结论 |

证据：
[安全测试](evidence/safety-tests-final.log)、
[实际防覆盖结果](evidence/postbuild-refusal.json)、
[完整结果](evidence/run04/result.json)、
[产物清单](evidence/run04/artifacts-sha256.json)。

run04 用时：14:14:03～14:24:07（本地 +08:00）。所有阶段结果来自本次实际运行。

### 时序、资源和内存

- WNS = 4.640 ns；TNS = 0；WHS = 0.056 ns；THS = 0；WPWS = 3.000 ns；TPWS = 0。
- 内部无未约束最大延迟端点；上述仅表示现有约束下内部 setup/hold/pulse-width 检查通过。
- 仍有 4 个输入端口缺 input delay、4 个输出端口缺 output delay；外部 IO 延迟和物理四 CLOCK 偏斜未验证，
  不声称“全部时序闭合”或已完成实物同步测量。沿用原暂缓边界，不在此任务更改约束。
- 布线后资源：Total LUTs 8347（logic 4439、LUTRAM 3850、SRL 58），FF 4390，
  RAMB36 1、RAMB18 1、DSP 0。
- DRC：6 个 Warning、2 个 Advisory；PDCN-1569 ×5、RTSTAT-10 ×1、REQP-165/181 各1。
  Methodology：LUTAR-1 ×5，位于既有 AXI 互连/FIFO 生成逻辑。保留告警，不在本任务改变 RTL/IP 来消音。
- 程序 end = 0x00112630 < RX 起点 0x01000000。
  32000 组 ×32 字节 = 1024000 字节；保护区末端 0x010FA040 < 0x01100000。
  这只是链接边界检查，不是重新进行 DDR/DMA 实板测试。

完整报告：[时序](evidence/run04/reports/timing-summary.rpt)、
[资源](evidence/run04/reports/utilization.rpt)、
[DRC](evidence/run04/reports/drc.rpt)、
[方法学](evidence/run04/reports/methodology.rpt)。

### 必须如实说明的生成差异

- 强制验证把原 XCI 已有的 299 项值展开写入**隔离副本** BD；逐项匹配原 XCI，
  原 BD 已有参数、连线、端口、地址及其余内容必须相同。名单在 result.json。
- 自动 wrapper 只允许 Date/Host 注释和行尾变化，正文相同。
- 新旧 XSA 不是原始字节相同。HWH 除时间戳外，仅 8 个未启用 CTI GUI 哨兵值
  DISABLED / &lt;Select&gt; 不同。CROSS_TRIGGER=0、P2F_CTI_INTR=0、无触发端口/接口，
  且其余 HWH 全部保持一致；ps7_init.c 逐字节相同。
- 等价规则及 AMD 定义依据：[核对记录](evidence/hwh-compatibility-audit.md)。
  [BSP 配对结果](evidence/run04/reports/bsp-contract.json) 同时保存严格签名和兼容签名。
  有效参数、地址、接口或初始化改变仍失败，不能凭“位流生成成功”复用不匹配 BSP。

## 保留的失败与修正

| 尝试 | 实际结果 | 入口修正，不修改设计 |
| --- | --- | --- |
| 01 | 版本探测退出 1，未综合 | Windows vivado.bat -version 显示版本仍可返回 1；改在 Vivado Tcl 内先核对版本 |
| 02 | 综合结束，实现因 SmartConnect bd_8422 黑盒失败 | 不复制旧缓存；强制传播参数并生成完整子设计，新增综合后黑盒检查 |
| 03 | 硬件完成，严格 HWH 比较拒绝 PS 链接 | 查明上述 8 个禁用 CTI 哨兵差异，增加受限等价规则及反例测试 |
| 04 | 完整隔离构建自检通过 | 保留全部报告、实际入口与产物哈希；未上板 |

四次完整目录均在 F:/College/verilog_digital_system/four_diagnostic_work/，
后缀为 current_rebuild_20260912_01～04。前三次仍为 BUILD_FAILED，不回写为成功。
本包 evidence/run01～04 保留对应入口快照、日志、报告、输入及产物哈希。
未删除失败记录，不用失败目录覆盖重跑。

## 产物 SHA-256

成功目录的 artifacts/ 下实际生成以下文件；未整体复制工具/BSP/缓存进仓库。
原二进制留在明确的成功目录中，以下哈希与实物文件再次核对一致。

| 产物 | 字节数 | SHA-256 |
| --- | ---: | --- |
| hw/system_c_adapter.bit | 4045690 | d295fae45db5af0bd39ce5a6aa0d8d20a8383e57e98be164a9450174ad062e29 |
| hw/system_c_adapter.xsa | 609578 | fc9c1a24c0297f7230e629a440ef5c4c0b5682a5866607ba72c4d6500d76cf18 |
| ps/four_mic_capture.elf | 283480 | 1f7418fd844c19560499971f11b08aadabf551079ba567a9d80825c03f76ca24 |
| ps/four_mic_capture.map | 150208 | 7050e6a80bab45b696b88af8401d9c87a9036e2cda9ec1733f063ab9ef93413f |

时间、调试路径和编译日期可以使哈希不同于历史产物；这里不承诺位对位重现旧 bit/ELF。

## 未完成项与移交

1. 待工作执行提交本批新增文件、由 B 按准确 SHA 独立复核；作者自检不是审批。
2. 本次完成“现成 BSP 依赖下”的隔离构建，未从 BSP 源码重建 Vitis 平台，也未在第二台电脑重复运行。
   更换平台输入须重新核对配对，不拿本结果为任意 BSP 背书。
3. 外部 IO 细化时序、物理时钟偏斜、实板加载及新录音均未执行；不追溯改变历史诊断门槛。
4. 原始日志已在 current_build 的局部忽略例外中显式保留；新证据按原字节保存。
   原工程和四次本地构建目录均未删除；复制件/缓存仅在复核后由负责发布者确认无独有材料再处置。
5. 本批未提交、推送或合入；后续获准发布后再按团队规则核对实际共享 main、origin/main、远端和有用本地材料。
