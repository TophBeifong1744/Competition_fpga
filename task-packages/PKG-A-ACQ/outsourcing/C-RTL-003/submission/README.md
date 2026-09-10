# C-RTL-003：四通道 PCM 符号扩展与打包交付

状态：作者功能自检 PASS；待独立验收及 B 正式复核，未获总工程接入批准。

## 基本信息

- 作者：hsc（Codex 辅助实现）；版本 v1.0；日期 2026-09-10。
- 本地交付分支：`codex/c-rtl-001-outsourcing-docs`。不合并 main，不推送远端。
- 工作基线：`9a02a084dcf8d823314d06347b02ae1ce0fa5570`。
- 准确交付提交：在仓库根目录执行 `git log -1 --format=%H -- task-packages/PKG-A-ACQ/outsourcing/C-RTL-003/submission`；各文件精确字节由 file-manifest.json 标识。
- 实际工具：Vivado/XSim 2025.2，SW Build 6299465。
- 独立工程器件：xc7z020clg400-2。
- 依据：[操作单](../instructions/README.md)。H1 候选 ss-data-draft-0.3 仅作通道及数值语义依据。

## 功能与接口

设计顶层 `pcm4_signext_pack`，参数 SAMPLE_WIDTH 默认 24，支持 2～32。
四路 signed 输入分别符号扩展到 32 位：mic0 占 [31:0]，mic1 占 [63:32]，mic2 占 [95:64]，mic3 占 [127:96]。
纯组合连续赋值，无时钟、复位、状态、锁存器或 RTL 延时；32 位输入原样保留。
不缩放、舍入、饱和、截断或左对齐。每个槽位各自解释为 signed32，整个向量不是一个有符号样本。
128 位仅为内部测试/转换向量，不是已批准的 DMA 字宽或内存字节序合同。

## 文件清单

| 文件 | 用途 |
|---|---|
| rtl/pcm4_signext_pack.v | 可综合 Verilog 组合模块 |
| tb/tb_pcm4_signext_pack.v | 五位宽并行自检，顶层 tb_pcm4_signext_pack |
| run_xsim.ps1 | 编译、展开、仿真及 PASS/失败判定 |
| create_project.tcl | 创建独立工程并导入本地源码副本 |
| update_manifest.ps1 | 生成其他所有文件的相对路径、字节数和 SHA-256 |
| logs/xvlog.log、xelab.log、xsim.log | 最终成功运行的原始日志 |
| logs/run-summary.txt | 实际起止时间、工具位置和运行目录 |
| logs/create-project.log | Vivado 工程创建原始日志 |
| logs/project-copy-check.txt | 工程内副本与交付源码的 SHA-256 一致性 |
| logs/attempt-*/ | 两次早期失败记录，保留原始证据 |
| .gitignore、.gitattributes | 仅本包日志放行及精确字节保存 |
| file-manifest.json | 文件清单，不包含自身 |

## 完整复现步骤

Windows PowerShell 7，已安装 Vivado 2025.2。在本 submission 目录执行：

```powershell
& .\run_xsim.ps1 -VivadoBin 'C:\AMDDesignTools\2025.2\Vivado\bin'
```

工具安装路径通过参数传入；源码相对脚本定位。脚本在系统临时目录创建唯一构建目录，缓存不进入交付包。
旧编译/展开/仿真日志及运行摘要先复制到 logs/attempt-*，再生成新的最终日志。
仅在当前进程缺少 PROCESSOR_ARCHITECTURE 且系统为 X64 时补为 AMD64，结束恢复，不修改全局环境。

实际工具调用顺序（在包外的空构建目录、正常 Vivado 环境中执行；将 `<submission>` 换成实际绝对路径）：

```text
xvlog "<submission>/rtl/pcm4_signext_pack.v" "<submission>/tb/tb_pcm4_signext_pack.v" -log "<submission>/logs/xvlog.log"
xelab work.tb_pcm4_signext_pack -s pcm4_test -log "<submission>/logs/xelab.log"
xsim pcm4_test -runall -log "<submission>/logs/xsim.log"
```

xvlog 不使用 --sv。每步检查退出码，仿真日志必须包含 ALL TESTS PASS 且不能出现失败标记。
预期输出：三份工具日志及 run-summary.txt。下一步核对覆盖后，交独立验收及 B 复核。
重新运行导致日志变化后，执行 `& .\update_manifest.ps1` 更新清单，再检查提交差异。

