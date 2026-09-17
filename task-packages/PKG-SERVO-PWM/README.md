# 单路 360° PWM 舵机驱动

本任务包提供纯 Verilog 驱动、自检 testbench、仿真运行入口和 Vivado 工程创建脚本。任务分支为 `codex/servo-pwm-driver`，从用户指定仓库当时的本地 `main` 创建；创建时本地 main 比缓存的 origin/main 落后 52 个提交，本次没有拉取或合入远端变更。

本包为新增待复核模块，未修改既有已批准 RTL 库、one 工程或 BD。器件目标根据仓库环境记录为 `xc7z020clg400-2`；照片本身不证明完整速度等级。具体实测结果见 [VALIDATION.md](VALIDATION.md)。

## 一页复核入口（2026-09-17 增量复核）

| 字段 | 本次交付 |
|---|---|
| 任务 / 作者 / 复核人 | PKG-SERVO-PWM；本任务用户与 Codex 实现；请交给非作者成员独立复核，若作者为 A 则由 B 复核；未代替其他成员确认接收 |
| 固定版本 | 仓库 https://github.com/TophBeifong1744/Competition_fpga ，分支 `codex/servo-pwm-driver`；已直接查询远端的实现 SHA：`9b74815ba838ef1132e64105f8a228dcef164b7a`。本入口是随后仅 README 的补充提交，最终候选完整 SHA 由发布回执/提示词固定；该候选的其余 8 个文件必须与上述实现 SHA 相同 |
| 基线 / 规则 | 首次交付，无旧独立复核结论；分支基线 `99cf1dc2c1e7e2bd60ca843839d47906f9b84770`。交付核查时远端 main 为 `02b578c730c539e7fb45e11386567f28ffe7ab71`，比共同基线领先 52 个提交。采用该 main 的 [统一规则](https://github.com/TophBeifong1744/Competition_fpga/blob/02b578c730c539e7fb45e11386567f28ffe7ab71/docs/team-workflow.md#review-efficiency) 和 [一页模板](https://github.com/TophBeifong1744/Competition_fpga/blob/02b578c730c539e7fb45e11386567f28ffe7ab71/docs/templates/review-brief.md)，不要只读取候选内旧规则 |
| 申请范围 | 本包 9 个文件的模块级技术复核：PWM、角度映射/限幅/舍入、复位、周期更新、TB 判据、脚本与说明；不申请机械到位、2025.2 兼容、综合时序、板测或 one/BD 生产接入批准 |
| 变化 | 相对共同基线新增独立包；实现提交后仅补本 README 的交付索引，RTL、TB、运行脚本、原测试证据不变；无其他模块依赖或主线源码修改 |
| 输入 / 依赖 | 用户确认 20 ms 周期下 2.5%~12.5% 对应 0~360°；默认 100 MHz 是接口配置要求，不是实测晶振结论。Windows PowerShell、Vivado/XSim；作者验证工具为 2018.3。无外部数据输入、无第三方 RTL；9 位角度须同域稳定，复位须同步释放 |
| 独立复核建议 | 首次完整审本包合同/实现/测试判据，独立验证端点、1 us 边界、舍入、上限、周期中更新、异步复位及重启；检查错误参数负例、测试超时/失败传播、脚本平台兼容性。由复核人决定实际检查范围，不将作者 PASS 直接视为批准 |
| 运行入口 | 在固定最终候选 SHA 的独立干净 worktree，从仓库根执行下方两条命令。脚本输出目录固定，每轮使用新 worktree，运行前要求对应 sim/build 目录不存在；完整 stdout/stderr 和退出码另存本轮新日志目录。不要在作者原工作区复跑覆盖旧日志 |
| 结果 / 未测 | 复用 [VALIDATION.md](VALIDATION.md) 的作者证据：100 MHz、1 MHz 各 39 项检查 PASS，同一组检查的两个配置，不算 78 个独立用例；工程创建成功。本次文档交付只核对 Git 身份、文件与链接，未重跑仿真；独立复核尚未执行。2025.2、综合/实现/时序、实板均未测 |
| 已知问题 | 交付完整性核查未发现阻断，不代表技术无缺陷。非阻断观察：运行脚本会复用固定输出目录，须独立新工作树；工具路径需按复核机器修改。独立 home/enable、平滑运动、位置回读不在本版实现；回位由上层送安全目标角度，逻辑复位不等于回位 |
| 集成 / 收尾 | 本轮先申请模块级批准。若批准活动库接入，建议源码 `rtl/servo/motor_drive.v`、TB `tb/servo/tb_motor_drive.v`，运行入口纳入 `sim`，更新已有清单；搬迁时核对真实加载路径并运行相称测试，不直接把依赖包布局的脚本挪走。板级接入由用户按最新 Vivado 操作约定决定，不自动生成/下载 bitstream。未准入部分保留本包说明原因。只有确认本批完整入库且无继续工作后，才能清理本任务短分支和仿真缓存，保留原证据；本轮不删除、不合入 main |

复跑示例（独立新 worktree 的仓库根目录；按本机修改 VivadoBin）：

```powershell
& .\task-packages\PKG-SERVO-PWM\scripts\run_xsim.ps1 -VivadoBin 'D:\Vivado\2018.3\bin' -ClockHz 100000000
& .\task-packages\PKG-SERVO-PWM\scripts\run_xsim.ps1 -VivadoBin 'D:\Vivado\2018.3\bin' -ClockHz 1000000
```

复核回交请绑定最终候选完整 SHA，结论为限定范围 PASS / NEEDS_FIX / BLOCKED；分别记录本次运行、复用依据、未测、扩大检查原因及原始日志。集中反馈同类问题；返修才采用增量复审。批准后的合入/相称验证/推送/本地与远端核对按上述最新规则执行，不夹带未审提交。

## 文件入口

| 文件 | 用途 |
|---|---|
| [rtl/motor_drive.v](rtl/motor_drive.v) | 综合源码和中文注释，无其他 RTL 依赖 |
| [tb/tb_motor_drive.v](tb/tb_motor_drive.v) | 输入输出边沿自检、失败立即报错、超时保护 |
| [scripts/run_xsim.ps1](scripts/run_xsim.ps1) | Windows XSim 一键自检，检查退出码及 PASS 标志 |
| [scripts/create_project.tcl](scripts/create_project.tcl) | 创建独立 Vivado 模块仿真工程 |

## 功能和接口

接口 v1。默认时钟为 100 MHz，必须根据实际连接设置 `CLK_FREQ_HZ`。支持不小于 1 MHz 的整数 MHz 时钟。PWM 周期固定为 20 ms，脉宽计数分辨率 1 us。输入为 9 位无符号整数角度，1 LSB = 1°，超过 360 的数值饱和到 360。

| 端口 | 方向/位宽 | 含义 |
|---|---|---|
| clk | 输入/1 | 唯一主时钟 |
| rst_n | 输入/1 | 低有效异步复位；系统应同步释放 |
| angle_deg_i | 输入/9 | 同时钟域稳定目标角度，无握手 |
| pwm_o | 输出/1 | 寄存器驱动的舵机 PWM |

角度映射以用户本次明确确认的关系为依据，不冒充新版手册提供了逐点对应表：

`pulse_us = 500 + round(angle_deg * 2000 / 360)`

| 角度 | 高电平时间 | 占空比 |
|---|---|---|
| 0° | 500 us | 2.5% |
| 90° | 1000 us | 5% |
| 180° | 1500 us | 7.5% |
| 270° | 2000 us | 10% |
| 360° | 2500 us | 12.5% |

整数换算四舍五入，最大数值舍入误差不超过 0.5 us；这不是舵机机械精度承诺。乘法中间值显式扩为 32 位。常数除法可综合，但资源和时序须以实际综合报告为准。

## 时序行为

1. 复位期间立即输出低电平并清空状态；复位可截断当前脉冲。
2. 释放复位后的第一个有效时钟，采样角度并立即开始完整周期。
3. 周期中输入变化不改变当前脉宽，只在下个周期边界采样最新输入；命令延迟最多约 20 ms。
4. 输入必须跨越采样边沿稳定。短暂角度命令可能被漏采；模块不保存命令队列。同周期的多次更新以采样时最新值为准。
5. 脉冲结束后保持低电平到周期末。没有新命令时持续发送当前目标位置。

100 MHz 时，微秒分频计数为 0~99；微秒周期计数为 0~19999。`us_tick` 是计数使能，不是门控时钟。输出寄存器在计数推进时按下一微秒区间更新，避免多 1 us 的错误。

## 回位、复位和限制

逻辑复位不是舵机回位。要回到中位，由上层将 `angle_deg_i` 稳定设为 `9'd180`；下个 PWM 周期输出 1500 us，不能据此认定机械已经到位。安装回位角度可由上层选择其他安全值。

本版忠实实现聊天中确认的基础模块：不含独立 home/enable 端口、平滑速度规划、实际角度回读或到位标志。需要专用回位命令时可在上层选择 home angle；需要平滑运动时应按周期逐步改变目标。上电未知实际角度，首次动作可能快速跳转。

0°与360°按区间两个端点编码，不自动跨零点规划最短路径。驱动支持一圈角度命令不代表云台支架、俯仰轴和线缆允许全部行程。机械安全范围应在上层进一步限制。

## 运行自检

从仓库根目录，在 PowerShell 执行（默认本机已发现的 2018.3 安装位置）：

```powershell
& .\task-packages\PKG-SERVO-PWM\scripts\run_xsim.ps1
```

指定其他版本和时钟参数：

```powershell
& .\task-packages\PKG-SERVO-PWM\scripts\run_xsim.ps1 -VivadoBin 'D:\Vivado\2018.3\bin' -ClockHz 1000000
```

`-VivadoBin` 应指向实际含 xvlog.bat、xelab.bat、xsim.bat 的目录，使用 2025.2 时同样指定其真实 bin 目录。测试时钟随 ClockHz 变化；单个测试默认最长 400 ms 仿真时间。

预期：终端和 simulation.log 出现 `PASS motor_drive checks=39 CLK_FREQ_HZ=...`。异常波形、数值不符、工具失败或未出现 PASS 都视为失败。输出位于仓库 `sim/build/servo-pwm-<频率>/`，包含编译/展开/运行日志及 XSim 临时文件；本次验证仅在包内保存运行日志文本，不提交生成工程和二进制。

## 在 Vivado 中使用

已有工程：把 `rtl/motor_drive.v` 加入 Design Sources，把 `tb/tb_motor_drive.v` 加入 Simulation Sources，仿真顶层选 `tb_motor_drive`，运行 Run All，观察 PASS 标记。需要波形时把 clk、rst_n、angle_deg、pwm 加入波形窗口。

创建独立工程：从仓库根目录执行（vivado 已加入 PATH）：

```powershell
vivado -mode batch -source .\task-packages\PKG-SERVO-PWM\scripts\create_project.tcl
```

预期输出 `vivado/build/servo_pwm/servo_pwm.xpr`；目录已存在时脚本拒绝覆盖。打开工程后运行 Behavioral Simulation。该脚本不会运行实现或输出 bitstream。

集成时，在你的上层模块实例化：

```verilog
motor_drive #(.CLK_FREQ_HZ(100_000_000)) u_motor_drive (
    .clk(clk_100m),
    .rst_n(reset_n),
    .angle_deg_i(target_angle_deg),
    .pwm_o(servo_pwm)
);
```

作为 BD Module Reference 时入口为纯 Verilog 的 motor_drive；不要将已有 BD 顶层替换成此模块。跨时钟域角度总线需握手/一致性传输，不能仅对各位独立打两拍；按键需同步消抖。

## 接线和下一步

舵机独立电源与 FPGA 共地，PWM 为控制信号，不由 GPIO 给舵机供电。需确认 IO Bank 电压和舵机信号门限。未获得该板准确 PL 时钟和 PWM 引脚依据，因此本包不编造 XDC 引脚、不生成可下载 bitstream。

下一步：确认实际时钟源、引脚和 IO 标准，在目标 Vivado 2025.2 工程验证模块接入、综合、实现与时序，再用示波器核实周期/脉宽，最后在机械安全范围内测试舵机。仿真通过不等于板上通过。
