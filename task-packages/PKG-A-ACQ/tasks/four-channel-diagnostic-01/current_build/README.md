# 当前四路工程：安全、参数化的隔离构建入口

本次只整理构建流程，不重做“单麦→四麦”迁移，不增加 9 月 16 日诊断验收门槛。
历史 adapt_c_one.tcl、integrate_one.tcl、build_ps.ps1 和 189 份冻结原件保持不变。
新增入口适用于已经适配完成的 one；不连接板卡、不下载、不提交或自行合入。

2026-09-12 PS 合同阻断修复：见 [修复说明与验证](repair_ps_contract/README.md)。
旧 RESULTS.md、evidence/run01～04 和 ENVELOPE-SHA256.json 保留为 050d06 的历史自检证据，
不表示已经通过 B 独立复核。当前增量哈希以 repair_ps_contract/REPAIR-MANIFEST.json 为准。

## 入口与边界

- build_current.py：Python 3.11+，仅标准库；check / ps-check / build 三种明确模式。
- ps_contract.py：从同一编译单元的目标文件及最终 ELF 提取真实 PS 合同；未知源码形态拒绝。
- build_hw.tcl：仅供 Python 入口在新建快照内调用，不作为对真实 one 的操作入口。
- test_build_current.py：微型临时夹具测试，禁止启动 Vivado/GCC，不依赖真实板卡。
- 本目录内 evidence/、RESULTS.md：本次真实命令、检查结果、构建记录和产物索引；以实际存在的结果为准。

不覆盖原工程，也不把当前源码重建成另一个设计：复制当前 XPR、已登记输入及 .srcs，
保留其 BD、RTL、XDC、IP 参数、约束启用状态和综合实现策略。
仅在副本 XPR 重定位工程路径，关闭旧增量 DCP 复用，从综合开始完整构建。
生成缓存、运行文件、bit/XSA/ELF/map 均位于新输出目录。

## 参数

以下参数全部显式提供，不从个人路径猜测输入：

| 参数 | 含义 |
| --- | --- |
| --project | 已适配四路的现有 .xpr；不是旧单麦工程或迁移脚本 |
| --vivado | Vivado 2025.2 启动程序，例如 vivado.bat |
| --gcc | 同套 2025.2 安装中的 arm-none-eabi-gcc；同目录须有 size、nm |
| --bsp | 现有 Cortex-A9 standalone BSP 导出目录，含 include/lib/Xilinx.spec/hw_artifacts |
| --bsp-xsa | 产生该 BSP 的平台 XSA，不可随意配旧单麦/旧 DMA 平台 |
| --ps-source | 当前应用源目录，含 main_four_capture.c 和 lscript.ld |
| --output | 绝对路径；父目录已存在，目标目录必须不存在，连空目录也拒绝 |
| --jobs | Vivado 并行作业数，默认 4，允许 1～16 |

固定当前工程合同：xc7z020clg400-2、Vivado 2025.2、four_mic_top_0、
四个 CLOCK 输出、四路 DATA、32000 组、250 组/包、4096 组预热、FIFO_LOG2=10。
本入口不会帮旧设计迁移或修改合同；不满足时先报错。

BSP 使用现成的驱动库，不创建/重建 Vitis 平台。记录所用 BSP 文件哈希；
构建前验证其 ps7_init.c 与所提供 XSA 对应，
先编译检查 PS 与该参考 XSA 的合同；完整构建结束后要求新 XSA 的 HWH 按下述受限等价规则匹配，
且 PS 初始化逐字节一致，才允许把已校验 ELF 随新硬件一起标为构建完成。
HWH 忽略 TIMESTAMP；针对 PS7 5.5，仅当 PCW_USE_CROSS_TRIGGER=0、PCW_P2F_CTI_INTR=0，
且未出现 FTMT/TRIGGER 硬件端口或接口时，8 个 PCW_FTM_CTI_IN/OUT0～3 的
DISABLED 与 &lt;Select&gt; 两种未启用 GUI 哨兵值视为等价。
依据本机 AMD processing_system7_v5_5/component.xml 的参数/端口使能表达式；
这些功能启用、出现接口、值变为其他内容或任何其他字段改变均不得归一化。
原始 HWH 签名与受限兼容签名同时记录在 reports/bsp-contract.json，不能写成原始文件完全相同。
这不是独立证明任意第三方预编译 BSP 库的来源；BSP 必须是用户提供的可信匹配导出物。

## 先 check，再 build

在当前四路任务目录执行。下面是本机输入示例；换电脑只替换参数，不改脚本。
不要执行旧适配脚本，不要先创建 --output 指向的目录。

