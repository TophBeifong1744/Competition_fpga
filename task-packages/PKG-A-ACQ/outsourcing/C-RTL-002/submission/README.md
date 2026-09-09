# C-RTL-002 错误统计快照交付 v1.1

**状态：RTL 审查、增强功能仿真、错误注入检查、独立综合均通过；待 B 正式复核。**
本次未发现需要修改的 RTL 功能错误，修订集中在测试覆盖和证据完善。

## 版本与约定

- 作者：Codex，按成员 C 请求实现并进行本次自查；不是第三方独立验收，不代签 B 批准。
- 日期：2026-09-09；当前版本 v1.1。
- 唯一交付分支：`codex/c-rtl-001-outsourcing-docs`；不合并 main。
- 初始工作基线：`896ce7ad983e3c4781af4fcdf7092cca5cad37f0`。
- 上一版交付提交：`716cd4b0b1bae673b639827fc36f993603634e63`。
- 当前交付提交在仓库根目录用 `git log -1 --format=%H -- task-packages/PKG-A-ACQ/outsourcing/C-RTL-002/submission` 定位；文件精确内容由 file-manifest.json 标识。
- 工具：Vivado/XSim 2025.2，SW Build 6299465；器件 xc7z020clg400-2。
- 任务依据：[原操作单](../instructions/README.md)。
- 按用户后续要求，新 RTL 和 TB 使用 Verilog .v，已用不带 --sv 的 xvlog 编译。替代原操作单的新建 .sv 文件名要求；行为和端口定义不变。
- 后续约定：简单模块用 .v；复杂模块可用 .sv 内核加 .v 包装。仅指定的 001 参考依赖保留原始 .sv，单独以 --sv 编译，不改原 001。

## 功能审查结论

`stream_error_snapshot` 参数 COUNT_WIDTH 默认 32，支持 1～64。clk 上升沿：
1. rst_n=0：两个计数、两个 sticky、snapshot_valid 全部清零，优先于请求。
2. rst_n=1：valid 更新为 req；req=1 时同时保存四项 live 输入，req=0 时保持保存数据。

无边沿检测、异步复位、额外流水级、busy、计数或饱和逻辑。count 与 sticky 无论是否一致均原样保存。
与 001 同沿运行时捕获更新前的值；下一拍请求才捕获更新后的计数或 clear 结果。
RTL 相对 v1.0 未改，SHA-256：
`fe4b8bd5559ca8883044c23406f0dc637d72844bcc767c3320941ba025d6abe6`。

## 文件与来源

| 路径 | 内容 |
|---|---|
| rtl/stream_error_snapshot.v | Verilog 设计源 |
| tb/tb_stream_error_snapshot.v | 参数化 checker、标准四位宽顶层、1～64 全位宽顶层 |
| tb/tb_stream_error_snapshot_integration.v | 001+002 联合自检，32 个定向步骤 |
| reference/stream_error_stats.sv | 指定 001 的原始 Git blob |
| run_tests.ps1 | 三组正向仿真的一键命令 |
| audit_mutations.ps1 | 六种临时错误副本的判错能力验证，不修改正式 RTL |
| audit_synthesis.tcl | 1、32、64 位独立综合和寄存器结构检查 |
| logs/ | 当前三组仿真的八份原始工具日志 |
| logs/mutations/ | 六种错误注入各自的编译、展开、仿真日志及 summary.json |
| logs/synthesis/ | 独立综合原始日志、资源报告和 summary.txt |
| logs/v1-0/ | v1.0 完整运行的六份历史原始日志 |
| logs/attempt-01/ | 最初因日志判读脚本误报而中止的四份工具日志 |
| audit-report.md | 本次审查发现、修订和验收边界 |
| .gitignore / .gitattributes | 仅本包日志放行，保持文件字节，不改根规则 |
| file-manifest.json | 全部其他文件的相对路径、字节数、SHA-256；不含自身 |

001 依赖提交：`ac8a7bb60d94c069f5f1b61e9fc38658b0742962`。
来源路径：`task-packages/PKG-A-ACQ/outsourcing/C-RTL-001/submission/rtl/stream_error_stats.sv`。
SHA-256：`333dc4d193169982a6609c886a48968e87ef2631496d0c90137d24f228a94afe`。
提取文件与 Git blob 一致，未经修改。

## 功能仿真复现

