# C-RTL-004：001核心Verilog包装与独立BD交付

状态：作者自检 PASS，独立 BD 默认32/3位检查及 Validate PASS。待独立验收及 B 正式复核，由 A 安排后续总工程集成。

## 交付信息

- 作者：hsc（Codex辅助）；版本1.0；2026-09-10。
- 唯一本地交付分支：codex/c-rtl-001-outsourcing-docs；不合并 main，不推送远端。
- 工作基线：0bcae278335e8029f6c7c3dc8e20a9bbadc8ff85。
- 准确交付提交：仓库根目录执行 `git log -1 --format=%H -- task-packages/PKG-A-ACQ/outsourcing/C-RTL-004/submission`。精确文件字节另见 file-manifest.json。
- 规范：rtl-bd-policy-1.0；接口：c-rtl-004-if-1.0。
- 工具：Vivado/XSim 2025.2，SW Build 6299465；器件 xc7z020clg400-2。
- 核心为 SystemVerilog；BD 入口为 Verilog `stream_error_stats_bd.v`，模块名 stream_error_stats_bd。
- COUNT_WIDTH 是 integer 参数，默认32，合法1～64；两个计数无符号、无缩放；其余端口均为标量。
- clk 上升沿工作，rst_n 同步低有效且最高优先；clear 清历史并计入本拍事件；sticky 保持；计数饱和不回绕。
- 外壳只有一次核心实例化和命名端口映射，无额外寄存器或包装延迟。

## 固定依赖与文件

核心从 Git 提交 `ac8a7bb60d94c069f5f1b61e9fc38658b0742962` 提取：
`task-packages/PKG-A-ACQ/outsourcing/C-RTL-001/submission/rtl/stream_error_stats.sv`。
SHA-256：`333dc4d193169982a6609c886a48968e87ef2631496d0c90137d24f228a94afe`。
提取使用 git show 的原始字节，未改原核心（含原始无 timescale 状态）。无 package/include 依赖。

| 文件 | 内容 |
|---|---|
| reference/stream_error_stats.sv | 指定提交的原核心 |
| rtl/stream_error_stats_bd.v | 薄包装，普通 wire 端口 |
| tb/tb_stream_error_stats_bd.sv | 定向测试、原核心/包装/独立整数参考三方核对 |
| scripts/run_tests.ps1 | 在新的包外目录编译和仿真，不覆盖本包证据 |
| scripts/rebuild_bd.tcl | 从零创建独立工程，导入源码，默认32及修改3位检查与 Validate |
| scripts/update_manifest.ps1 | 更新文件清单，不包含清单自身 |
| logs/simulation/ | 编译核心、包装、TB、展开、仿真及运行摘要 |
| logs/bd-final/ | 最终 BD 原始日志、两份端口表、两份工具导出的 BD Tcl |
| logs/attempt-bd01/、attempt-bd02/ | 两次脚本失败的原始工具日志 |
| logs/diagnostic/ | 参数刷新诊断脚本和原始日志 |
| logs/source-check.txt | 指定核心和工程内三个源码副本的哈希检查 |
| warnings.md | 每一条工具警告的文件、行号、原文与说明 |
| .gitattributes、.gitignore | 保持精确字节，仅本包所需日志放行 |
| file-manifest.json | 相对路径、字节数、SHA-256 |

## 仿真复现

Windows PowerShell 7，在本 submission 目录执行：

```powershell
& .\scripts\run_tests.ps1 -VivadoBin 'C:\AMDDesignTools\2025.2\Vivado\bin'
```

可额外指定 `-RunDirectory '<新的包外目录>'`；目录已存在时拒绝运行。默认在系统临时目录建立唯一目录。
脚本打印实际输出位置，包含 compile-core.log、compile-wrapper.log、compile-tb.log、elaborate.log、simulate.log、summary.txt 和包外缓存。
依赖与编译顺序：核心 xvlog --sv → 包装 xvlog（不带 --sv）→ TB xvlog --sv → xelab → xsim。
xelab 使用 `-timescale 1ns/1ps`，不修改无 timescale 的核心。
脚本检查每一步退出码和仿真日志成功/失败标记。仅当前自动化进程缺少 PROCESSOR_ARCHITECTURE 且系统为X64时临时补AMD64，结束恢复，不重置全局环境。

TB 先测3位，再依次1、默认32、64；默认32包装不覆盖参数。每步下降沿驱动，1 ns后确认未到上升沿输出保持，再在上升沿1 ns后验证当前拍结果。
原核心和包装接受同样输入；二者分别与独立64位无符号整数参考比较，并比较彼此全部输出。比较使用 !==，失败打印用例、位宽、输入和三方结果，再 $fatal；100000 ns超时。
小位宽饱和由真实事件驱动达到，不使用 force。测试结束时间1156 ns；TB时钟周期不是板上频率合同。

```text
WIDTH PASS W=3 checks=87 time=436000
WIDTH PASS W=1 checks=63 time=756000
WIDTH PASS W=32 checks=39 time=956000
WIDTH PASS W=64 checks=39 time=1156000
ALL TESTS PASS: W=3,1,default32,64 core oracle + wrapper oracle + equivalence
```

共228次核对调用，包含沿前/沿后及初始复位检查；不是228个独立用例。%t按ps显示。
实际运行：2026-09-10 22:10:49至22:10:59（UTC+08:00），详见 summary.txt。
下一步：核对日志覆盖，交独立验收与B复核。

## BD及本机工程