## 实际测试结果

| 项目 | 状态 | 证据/覆盖 |
|---|---|---|
| Verilog 编译、展开 | PASS | logs/xvlog.log、logs/xelab.log |
| 2、3、16、默认24、32位 | PASS | 五个 WIDTH PASS；24位 DUT 不覆盖默认参数 |
| README 两个24位例子 | PASS | 同时检查独立整数参考值和给定128位常量 |
| 六种数值边界 | PASS | 每个宽度每路分别测0、1、-1、最大正数、最小负数、最小负数+1 |
| 四路顺序及独立性 | PASS | 不同基准码值；每次单路边界/逐位变化时另外三槽保持 |
| 正负符号组合 | PASS | 每个宽度全部16种 |
| walking-one / walking-zero | PASS | 每路每个位；五宽度分别16、24、128、192、256个刺激，包含32位最高位 |
| 2位四通道穷举 | PASS | 4^4=256组 |
| 连续组合变化 | PASS | 无时钟，多次输入更新后延迟1 ns比较完整输出 |
| 固定种子随机 | PASS | 16、24、32位各256组，xorshift32，无浮点 |
| 工程及导入源码 | PASS | create-project.log、project-copy-check.txt |
| 综合（可选） | NOT_RUN | 本批未执行 |
| 时序、布局布线、板测、DMA和总工程接入 | NOT_RUN | 本批不要求 |

参考模型使用 signed64 保存数学整数；无符号码值最高位为1时减去 2^W，再取32位表示。
参考计算不照抄 DUT 符号拼接。完整128位用 !== 比较；失败打印 W、四路输入、期望/实际并 $fatal。
顶层设100000 ns超时保护；全部五宽度完成后才输出最终成功标志。
随机种子：16位 13579bcf，24位 13579bc7，32位 13579bff。

```text
WIDTH PASS W=3 comparisons=73 time=73000
WIDTH PASS W=2 comparisons=321 time=321000
WIDTH PASS W=16 comparisons=433 time=433000
WIDTH PASS W=24 comparisons=499 time=499000
WIDTH PASS W=32 comparisons=561 time=561000
ALL TESTS PASS time=561000
```

日志 %t 以 ps 显示，最终结束时间为561 ns。共1887次完整向量比较，比较次数不等于独立用例数。
实际运行：2026-09-10 11:21:59.8856633 至 11:22:10.1149365（UTC+08:00），详见运行摘要。

## 本机 Vivado 工程

工程：`D:\vavido_project\pcm4_signext_pack\pcm4_signext_pack.xpr`。
设计源：`pcm4_signext_pack.srcs/sources_1/imports/rtl/pcm4_signext_pack.v`。
仿真源：`pcm4_signext_pack.srcs/sim_1/imports/tb/tb_pcm4_signext_pack.v`。
打开工程，Run Simulation → Run Behavioral Simulation，运行到结束即可检查相同测试。
工程创建和源码注册已验证；GUI 手动运行未执行，功能通过证据来自上述命令行 XSim。

如需在其他位置重建，在包外临时目录中执行（替换安装、脚本和新工程路径）：

```text
vivado -mode batch -source "<submission>/create_project.tcl" -log create-project.log -nojournal -tclargs "<new-project-directory>"
```

预期生成 pcm4_signext_pack.xpr 及工程内 RTL/TB 副本。脚本拒绝覆盖已有同名 XPR。
下一步打开工程运行 Behavioral Simulation。整个 GUI 工程及缓存留在交付包外。

## 已解决问题与验收边界

1. 首次启动因自动化进程缺少架构环境变量，xvlog 启动器返回1，未生成工具日志；保留运行摘要。采用此前002成功使用的进程级架构设置后解决。
2. 第二次编译成功，但展开报告 RTL 缺少 timescale；在 RTL 补充 1ns/1ps 声明后重跑全部测试通过。原编译/展开失败日志保留在 attempt 目录。该声明不引入硬件延时。
3. 无未解决的必测失败。未逐一测试其余2～32位参数，也未做错误注入框架，均非最低交付要求。
4. 不修改001/002、H1文档、根.gitignore或总工程。无采集、滤波、AXI、DMA、CDC、FIFO及采样编号功能。
5. 数字码型自检不是声学模拟或实录，也不表示H1硬件验收、物理通道正确或采样同步已完成。
6. 作者自检不替代独立验收或B批准；后续由A决定是否接入。