需要 Windows PowerShell 7 和 Vivado/XSim 2025.2。在本 submission 目录执行：

```powershell
& .\run_tests.ps1 -VivadoBin 'C:\AMDDesignTools\2025.2\Vivado\bin'
```

脚本根据自身目录定位源码，默认在系统临时目录创建唯一的新目录。
可加 `-RunDirectory 'C:\temp\snapshot-audit-new'` 指定尚不存在且位于交付包外的目录。
每步检查退出状态；仿真日志还必须有 ALL TESTS PASS 且无行首 FAIL/FATAL/ERROR/TIMEOUT。
预期输出：compile_verilog.log、compile_reference.log、三个 *-elaborate.log、三个 *-simulate.log 和临时 XSim 缓存。
最后打印 VERIFIED ALL THREE TEST TOPS 和输出路径。下一步核对下面的覆盖和成功标志，提交 B 复核。

等效命令（在已配置 Vivado 环境的新临时目录内，将 <submission> 换为绝对路径）：

```text
xvlog "<submission>/rtl/stream_error_snapshot.v" "<submission>/tb/tb_stream_error_snapshot.v" "<submission>/tb/tb_stream_error_snapshot_integration.v" -log compile_verilog.log
xvlog --sv "<submission>/reference/stream_error_stats.sv" -log compile_reference.log
xelab work.tb_stream_error_snapshot -s tb_stream_error_snapshot -debug typical -timescale 1ns/1ps -log tb_stream_error_snapshot-elaborate.log
xsim tb_stream_error_snapshot -runall -log tb_stream_error_snapshot-simulate.log
xelab work.tb_stream_error_snapshot_integration -s tb_stream_error_snapshot_integration -debug typical -timescale 1ns/1ps -log tb_stream_error_snapshot_integration-elaborate.log
xsim tb_stream_error_snapshot_integration -runall -log tb_stream_error_snapshot_integration-simulate.log
xelab work.tb_stream_error_snapshot_all_widths -s tb_stream_error_snapshot_all_widths -debug typical -timescale 1ns/1ps -log tb_stream_error_snapshot_all_widths-elaborate.log
xsim tb_stream_error_snapshot_all_widths -runall -log tb_stream_error_snapshot_all_widths-simulate.log
```

默认32位 DUT 没有参数覆盖。三个顶层均有100 us超时。下降沿驱动，上升沿后1 ns比较；额外连续监视沿间输出变化。
新 TB 使用 Verilog 语法，并按任务要求使用 XSim 支持的 $fatal。xelab 默认时间单位用于保留001无 timescale 的源文件原样。
每次比较使用 !== 检查两项计数、两项标志和 valid，失败打印位宽、用例和预期/实际；联合测试还检查001实时输出。

## 当前实测结果

| 检查 | 结果 | 证据与范围 |
|---|---|---|
| Verilog 编译及001参考编译 | PASS | 两份 compile 日志 |
| 标准1、3、默认32、64位 | PASS | 单实例完成时打印769、1745、953、1209次比较；顶层8707 ns结束 |
| 全部合法1～64位 | PASS | all_widths 日志中64个宽度分别通过；8707 ns结束 |
| 001联合测试 | PASS | 32个步骤，326 ns结束 |
| 六种错误注入 | 全部检出 | mutations/summary.json 和各 simulate.log |
| 1、32、64位独立综合 | PASS | synthesis/summary.txt；FDRE分别5、67、131个，锁存器和异步复位触发器均0 |
| 资源时序验收、布局布线、板测、BD接入、CDC、PS协议 | NOT_RUN | 未执行，不由功能仿真或独立综合替代 |

```text
ALL TESTS PASS: COUNT_WIDTH=1,3,default32,64
ALL TESTS PASS: integration COUNT_WIDTH=3 checks=32
ALL TESTS PASS: every COUNT_WIDTH from 1 through 64
ALL 6 MUTANTS DETECTED
ALL SYNTHESIS CHECKS PASS
```

检查次数不是独立用例数。全位宽覆盖也不是穷尽64位数据或全部时序状态的形式证明。

## 任务指标与特殊情况

