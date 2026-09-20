# 单路舵机 PWM 驱动

最终设计源码只有 **rtl/motor_drive.v**。调用者需要两路舵机时自行实例化两次。按用户要求已移除双路封装及其TB，运行脚本和工程脚本只使用单路驱动。

## 参数

| 参数 | 默认值 | 作用 |
|---|---|---|
| CLK_FREQ_HZ | 100_000_000 | 实际输入时钟，必须为正整数MHz |
| MAX_ANGLE_DEG | 360 | 舵机最大转角，合法范围1–511 |
| RESET_ANGLE_DEG | MAX_ANGLE_DEG / 2 | 复位目标角，合法范围0至最大角 |

360°舵机设置最大角360、复位角180；220°舵机设置最大角220、复位角130。参数在实例化时确定，修改后需要重新综合。

PWM周期固定20ms，0°对应500us（2.5%），最大角对应2500us（12.5%），超出量程自动限幅。微秒换算四舍五入。180/360对应1500us，130/220对应1682us。

## 端口和复位

| 端口 | 方向/位宽 | 用途 |
|---|---|---|
| clk | 输入1 | 时钟 |
| rst_n | 输入1 | 低有效复位；异步置位，调用者同步释放 |
| angle_deg_i | 输入9 | 目标角度，单位1° |
| angle_valid_i | 输入1 | 新角度命令有效，通常拉高一个时钟周期 |
| pwm_o | 输出1 | 舵机PWM |

按住复位时PWM为低，松开后持续发送RESET_ANGLE_DEG的PWM，直到收到新的有效角度命令。无valid时角度总线变化不覆盖回位位置。持续拉高valid会持续接受总线目标，因此建议单拍命令。上电须保证复位有效；按键同步释放和需要的消抖由上层处理。

角度与valid必须来自clk同一时钟域，valid有效上升沿锁存命令，周期边界应用最新命令。边界同拍接受的新命令在再下个周期生效；周期中不改变当前脉宽。跨时钟域命令需要一致性传输。没有机械反馈，发送回位PWM不代表已经到位。

## 调用者自行实例化两次

```verilog
motor_drive #(
    .CLK_FREQ_HZ(100_000_000),
    .MAX_ANGLE_DEG(360), .RESET_ANGLE_DEG(180)
) u_horizontal (
    .clk(clk), .rst_n(rst_n),
    .angle_deg_i(horizontal_angle), .angle_valid_i(horizontal_valid),
    .pwm_o(horizontal_pwm)
);

motor_drive #(
    .CLK_FREQ_HZ(100_000_000),
    .MAX_ANGLE_DEG(220), .RESET_ANGLE_DEG(130)
) u_vertical (
    .clk(clk), .rst_n(rst_n),
    .angle_deg_i(vertical_angle), .angle_valid_i(vertical_valid),
    .pwm_o(vertical_pwm)
);
```

上述是上层实例化片段，角度各9位，valid各1位，分别提交命令。端口可连接调用者的顶层信号，再在XDC中绑定实际物理引脚；驱动不固定管脚号，不需要额外的引脚参数。若使用内部PL时钟，不必给该内部时钟指定外部引脚。

## 仿真与工程脚本

源码：rtl/motor_drive.v。自检：tb/tb_motor_drive.v。实际证据见VALIDATION.md，历史记录保留但不代表当前交付仍包含双路封装。

在仓库根运行，默认工具C:/AMDDesignTools/2025.2/Vivado/bin，可用-VivadoBin覆盖：

```powershell
& .\task-packages\PKG-SERVO-PWM\scripts\run_xsim.ps1 -ClockHz 100000000 -MaxAngleDeg 360
& .\task-packages\PKG-SERVO-PWM\scripts\run_xsim.ps1 -ClockHz 100000000 -MaxAngleDeg 220
```

可改为-ClockHz 1000000测试1MHz。预期360配置61项PASS，220配置69项PASS。输出sim/build/servo-pwm-<频率>-<量程>-<时间>/，包含编译、展开、simulation.log及临时文件。-OutputDirectory可指定全新目录，已有目录拒绝覆盖。

```powershell
vivado -mode batch -source .\task-packages\PKG-SERVO-PWM\scripts\create_project.tcl -tclargs 220
```

预期输出vivado/build/servo_pwm_220/servo_pwm.xpr；参数省略默认360，对应servo_pwm_360。器件沿用xc7z020clg400-2，工程含一个RTL和一个TB，设计和仿真分别设置相应参数。目录已存在拒绝覆盖。打开Behavioral Simulation后Run All，不生成bitstream。

下一步由调用者将单路模块实例化两次，连接命令、时钟、复位和输出，设置实际引脚，再综合实现及板测。仿真不代表机械运动或时序验证通过。仓库活动目录原有未提交修改未覆盖，本轮最终代码在用户指定任务包中。
