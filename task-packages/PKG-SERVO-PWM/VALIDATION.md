# 验证记录

日期：2026-09-17。性质：作者自检，不是独立验收或板级通过。

分支：`codex/servo-pwm-driver`。
基线：本地 main `99cf1dc2c1e7e2bd60ca843839d47906f9b84770`。
基线当时落后缓存的 origin/main 52 个提交；未刷新远端，未改变 main。

## 首次执行（2018.3，历史证据保留）

工具：本机 `D:/Vivado/2018.3/bin`，Vivado/XSim 2018.3 (64-bit)，并非 2025.2。

| 检查 | 结果 |
|---|---|
| xvlog 编译 / xelab 展开 | 100 MHz 和 1 MHz 均成功 |
| 默认 100 MHz 自检 | PASS，39 项检查，结束于 281513065 ns |
| 最小允许频率 1 MHz 自检 | PASS，39 项检查，结束于 281572500 ns |
| create_project.tcl | 成功创建 xc7z020clg400-2 工程，源文件和仿真顶层设置成功 |

保留运行日志文本（工程创建日志仅去除行尾空格，原始日志仍在 sim/build）：[100 MHz](evidence/xsim-100mhz.txt)、[1 MHz](evidence/xsim-1mhz.txt)、[工程创建](evidence/project-create.txt)。命令见 README；编译和展开日志留在本地 sim/build 目录。

检查内容：复位低电平、0/90/180/270/360°、1/2/359°舍入、511°上限饱和、20 ms 周期、高电平中修改输入不截断、低电平中修改输入不产生额外脉冲、新目标下周期生效、高电平异步复位、低电平复位、释放后完整周期重启。所有波形检查依据对外端口边沿时间，不读取 DUT 内部状态。

## 调试过程

首次运行因工具进程缺少 PROCESSOR_ARCHITECTURE，旧版 Vivado 错选 32 位程序；运行入口增加临时架构变量恢复处理，不修改系统环境。随后发现 Windows .bat 把未保留引号的参数等号拆开，修正为保留字面引号后重新完整通过测试。RTL 无需因这两个工具启动问题修改。

## 尚未验证

- Vivado 2025.2 的工程创建及 BD 接入；编译/展开/功能仿真已补测通过。
- 综合资源、综合后仿真、布局布线、时序收敛。
- 板级引脚、IO 电平、实际时钟、PWM 实测和机械运动。
- 实际位置反馈/机械到位能力；本模块不提供这些接口。

没有生成 bitstream，也没有把作者自检称为系统验收。下一步按 README 核实板级连接后集成和板测。

## 2026-09-17 补做 Vivado 2025.2

本次只修改仿真运行脚本和文档，RTL、TB、工程创建 Tcl 与 34e9c9c 候选一致。工具由本机快捷方式定位为 `C:/AMDDesignTools/2025.2/Vivado/bin`，XSim 2025.2，SW Build 6299465。

| 配置 / 检查 | 实际结果 | 日志 |
|---|---|---|
| 100 MHz | xvlog、xelab、xsim 退出码均 0；39 项 PASS，结束 281513065 ns | [编译](evidence/2025.2-100mhz/xvlog.txt)、[展开](evidence/2025.2-100mhz/xelab.txt)、[运行](evidence/2025.2-100mhz/simulation.txt) |
| 1 MHz | xvlog、xelab、xsim 退出码均 0；39 项 PASS，结束 281572500 ns | [编译](evidence/2025.2-1mhz/xvlog.txt)、[展开](evidence/2025.2-1mhz/xelab.txt)、[运行](evidence/2025.2-1mhz/simulation.txt) |
| 输出目录保护 | 指定已存在的 100 MHz 输出目录，脚本在调用工具前按预期抛出 Output already exists；捕获确认，无日志覆盖 | 检查结果记录于本表 |

执行命令：从仓库根运行 `scripts/run_xsim.ps1`（实际包内完整路径见 README），分别设置 `-ClockHz 100000000`、`-ClockHz 1000000`，并设置 `-OutputDirectory` 为仓库 `sim/build/servo-2025-2-100mhz-01`、`sim/build/servo-2025-2-1mhz-01` 的绝对路径。两个目录均为本次新建。

运行脚本默认改为本机 2025.2 路径；未指定 OutputDirectory 时使用时间戳新目录，指定目录已存在时拒绝覆盖。测试判据未修改。同组检查在两个时钟配置分别运行，不算 78 个独立用例。2018.3 证据复用未重跑；本次不执行工程创建、综合实现或板测。独立复核仍待其他成员完成。