| 指标 | 覆盖 |
|---|---|
| 复位优先于请求 | reset wins over request；另补无请求时从非零状态复位 |
| 同步复位时机 | 沿间拉低保持，下一上升沿才清零；另测完全位于沿间的复位短脉冲 |
| 无请求时初始零与长期保持 | 初始8拍、后续32拍live变化；valid撤销与快照保持同时检查 |
| 单拍请求和连续请求 | 连续16拍四项变化；不要求插空拍 |
| 0、全1、最高位、交替位 | 每种交叉sticky的00/01/10/11；包含64位最高位 |
| 中间位错误和串路 | 两路分别逐位 walking-one、walking-zero，覆盖每一位 |
| 小位宽输入组合 | W=1、2、3遍历全部两个计数与sticky组合，每次捕获后验证保持 |
| 更广控制序列 | 每位宽256拍，固定种子64位xorshift数据、混合请求及周期性复位，可重复 |
| 沿间请求/live时机 | 每次下降沿后检查；独立请求、数据、复位短脉冲；连续输出变化监视器捕捉沿间变化 |
| 复位恢复 | 重新请求时valid与数据同拍更新 |
| 默认参数与范围 | 默认32不覆盖参数；1～64逐一展开和仿真 |
| 同沿event+req旧值 | 单路和双路事件；下一拍获取更新值 |
| 同沿clear+req旧值 | 清零前快照、下一拍清零结果；覆盖clear+事件00/01/10/11 |
| 饱和与清零相互作用 | 001真实事件累加至7，再连续4拍饱和；饱和后clear+event+req、连续clear |
| clear无req | 001清零而002旧快照保持，后续请求得到零 |
| 自动失败机制 | 六种错误副本触发实际FAIL/$fatal，编译失败和超时均不算成功检错 |

## 错误注入与综合复现

错误注入：
```powershell
& .\audit_mutations.ps1 -VivadoBin 'C:\AMDDesignTools\2025.2\Vivado\bin'
```
预期在新临时目录生成六个错误副本、原始日志和summary.json。六项应全部DETECTED；这些日志中的FAIL是预期的负向证据。
错误包含异步复位、无请求捕获、valid粘滞、计数串路、第17位取第19位、复位优先级错误。
脚本验证正式RTL前后哈希不变。下一步核对每项具体失败原因，不能把工具编译错误当成检错成功。

独立综合：在已配置 Vivado 的命令提示符进入一个新临时工作目录执行：
```text
vivado -mode batch -source "<submission>/audit_synthesis.tcl" -log synthesis.log -nojournal -tclargs "<new-output-directory>"
```
输出目录必须尚不存在且在交付包外。预期生成3份utilization-width*.rpt和summary.txt。
使用xc7z020clg400-2；检查FDRE数量=2*COUNT_WIDTH+3、无锁存器、无异步复位触发器。
下一步阅读报告。没有创建时钟/IO时序约束，因此本项是可综合性和结构核查，不是频率或时序收敛结论。

## 本地 Vivado 工程

`D:\vavido_project\stream_error_snapshot\stream_error_snapshot.xpr`。
当前RTL、两个TB和001参考均已同步到工程内部，哈希记录在工程local_checks/source-sync-manifest.json。
默认sim_1顶层是tb_stream_error_snapshot，sim_integration是联合测试。打开后启动Behavioral Simulation，再输入run all。
全位宽测试顶层为tb_stream_error_snapshot_all_widths，位于同一个TB文件，可在Vivado中将其设为仿真顶层运行。
D盘完整工程和缓存不提交到Git，正式交付仅在本submission目录；同步是本次执行的复制，不是自动双向监视。
D盘历史工程仿真日志仍是v1.0；本次增强后的当前功能证据在本包logs/，两处当前源码逐字节一致。

## 历史修正与边界

v1.0首次运行时，脚本的宽泛ERROR正则误匹配模块名中的error，提前停止；RTL自检已经通过但联合测试未运行。修正为行首错误标志后完整重跑通过。保留两次历史工具日志，不把人工说明当原始异常日志。

v1.1查出并补齐的是测试覆盖缺口，没有改RTL或001，也没有改期望值迁就错误。
综合脚本查询锁存器/异步触发器时，“No cells matched”告警表示预期数量为0；综合本身无错误。详见审查报告。
脚本仅在缺少PROCESSOR_ARCHITECTURE且确认为X64时补当前进程AMD64并恢复；没有重置全局环境。
控制输入须稳定同步到clk；亚稳态、非法参数、硬件X/Z行为不在本任务定义内。未进行形式验证或总工程接入。
