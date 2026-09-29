# XSim 模块诊断入口

本目录是现有 XSim/PowerShell 诊断流程，不是正式 ModelSim/Questa 桌面模板；没有已核定的 run.bat 或 .xpr，工程 adapter 仍为 UNVERIFIED。目录迁移本身不签发新的功能批准。

仓库根执行，环境为 Vivado/XSim 2025.2 与 PowerShell 7；`<Vivado-bin>` 替换为本机确认的 bin 目录：

```powershell
pwsh -File ./simulation/run_regression.ps1 -VivadoBin '<Vivado-bin>' -OutputDirectory './codex_out/regression-new'
pwsh -File ./simulation/run_servo.ps1 -VivadoBin '<Vivado-bin>' -OutputDirectory './codex_out/servo-new' -ClockHz 1000000 -MaxAngleDeg 360
```

[modules.json](modules.json)列出 7 组及来源身份。统一回归校验活动源码哈希，分别编译 Verilog/SystemVerilog；预期 7 行 PASS 与 result.json 中的 PASS_MODULE_REGRESSION。错误、缺标记或非零退出均失败。输出目录必须尚不存在；统一回归仅接受仓库 codex_out 下的新目录，拒绝已有目录和 reparse 输出祖先。历史批准范围不因这些字符串扩大。

唯一活动输入在[RTL](../project/rtl/README.md)与[TB](tb/README.md)。#19 候选分支的舵机活动源现为 v2，包含 `angle_valid_i` 与 `RESET_ANGLE_DEG`，默认360°、可设220°；`run_servo.ps1` 按两档检查 61/69 项作者 TB 标记。针对 A 的定向入口见[servo TB 说明](tb/servo/README.md)。b1d51d4 批准仅覆盖旧快照，当前 v2 待 A 独立复核；仿真不能推断机械到位。

获准后由用户在已打开的 Vivado 工程执行 `source /实际路径/project/add_sources.tcl`。它只加入三件基础设计源，不选系统顶层、不接 BD、不修改约束，本次未执行。实际 one 工程不随仓库路径自动修改。

Skill 示例迁移后的入口是[仓库适配器](../scripts/run_module_skill_examples.py)：

```text
python -B scripts/run_module_skill_examples.py --case all --vivado-bin <Vivado-bin> --output codex_out/skill-examples-new
```

适配器只在新输出目录写派生 case；PCM4 DUT 指向 project/rtl，合同/TB 及 run_xsim.py 指向原 Skill，minimum_checks 和检查逻辑不变。--case 可选 pcm4、elastic、all；--prepare-only 仅解析并生成 case，不运行工具。这里只复跑正例入口，旧 run_examples.py 的变异演示依旧按原提交复现。

历史记录：[9月10日六组收尾](../deliverables/phase-2026-09-10/CLOSEOUT.md)、[9月17日舵机限定复核](../docs/reviews/servo-b1d51d4/REVIEW.md)。旧命令/结果以其准确旧 SHA 为准；新路径验证见[迁移说明](../document/layout-migration.md)，后续按[阶段收尾规则](../document/phase-closeout.md)交付。