~~~powershell
$BuildPython = 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$BuildArgs = @(
  '--project', 'F:/College/verilog_digital_system/AMD/Competiton/one/one.xpr',
  '--vivado', 'F:/AMD/2025.2/Vivado/bin/vivado.bat',
  '--gcc', 'F:/AMD/2025.2/Vitis/gnu/aarch32/nt/gcc-arm-none-eabi/bin/arm-none-eabi-gcc.exe',
  '--bsp', 'F:/College/verilog_digital_system/Vitis/c_adapter_platform/export/c_adapter_platform/sw/standalone_ps7_cortexa9_0',
  '--bsp-xsa', 'F:/College/verilog_digital_system/Vitis/c_adapter_platform/export/c_adapter_platform/hw/system_c_adapter.xsa',
  '--ps-source', 'F:/College/verilog_digital_system/Vitis/four_mic_capture/src',
  '--output', 'F:/College/verilog_digital_system/four_diagnostic_work/current_rebuild_next',
  '--jobs', '4'
)
& $BuildPython -B current_build/build_current.py check @BuildArgs
if ($LASTEXITCODE -ne 0) { throw '检查未通过，先按错误说明修正参数或依赖' }
~~~

check 只读文件并向控制台输出 JSON，不创建输出目录，不调用工具、不检查许可证、不构建。
CHECK_PASS_NOT_BUILD 只表示检查通过，不能写成“工程复现成功”。
此时 ps_contract_status=NOT_VERIFIED_IN_READ_ONLY_CHECK，不代表实际 PS 缓冲区安全。
检查通过后，同样参数执行：

~~~powershell
& $BuildPython -B -m unittest discover -s current_build -p 'test_*.py' -v
if ($LASTEXITCODE -ne 0) { throw '安全测试未通过，不执行构建' }
& $BuildPython -B current_build/build_current.py build @BuildArgs
if ($LASTEXITCODE -ne 0) { throw '构建未通过，保留整个输出目录并查看 result.json 与 logs' }
~~~

仅验证 PS 源码/编译/链接合同，可把 build 换成 ps-check。
它仍使用全新输出目录，返回 PS_CONTRACT_PASS_NOT_HW_BUILD；不会启动 Vivado。
随后若做完整 build，必须另换新目录，不能复用 ps-check 输出。
完整 build 也强制先执行同一 PS 校验，没有跳过选项。

## PS 合同如何绑定

1. 仅识别现有采集函数正文；允许七个宏行的受限算术表达式，拒绝新增条件分支、宏重定义或未知正文。
   这不是通用 C 解析器，也不以版本字符串或未绑定 JSON 推定地址。
2. 独立构建包装单元包含原始 main_four_capture.c，再附加一份只读合同常量；
   不改源文件或采集逻辑。GCC 对同一单元预处理一次，生成的 .i 是实际编译 .o 的输入，
   随后只链接这个 .o，不另行编译一份主程序。
3. 从实际 ARM ELF32 目标文件读取 BASE/LIMIT/GROUPS/WORDS_PER_GROUP/BYTES/PACKET/GUARD、
   BSP DDR 上下界及实际 ABI 大小；与 BD 采集参数、XSA DDR/HP0 范围和 DMA 长度位数核对。
4. 最终 ELF 中的合同必须与目标文件一致，并检查全部非空 SHF_ALLOC 区间、PT_LOAD、
   堆/栈及真实 end 符号。报告地址由该校验结果生成，不再使用固定地址作为未经核实的报告值。
5. 首版只放行既有固定合同；其他缓冲区搬迁即使数学上可行也拒绝，须另行审核。
   源码、预处理输入、目标文件、链接脚本、ELF、map、参考 XSA/BD、编译参数均记录来源和哈希。

再次复现必须换一个尚不存在的输出目录，不能删除失败目录来复用名字。
已有目录、路径重叠、缺依赖、已改变输入、旧单麦 BD、未知外部引用或脚本钩子均应拒绝；
不得用 --force、宽泛删除、还原旧 recovery 或覆盖真实 one 来绕过。

## 安全措施与已知限制

1. 目标以原子 mkdir 独占创建；没有递归删除、覆盖已有输出或续写失败输出的选项。
2. 输出不能位于实际工程、BSP、PS 源、工具或入口目录内部，也不能包含这些输入。
3. 工程/输出的符号链接、junction/reparse point 拒绝；AMD 安装器的只读工具链接可解析到真实工具路径后使用。
4. XPR 已登记源文件必须位于工程目录；旧 ImportPath 只是导入来源记录，不要求复活已删除历史副本。
   未支持的外部路径、运行目录和 Tcl 前后钩子应先人工整理，不自动执行。
