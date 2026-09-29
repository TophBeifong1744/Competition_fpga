# #19 舵机 v2 定向仿真

活动 DUT 为 `project/rtl/servo/motor_drive.v`。此目录的两个定向 TB 只观察外部 PWM 引脚：单轴检查有效命令在周期边界前一拍、同拍、后一拍，复位释放同拍、复位期间及持续 valid；双轴以两个独立实例检查各轴独立命令、同时命令、保持、共同复位。`canary` 在新输出目录复制并故意破坏 DUT 的命令锁存，只证明检查器会拒绝该故障；不改活动 RTL。

在仓库根以 PowerShell 7 和 Vivado/XSim 2025.2 执行。每次使用**不存在**的新输出目录；本机工具目录不同则传 `-VivadoBin`。参数 `-Mode single` 支持 220/360°及 1/100 MHz；`-Mode dual` 同时实例化 360/180 水平轴与 220/130 垂直轴。

```powershell
pwsh -File ./simulation/tb/servo/run_v2_targeted.ps1 -Mode single -ClockHz 1000000 -MaxAngleDeg 360 -OutputDirectory ./codex_out/servo-v2-single-1m-360-new
pwsh -File ./simulation/tb/servo/run_v2_targeted.ps1 -Mode single -ClockHz 1000000 -MaxAngleDeg 220 -OutputDirectory ./codex_out/servo-v2-single-1m-220-new
pwsh -File ./simulation/tb/servo/run_v2_targeted.ps1 -Mode single -ClockHz 100000000 -MaxAngleDeg 360 -OutputDirectory ./codex_out/servo-v2-single-100m-360-new
pwsh -File ./simulation/tb/servo/run_v2_targeted.ps1 -Mode single -ClockHz 100000000 -MaxAngleDeg 220 -OutputDirectory ./codex_out/servo-v2-single-100m-220-new
pwsh -File ./simulation/tb/servo/run_v2_targeted.ps1 -Mode dual -ClockHz 1000000 -OutputDirectory ./codex_out/servo-v2-dual-1m-new
pwsh -File ./simulation/tb/servo/run_v2_targeted.ps1 -Mode dual -ClockHz 100000000 -OutputDirectory ./codex_out/servo-v2-dual-100m-new
pwsh -File ./simulation/tb/servo/run_v2_targeted.ps1 -Mode canary -ClockHz 1000000 -MaxAngleDeg 360 -OutputDirectory ./codex_out/servo-v2-canary-new
```

正常配置预期 `result.json` 为 `PASS_DIRECTED_SIM_AUTHOR`：单轴每配置 25 项，双轴每配置 41 项。canary 预期 `EXPECTED_FAIL_CHECKER`，`simulation.log` 中有精确的 `Fatal: FAIL valid B-1 width`，且没有 PASS 标记。XSim 2025.2 的 `$fatal` 可能仍返回进程码 0，因此脚本核查日志内容。每个输出目录保留 `xvlog.txt`、`xelab.txt`、`xsim.stdout.txt`、`simulation.log`、`result.json`；其余编译缓存为派生物。

下一步由 A 对准确源 SHA 和 TB 判据作非作者复核。随后在明确舵机手册、供电及板上 PWM 引脚后，先测引脚脉冲，再测机械到位；这里的仿真不证明板级引脚、电气安全、真实角度或停止状态。对应执行证据见 `docs/evidence/issue19-servo-v2-20260928/`。
