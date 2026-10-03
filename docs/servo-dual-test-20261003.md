# 独立双轴定角工程入口（2026-10-03）

本次新增配套顶层与 XDC，采用用户确认的接线/角度合同。它是下一阶段的新源码入口，不是历史实测版本证明，不改变 #19 的旧批准或现场记录。

## 源文件与使用方法

Vivado 工程仅添加以下三个文件，顶层设为 `servo_dual_test_top`：

| 文件 | 作用 |
|---|---|
| `project/rtl/servo/motor_drive.v` | 既有接口 v2 PWM 驱动，保持原字节 |
| `project/rtl/servo/servo_dual_test_top.v` | 两轴实例、启动有效信号和机械限幅 |
| `project/constraints/servo_dual_test.xdc` | 50 MHz/U18 时钟、水平 T15、垂直 W16 |

在 Vivado GUI 将仓库上述文件加入 Design Sources/Constraints，选择顶层，并检查源文件完整路径。用户导入后，停用旧 D 盘同名驱动、顶层和 XDC，避免重复模块和约束。不同时加载 LCD 约束：T15/W16 在既有 LCD 路径上分别涉及 rgb19/rgb17。本入口只用于独立舵机工程。

工具上下文为 Vivado 2025.2 / Navigator 板；仓库目标记录的速度等级 `-2` 与 D 盘旧 XPR 的 `xc7z020clg400-1` 存在差异。本次不创建 XPR，不选择或更改器件；实际构建前须确认工程准确器件/速度等级。本次没有构建、下载、复位或板上运动。

## 参数与行为

| 项目 | 水平 | 垂直 |
|---|---|---|
| 信号引脚 | T15 | W16 |
| 舵机完整电气量程 | 360° | 220° |
| 允许目标范围 | 0–360° | 40–220° |
| 配置启动/复位位置 | 180° | 130° |
| 默认目标参数 | `HORIZONTAL_DEG=180` | `VERTICAL_DEG=130` |

`CLK_FREQ_HZ` 默认 50,000,000，与当前 XDC 的 20 ns 一致。更改时钟参数必须同步修改约束。目标参数先进行有符号整数限幅，再转成 9 位角度；垂直 40° 下限属于机械限位，不改变驱动的 0–220° 电气映射。

配置初始化后，第 16 个时钟沿完成内部复位同步释放；第 17 个时钟沿两轴开始首个完整 PWM 周期，并接受一次有效目标命令。首周期使用复位位置，目标参数在下一 20 ms 周期边界生效。默认配置中目标与复位位置相同。水平复位脉宽 1500 us，垂直复位脉宽 1682 us；驱动的 500–2500 us 映射及四舍五入规则保持原样。

本顶层只有时钟和两路 PWM 端口，无运行时复位、动态角度输入、TTL、声源方向转换、反馈或机械到位判断。命令提交后持续输出目标 PWM；这不能证明舵机实际停止或到位。全部逻辑同一时钟域，不新增 CDC、寄存器总线、IRQ 或 DMA。配置启动依赖 FPGA 寄存器初始化；不引入外部复位引脚。

XDC 使用 LVCMOS33、DRIVE 4、SLOW；仅对外部 PWM 端口设置 false path，理由是舵机接收器异步测量脉宽，无共享采样时钟。内部时序路径仍需正式 STA，不填写虚构输出延时。

## 验证与交接

新增组合已使用 **XSim 2025.2** 完成原生编译、展开与运行：50 MHz 下 6 个参数场景，各观察 3 个完整 PWM 周期，共 54,000,306 次信号比较。正常测试输出 `TEST_PASS`；4 个负向 canary（脉宽、周期、启动沿、命令有效沿）均被检查器按预期拒绝。该结论限于 **FUNCTIONAL_SIM** 作者证据，已完成独立 AI 源码/证据复核；A 的成员接收仍待定，不表示板测或机械到位通过。综合、STA、实板验证均为 **NOT RUN**。

测试覆盖默认目标、负值和超量程参数限幅、两个轴的端点、同一脉宽的不同角度映射、首周期复位位置和一次有效命令。XSim 在负向 `$fatal` 下仍可能返回进程状态 0，因此负向结论依据日志中的断言失败和语义状态，不以进程状态 0 判定通过。

- TB：[`simulation/tb/servo/tb_servo_dual_test_top.sv`](../simulation/tb/servo/tb_servo_dual_test_top.sv)。
- 独立复核：[`FINAL-REVIEW.md`](evidence/issue19-dual-top-20261003/FINAL-REVIEW.md)；[`simulation-evidence.json`](evidence/issue19-dual-top-20261003/simulation-evidence.json)。
- 结果索引：[`verification-results.json`](evidence/issue19-dual-top-20261003/verification-results.json)。
- 正常原生日志：[`run.log`](evidence/issue19-dual-top-20261003/logs/normal_checked_wavefixed/run.txt)；同目录保存编译/展开原生日志；波形仅保留在 C 机。
- 四个负向日志位于已发布证据目录 `docs/evidence/issue19-dual-top-20261003/logs/` 下的 `NEG_*_wavefixed` 目录；交审范围见 [REVIEW-ENTRY.md](evidence/issue19-dual-top-20261003/REVIEW-ENTRY.md)。

## 复现组合仿真

GUI 方法：将上述两个 RTL 加入 Design Sources，将 TB 加入 Simulation Sources，Simulation Top 选择 `tb_servo_dual_test_top`，启动 Behavioral Simulation，然后执行 `run all`。正常结束必须看到 `TEST_PASS`。

CLI 方法：从 Vivado 2025.2 环境命令提示符进入仓库根目录，确认 `xvlog`、`xelab`、`xsim` 在 PATH 中。在 `codex_out` 下选择尚不存在的新目录，以下示例用 `servo-dual-reproduce-01`；若已存在则换名，不覆盖旧证据。每条命令成功后再执行下一条：

```bat
mkdir codex_out\servo-dual-reproduce-01
cd codex_out\servo-dual-reproduce-01
xvlog --sv ../../project/rtl/servo/motor_drive.v ../../project/rtl/servo/servo_dual_test_top.v ../../simulation/tb/servo/tb_servo_dual_test_top.sv --log compile.log
xelab work.tb_servo_dual_test_top --snapshot servo_top --debug typical --log elaborate.log
xsim servo_top --runall --sv_seed 19 --onerror quit --log run.log
```

输出为 `compile.log`、`elaborate.log`、`run.log` 及当前目录的 XSim 数据库。核对 `run.log` 中的 `TEST_PASS cases=6` 和 `checks=54000306`；若出现 `CHECKER_FAIL` 或 `ASSERTION_FAIL`，正常测试即失败。复现负向检查时，应另选新目录，并在最后一条命令添加 `--testplusarg NEG_WIDTH`（或 `NEG_PERIOD`、`NEG_STARTUP`、`NEG_VALID`），期望得到相应断言失败。