已保存的完整工程：`D:\vavido_project\c004_bd_verified\c004_bd_probe.xpr`。
该目录含导入的 .sv 核心、.v 外壳、.sv TB、本地 bd_probe.bd；三个源码副本哈希与交付一致。
最终保存 BD 参数为3，之前默认32状态的原始端口表和导出Tcl也保留。打开工程后双击 bd_probe.bd 查看。
仿真顶层 tb_stream_error_stats_bd、Run All 及 xelab 默认 timescale 已配置。未执行 GUI 点击仿真；实际功能证据为命令行 XSim。
首次未完成目录 c004_bd_probe 和诊断目录 c004_bd_probe_v1 保留现场；请使用 c004_bd_verified。

从零复现，在 submission 目录的正常 Vivado PowerShell 环境执行（安装路径按实际调整）：

```powershell
$toolBin = 'C:\AMDDesignTools\2025.2\Vivado\bin'
$bdScript = (Resolve-Path '.\scripts\rebuild_bd.tcl').Path
$bdRun = Join-Path ([IO.Path]::GetTempPath()) ('c004-bd-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $bdRun | Out-Null
Push-Location $bdRun
try {
    & (Join-Path $toolBin 'vivado.bat') -mode batch -source $bdScript -log bd.log -nojournal -tclargs (Join-Path $bdRun 'project')
    if ($LASTEXITCODE -ne 0) { throw 'BD verification failed; keep bd.log' }
} finally { Pop-Location }
```

若自动化进程缺少架构变量，按 run_tests.ps1 的相同进程级设置处理。不要设置全局变量。
预期新目录内产生 bd.log、project/c004_bd_probe.xpr、BD以及evidence端口表和导出Tcl。
脚本只使用其相对位置寻找依赖，目标位置由参数给出，不绑定个人D盘。

实际流程：Design Sources导入核心和包装，Simulation Sources导入TB；检查语言类型且没有重复模块；创建BD，create_bd_cell -type module -reference stream_error_stats_bd（对应Add Module），引出全部9个端口。
先核对未经参数覆盖的32位输出和所有方向，Validate成功；再set_property CONFIG.COUNT_WIDTH 3，工具自动刷新模块引脚，同时同步两个外部计数端口宽度，重新核对实际引脚及端口并Validate成功。
未使用GUI操作参数，因此不声称已验证GUI参数编辑对话框；参数识别、修改和端口刷新由实际Vivado Tcl API验证。

```text
PORTS_PASS COUNT_WIDTH=32
VALIDATE_PASS COUNT_WIDTH=32
PORTS_PASS COUNT_WIDTH=3
VALIDATE_PASS COUNT_WIDTH=3
ALL BD TESTS PASS
```

不添加PS、AXI、DMA、约束或system_wrapper，不声明未经确认的FREQ_HZ。两份write_bd_tcl导出需要先加载RTL依赖；完整重建使用scripts/rebuild_bd.tcl。
下一步：打开工程查看模块、端口和参数，再由B复核。不能将独立BD通过说成总工程已接通。

## 测试覆盖与状态

| 项目 | 状态 | 证据 |
|---|---|---|
| 原核心哈希及基线行为 | PASS | source-check；TB原核心也单独与整数参考比较 |
| 同步复位、沿间保持、复位覆盖clear及双事件 | PASS | 每宽度沿前/沿后核对，非零历史时拉低复位 |
| 空闲、单路/双路事件、连续事件、sticky保持 | PASS | simulation/simulate.log对应CASE PASS |
| clear无事件/单路/双路、连续clear+事件保持1 | PASS | 四宽度均覆盖 |
| 1/3位独立计数饱和、不回绕及清除后恢复 | PASS | 真实输入事件逐拍达到饱和，无force |
| 1/3/默认32/64包装等价、当前拍无额外延迟 | PASS | 四个WIDTH PASS及独立参考 |
| 独立BD添加、默认32位和修改3位接口、Validate | PASS（有警告） | bd-final/bd.log及ports-32.txt、ports-3.txt |
| 综合 | NOT_RUN | 可选，未执行 |
| one工程接入、时序、布局布线、板测 | NOT_RUN | 本批不要求 |

## 警告及已解决问题

最终BD运行有4条警告（3类）：IP_Flow 19-5661无关联数据总线；IP_Flow 19-11770未声明FREQ_HZ；BD 41-2925两次提醒导出脚本依赖RTL。全部原文和逐项解释见warnings.md。
诊断重开工程还出现其他开发板器件不可用和空Board Part警告，亦逐项登记；没有为消除它们修改全局安装环境。

1. 第一次BD脚本设置以减号开头的xelab选项时被Tcl解析为选项，提前失败；改用显式属性参数及前导空格后解决。原日志保留。
2. 第二次默认32位已通过；额外update_module_reference返回空错误。诊断证实CONFIG设置后实际模块计数引脚LEFT已由31变2，自动刷新已完成，3位Validate也通过。最终移除该冗余调用，在新工程完整重跑两种参数通过。诊断错误没有隐藏或写成通过。
3. GUI视觉检查、综合和板测未执行；不穷举64位计数，不添加额外随机框架。无未解决的必需功能或BD失败。
4. 未改001核心、002/003、instructions快照或共享one工程。功能和BD通过不等于正式时钟合同、整板时序或总工程接入通过。

复跑不会覆盖本包原始日志。需要更新交付证据时先保留旧版，再核对源码与日志版本并运行 `& .\scripts\update_manifest.ps1`。
