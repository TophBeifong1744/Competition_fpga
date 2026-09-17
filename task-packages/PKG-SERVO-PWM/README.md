# 单路 360° PWM 舵机驱动

本任务包提供纯 Verilog 驱动、自检 testbench、仿真运行入口和 Vivado 工程创建脚本。任务分支为 `codex/servo-pwm-driver`，从用户指定仓库当时的本地 `main` 创建；创建时本地 main 比缓存的 origin/main 落后 52 个提交，本次没有拉取或合入远端变更。

本包为新增待复核模块，未修改既有已批准 RTL 库、one 工程或 BD。器件目标根据仓库环境记录为 `xc7z020clg400-2`；照片本身不证明完整速度等级。具体实测结果见 [VALIDATION.md](VALIDATION.md)。

## 一页复核入口（2026-09-17 补做 Vivado 2025.2）

| 字段 | 本次交付 |
|---|---|
| 任务 / 作者 / 复核人 | PKG-SERVO-PWM；本任务用户与 Codex 实现；由非作者成员独立复核，若作者为 A 则交 B；尚未收到独立复核结论 |
| 固定版本 | 仓库 https://github.com/TophBeifong1744/Competition_fpga ，分支 `codex/servo-pwm-driver`。上一已发布候选 `34e9c9c961bd8501df2c540a09d6a894dfcae9c9`；本次最终 SHA 以发布回执固定，不再复核旧 SHA |
| 基线 / 规则 | 实现源自 `9b74815ba838ef1132e64105f8a228dcef164b7a`，共同基线 `99cf1dc2c1e7e2bd60ca843839d47906f9b84770`。采用 main `02b578c730c539e7fb45e11386567f28ffe7ab71` 的 [六项规则](https://github.com/TophBeifong1744/Competition_fpga/blob/02b578c730c539e7fb45e11386567f28ffe7ab71/docs/team-workflow.md#review-efficiency)；候选内规则较旧，勿仅按旧规则执行 |
| 申请范围 | 本包模块级技术复核：角度映射、PWM、限幅/舍入、复位和周期更新、TB 判据、运行脚本、2018.3/2025.2 功能仿真证据与文档；不申请综合时序、BD 集成或实板通过 |
| 本次变化 | 相对上一候选仅更新运行脚本默认工具路径及新输出目录保护、README/VALIDATION，新增 2025.2 日志；RTL、TB、工程创建 Tcl 和旧证据保持原字节。脚本变更已实际执行测试，不当作纯文档免测 |
| 输入 / 依赖 | 用户确认 20 ms 下 2.5%~12.5% 对应 0~360°；9 位无符号整数角度、同域稳定输入、同步释放复位。默认 100 MHz 是接口要求，非晶振实测；无外部数据与第三方 RTL。工具路径 `C:/AMDDesignTools/2025.2/Vivado/bin` |
| 独立复核建议 | 若此前尚未开始独立复核，首次完整审本包；若已有绑定旧 SHA 的结论，再按差异和影响链复审。关注脉宽/周期边界、舍入/限幅、周期内更新、复位重启、脚本失败传播和新目录保护，必要负例由复核人决定 |
| 运行入口 | 固定最终 SHA 的独立 worktree，从仓库根执行下方两条命令。脚本默认每轮生成唯一目录；可用 `-OutputDirectory` 指定不存在的新目录，已存在则报错。完整 stdout/stderr、退出码和工具版本另存本轮新证据目录 |
| 结果 / 复用 / 未测 | 本次真实运行 2025.2：100 MHz、1 MHz 各 39 项检查 PASS；相同检查的两个配置，不累加为不同用例。已存在输出目录拒绝覆盖检查 PASS。2018.3 证据复用、未重跑。见 [VALIDATION.md](VALIDATION.md)。2025.2 工程创建/BD、综合/实现/时序、实板未测 |
| 已知限制 | 作者自检不代替批准。回位由上层发送安全目标角度；不含独立 home/enable、平滑运动和位置反馈。电气兼容、实际时钟与针脚仍需核实。新路径保护不改变波形合同 |
| 集成 / 收尾 | 若独立批准活动库接入，建议 `rtl/servo/motor_drive.v`、`tb/servo/tb_motor_drive.v`，运行入口纳入 sim 并更新已有清单；搬迁须验证实际加载位置并做相称测试，勿直接搬走依赖包布局的脚本。实际工程修改/综合实现按最新用户操作约定执行。未批准前保留原包，不自行合入 main；仅本批全部入库且无继续工作后可清理任务短分支及可重建缓存，保留原证据 |

复跑命令（新候选独立 worktree 的根目录）：

```powershell
& .\task-packages\PKG-SERVO-PWM\scripts\run_xsim.ps1 -ClockHz 100000000
& .\task-packages\PKG-SERVO-PWM\scripts\run_xsim.ps1 -ClockHz 1000000
```

非默认安装位置用 `-VivadoBin` 指定真实工具目录。回交绑定最终完整 SHA 的限定 PASS / NEEDS_FIX / BLOCKED，并区分本次运行、复用、未测、扩大范围原因。批准后按最新规则完成相称验证和发布收尾。

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

从仓库根目录，在 PowerShell 执行（默认本机已确认的 Vivado 2025.2 安装位置）：

```powershell
& .\task-packages\PKG-SERVO-PWM\scripts\run_xsim.ps1
```

指定其他版本和时钟参数：

```powershell
& .\task-packages\PKG-SERVO-PWM\scripts\run_xsim.ps1 -VivadoBin 'C:\AMDDesignTools\2025.2\Vivado\bin' -ClockHz 1000000
```

`-VivadoBin` 应指向实际含 xvlog.bat、xelab.bat、xsim.bat 的目录，使用其他版本时同样指定其真实 bin 目录。测试时钟随 ClockHz 变化；单个测试默认最长 400 ms 仿真时间。

预期：终端和 simulation.log 出现 `PASS motor_drive checks=39 CLK_FREQ_HZ=...`。异常波形、数值不符、工具失败或未出现 PASS 都视为失败。输出位于仓库 `sim/build/servo-pwm-<频率>-<运行时间>/`，包含编译/展开/运行日志及 XSim 临时文件；本次 2025.2 验证在包内保存编译、展开和运行日志文本，不提交生成工程和二进制。

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
