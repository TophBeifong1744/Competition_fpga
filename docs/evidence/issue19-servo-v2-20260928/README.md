# #19 v2 定向仿真与活动入口证据（2026-09-28）

范围：C 作者侧模块仿真与文档，交 A 做准确候选的独立复核；**不是 A 批准、综合时序或板测 PASS**。工作树基线 `a1cbaa48a2c09719f14998b98a8000cc343d1adf`，分支 `codex/19-servo-v2-evidence`。包内 v2 候选身份 `d63544d6c48b9cfaaf2c629536de2647b8762f84`；活动 `project/rtl/servo/motor_drive.v` 与包内 RTL 字节相同，SHA256 `23f438b7c5d6ac491f6532c447413edad48f88d0bc79325d90ace8e3981f2214`。活动 `simulation/tb/servo/tb_motor_drive.v` 与包内 TB 字节相同，SHA256 `fb17b0e6328dc82ad06ee075c690d7d359ef70b9aa94e8d5247bf4f0930ebf33`。工具 Vivado/XSim 2025.2，执行 bin `C:\AMDDesignTools\2025.2\Vivado\bin`，PowerShell 7。

## v1.1 与 v2 合同变化

| 项目 | v1.1 / 旧批准 `b1d51d4` | v2 当前候选 |
|---|---|---|
| 命令 | 无 valid，角度总线在周期边界直接采样 | 同域 `angle_valid_i` 为高的时钟沿锁存；周期边界使用已锁存的最新目标，边界同拍命令在下一周期生效 |
| 复位释放 | 角度总线决定后续目标 | 先输出 `RESET_ANGLE_DEG`，持续保持直到接受有效命令；复位期间 valid 忽略 |
| 量程 | 固定 0～360° | `MAX_ANGLE_DEG` 参数化，水平 360/回位180，垂直 220/回位130，超限饱和 |
| 输出 | 20 ms 周期、500～2500 μs 映射 | 保持 20 ms / 500～2500 μs 名义映射，按所选满量程缩放；真实舵机脉宽仍须核对厂家资料 |
| 集成 | 单路模块 | 仍是单路模块；双轴由上层实例化两次，**没有产品双轴封装**；旧调用者必须补 valid 连接 |

旧 `b1d51d4` 的独立批准仅覆盖当时接口和源；本证据不继承旧批准。复核重点是 v2 边界语义和复位/valid 交互，而不是重复旧版全角度穷举。

## 执行结果

运行入口和完整命令见 [定向 TB 说明](../../../simulation/tb/servo/README.md)；`run_servo.ps1` 与 `run_regression.ps1` 的调用见 [模块入口](../../../simulation/README.md)。每个下列目录包含结果 JSON 与原生编译/展开/仿真文本日志；`codex_out/issue19-v2-targeted-20260928/` 的完整派生缓存留在执行工作树，索引目录只存必要日志。

| 证据目录 | 配置 | 结果 |
|---|---|---|
| `single-1m-360-r2` | 单轴 1 MHz / 360° | 25 项 PASS |
| `single-1m-220-r1` | 单轴 1 MHz / 220° | 25 项 PASS |
| `single-100m-360-r1` | 单轴 100 MHz / 360° | 25 项 PASS |
| `single-100m-220-r1` | 单轴 100 MHz / 220° | 25 项 PASS |
| `dual-1m-r1` | 双实例 1 MHz | 41 项 PASS |
| `dual-100m-r1` | 双实例 100 MHz | 41 项 PASS |
| `canary-1m-360-r2` | 临时副本阻断 valid 锁存 | **预期失败**，检出 `valid B-1 width`；XSim 的 `$fatal` 进程码为 0，脚本按精确日志签定 |
| `active-entry-1m-360` / `active-entry-1m-220` | 活动 `run_servo.ps1`，1 MHz | 61 / 69 项 PASS |
| `unified-regression-r2` | 活动模块 7 组统一回归 | 7/7 PASS；`modules.json` SHA256 `75499E05270519E29847258EDC9523E4A556E2A1A9647558CF899826233D64EE` |

初次 `single-1m-360` 编译失败是定向运行脚本漏用 `xvlog -sv`；补正后在新目录 `-r2` 通过。初次 `canary-1m-360-r1` 是检查脚本误以为 `$fatal` 必令 XSim 非零退出；修正判据后 `-r2` 检出预期故障。两次失败均保留 `result.json` 和相关日志，不列为产品 RTL 缺陷。

## A 评审与实物缺口

E01：核对包内 v2 到活动路径的准确 SHA、`simulation/modules.json` 的新候选身份、旧批准边界；评审源版本固定后再批准。E02：独立检查测试输入相位和固定输出 PWM 期望，尤其 B−1/B/B+1、复位释放首拍、复位期间 valid、持续 valid 最新值；若独立复核发现反例，保存最小波形。E03：核对 [实物与板测记录](../../../hardware/evidence/servo-c-20260928/README.md)；当前只有商品图和用户口述，缺准确厂家手册、板上双路引脚及原生到位读数。A 的 Vivado/Vitis 工程修改、构建、下载由 A 在其实际工程操作。本轮未执行综合、静态时序、板级波形或机构效果验证。
