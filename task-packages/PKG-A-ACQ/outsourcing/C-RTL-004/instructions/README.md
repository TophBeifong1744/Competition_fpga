# C-RTL-004：001核心Verilog包装与独立BD接入操作单

版本1.0；日期2026-09-10。本批只有这一项：为已验证的错误计数核心补Verilog外壳，完成包装前后行为验证及独立BD烟雾测试。不开发新的声学模块，也不接入总工程。

## 1. 为什么做、先读什么

当前Vivado 2025.2 Module Reference流程要求纯Verilog顶层。001核心是已验证的SystemVerilog，应保留原件，通过薄包装接入，而不是改后缀或重写核心。

统一依据：项目docs/rtl-language-and-bd-integration.md，版本rtl-bd-policy-1.0。本分支发布时该规范尚未随主流程提交，因此提供[只读规范快照](references/rtl-bd-policy-1.0.md)供离线阅读，不另立规则版本。快照来自主工作目录同名文件，2026-09-10复制，SHA-256：f6af7daa2880147e2c38f29e7ebcd3987b6ed5f79d982047b2d547de13eb6810。未来规范变化先报告差异，不改本快照或历史验收。

这项外包仍归A，C按操作单执行，本聊天独立验收，B正式复核。001无需返工，002/003无需重做；本批不依赖它们接入总工程。

## 2. 固定依赖与唯一接口

核心：ac8a7bb60d94c069f5f1b61e9fc38658b0742962中
task-packages/PKG-A-ACQ/outsourcing/C-RTL-001/submission/rtl/stream_error_stats.sv。
SHA-256：333dc4d193169982a6609c886a48968e87ef2631496d0c90137d24f228a94afe。
从该提交提取到本包reference/，核对哈希；不要从个人工程中找一个“差不多”的副本。

新文件rtl/stream_error_stats_bd.v，模块stream_error_stats_bd，parameter integer COUNT_WIDTH=32，合法1～64。内部实例化一次stream_error_stats，参数原样传递。顶层只用Verilog语法，普通wire端口，不写logic/always_ff/struct/interface。

| 端口 | 方向 | 位宽 | 语义 |
|---|---|---|---|
| clk | 输入 | 1 | 唯一上升沿时钟 |
| rst_n | 输入 | 1 | 同步低有效复位 |
| clear | 输入 | 1 | 清历史并计入本拍事件 |
| overflow_event / drop_event | 输入 | 各1 | 每个高电平周期计一次，两路独立 |
| overflow_count / drop_count | 输出 | 各COUNT_WIDTH，无符号 | 原核心饱和事件计数 |
| overflow_sticky / drop_sticky | 输出 | 各1 | 原核心保持标志 |

不增加/改名端口，不增加寄存器、同步器、边沿检测、valid或AXI。无额外延迟、缩放或符号转换。复位最高优先；clear=1且事件=1，该路计数/标志为1；饱和不回绕。包装接口版本c-rtl-004-if-1.0，继承001操作单v1.0行为。

## 3. 直接按这个顺序实施

1. 建立下方submission目录，提取并核对reference核心。先写.v包装的端口和一份命名端口实例化，不动核心。
2. 建立tb/tb_stream_error_stats_bd.sv（也可.v）。同时实例化包装和原核心，喂同一组输入，比较全部输出；再用独立计数参考或明确期望核对行为，不能只用两个实例“彼此相同”作为全部证据。
3. 先跑COUNT_WIDTH=3，再跑1、默认32、64。默认32包装实例不覆盖参数。每拍输出稳定后用!==比较，失败打印用例/位宽/预期/实际并$fatal，设超时；全部通过才输出ALL TESTS PASS。
4. Vivado/XSim 2025.2中将包装按Verilog编译，核心按SystemVerilog编译，TB按实际语言。原核心没有timescale时使用xelab的默认1ns/1ps设置，不改核心文件。保存原始日志。
5. 仿真通过后，新建一个**包外独立RTL工程**，器件xc7z020clg400-2。工程名可用c004_bd_probe，不打开或另存共享one工程。
6. Add Design Sources只加包装.v和核心.sv；核对File Type。TB只放Simulation Sources，不重复导入同名核心。
7. Create Block Design，新建bd_probe。在画布Add Module，选择stream_error_stats_bd（不是内部SV核心）。将端口引出为外部端口，不接板，不添加PS、AXI、DMA或物理引脚约束。
8. 先用默认32位检查两路count宽度、方向及控制端口；执行Validate Design，保存Messages和Tcl Console原始日志。再将COUNT_WIDTH改为3，刷新模块并重复检查端口宽度和Validate Design。若参数在当前GUI不可编辑，保留错误并报告，不能只改截图标签。
9. 保存可重建该独立BD的Tcl及步骤（GUI导出Write Tcl可作为起点）；只提交脚本和日志，不提交缓存或完整工程。记录每次参数、端口表、是否Validate成功及所有警告。无错误不等于没有警告，警告逐项说明。

BD烟雾测试本身不要求生成system_wrapper、下载或实现；若工具生成包装，不要把共享工程顶层从system_wrapper改成stream_error_stats_bd。不添加未经确认的FREQ_HZ来冒充正式时钟合同；TB的仿真时钟不是板上频率证据。

## 4. 必须覆盖的功能测试

- 同步复位：沿间拉低不立即清零，上升沿清零；复位与clear/双事件同拍时全零。
- 空闲保持；单路事件及双路事件；连续事件逐拍累计；sticky保持。
- clear无事件、与各路/双路事件同拍；连续clear+事件保持1。
- 位宽1和3实际输入计数到饱和，再来事件不回绕，清除后可继续计数；不force计数器。
- 1、3、默认32、64包装与参考等价，核对没有错位、串路或额外一拍延迟。

无需更复杂的随机框架或穷举64位计数；先完成上述定向用例。

## 5. 集中交付

```text
C-RTL-004/
  instructions/README.md
  instructions/references/rtl-bd-policy-1.0.md
  submission/
    README.md
    rtl/stream_error_stats_bd.v
    reference/stream_error_stats.sv
    tb/tb_stream_error_stats_bd.sv
    scripts/                 实际仿真/独立BD重建脚本
    logs/                    编译、展开、仿真、BD原始日志
    file-manifest.json       相对路径、字节数、SHA-256，不含自己
```

README必须列出核心语言SV、BD入口stream_error_stats_bd.v、完整依赖及哈希、接口版本、参数、无符号位宽、无缩放、同步复位、包装延迟不变，以及核心/包装/BD/综合/时序/板测各自状态。

复跑脚本将输出写到新的包外目录，不覆盖submission里的原始日志；如作者需要更新证据，先保存旧版，核对源码与日志版本并重建清单。不要提交.Xil、xsim.dir、波形库或个人完整工程。局部放行所需日志，不改根.gitignore。

## 6. 停止条件与通过标准

包装仿真和独立BD添加、参数识别、Validate Design均是本项必需证据。若工具环境阻断，保存实际错误并标BLOCKED_ENV，本项等待补证，不以源码检查代替BD通过。不要重装、重置全局工具环境，也不要让C研究新的PS/AXI架构。

若发现必须改核心、改变接口或操作共享one/BD/PS才能继续，立即停止扩展并反馈。综合可选，时序/布局布线/板测均不要求，未运行写NOT_RUN。B复核通过后仍由A安排实际集成，本包独立BD通过不能宣称总工程已接通。

本批只有这一项，不追加005，也不重做001～003的历史交付。