5. 工具只打开快照 XPR，Tcl 再核对已注册文件和运行目录均在快照内。
   在新快照中强制重新验证并生成 IP/BD 输出，防止“已验证/已生成”状态掩盖缺失的 SmartConnect 子设计；
   工具内部的 -force 只用于该次独占快照的生成物，不是允许覆盖用户已有输出目录。
   综合后还检查未解析黑盒，发现即停止，不等到实现阶段才报错。
6. 原件在复制前后、构建结束时比较 SHA-256；变化时结果标 INPUT_CHANGED_BUILD_INVALID，
   不用自动恢复/重置覆盖并发修改。构建期间不要另一个任务同时修改输入。
7. 实际 one 的所有输入始终按字节哈希保护。副本内手写 RTL/XDC 仍逐字节比较；
   工具生成的 system_wrapper.v 只允许 Date/Host 注释及行尾不同，正文变化仍拒绝。
   强制验证可能将原 XCI 已有值展开到副本 BD：只允许新增值逐项匹配原 XCI，
   原有 BD 参数、结构、端口、地址与其他字段必须完全不变，否则失败。每个展开项写入 result.json；
   这不是修改设计参数；HWH/BSP 仍按前述可审计等价规则检查，原始 BD/wrapper 不改写。
8. 工具和 Tcl/XDC 输入必须可信；路径保护不是执行任意恶意 Tcl 的安全沙箱。
   Windows 路径中的命令元字符主动拒绝；普通空格支持。
9. 保持既有外部 IO 时序/实测风险暂缓，不增约束、不调算法来“过时序”。
10. 不设“单击运行到板上”的入口。所有结果仅为离线构建自检，仍须准确范围的独立复核。

## 输出与判读

~~~text
<fresh-output>/
  preflight.json             输入位置、116 项左右的实际依赖及保护哈希（以本次清单为准）
  build_current.py           本轮实际入口快照
  ps_contract.py             本轮实际 PS 合同校验器
  build_hw.tcl               本轮实际 Tcl 快照
  ps_check/                  实际包装单元/.i/.o/ELF/map、编译合同与链接范围结果
  inputs/project/            当前工程复制件；包含本轮生成的 Vivado 缓存/运行文件
  inputs/bsp/                本轮链接的 BSP 输入复制件
  inputs/ps/                 未修改的 PS 源文件复制件
  inputs/bsp-reference.xsa    BSP 对应 XSA
  logs/                      命令参数、工作目录、版本、编译与失败输出
  reports/                   综合/实现状态、资源、时序、DRC、方法学、时钟、IO
  artifacts/hw/              system_c_adapter.bit / system_c_adapter.xsa
  artifacts/ps/              four_mic_capture.elf / four_mic_capture.map
  artifacts-sha256.json      logs/reports/artifacts 的大小与 SHA-256
  result.json                最终状态、输入保护、BSP 配对、内存边界与时序
~~~

- 工具版本由 Vivado 内部 version 命令核对和保存；Windows 的 vivado.bat -version 可能输出正常版本却返回 1，不据此误判安装失败。
- 只有所有步骤完成、BSP 硬件描述匹配、程序末端不覆盖 RX、内部 setup/hold/pulse width 无负裕量、
  原件未变化，才输出 BUILD_PASS_NOT_BOARD_TEST。
- 生成 bit 不代替时序判读；查看 WNS/TNS/WHS/THS/WPWS/TPWS 和完整 timing-summary.rpt。
  外部未约束路径、方法学告警仍按原边界单独说明，不消音、不升级为实板通过。
- 不承诺与历史产物位对位相同：生成时间、__DATE__/__TIME__、调试路径可能使 bit/XSA/ELF 哈希不同。
  可复现指明确输入、过程、约束、工具/BSP 与可检查结果；每轮保存自己的哈希。
- 本地完整构建目录含可再生缓存、工具/BSP输入和二进制，不整体重复提交到仓库。
  交付保留本批入口、测试、命令、原始报告/日志和哈希索引；产物及复现依赖留在明确位置，公开范围由工作执行/复核确认。
- 失败目录不作为下次构建输入；后续清理须先确认本批复核、独有材料、依赖及恢复位置，本入口不清理它们。

最终结果与未完成项见 RESULTS.md；本轮不自行提交、推送、批准或合并，也不更改已完成 H2 诊断结论。
