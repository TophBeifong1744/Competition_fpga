# C 单路舵机 PWM 首次独立复核

2026-09-17。作者 C；独立复核：A 主流程 / Codex。**PASS，限定模块功能与 PowerShell 7 / XSim 2025.2 仿真入口**。

- 固定候选 `b1d51d44aa2c055a145b832b7c272fd33b7d0395`，分支 `codex/servo-pwm-driver`。
- 规则：main `02b578c730c539e7fb45e11386567f28ffe7ab71` 的 AGENTS、team-workflow、review-brief；首次完整审本包，不审全仓。
- [作者入口](../../../task-packages/PKG-SERVO-PWM/README.md)及证据原样保存。原实现 `9b74815ba838ef1132e64105f8a228dcef164b7a`，上一交付 `34e9c9c961bd8501df2c540a09d6a894dfcae9c9`；RTL/TB/工程 Tcl 未变。
- 隔离工作树 `E:/ss-servo-review-0917` 执行前 HEAD 固定且干净，没有修改作者源码；故障副本放本轮证据目录。

## 批准边界

批准角度换算、限幅/舍入、20 ms 周期、周期边界更新、复位及完整重启、TB 判据和上述环境运行入口。可按原内容接入 `rtl/servo/motor_drive.v`、`tb/servo/tb_motor_drive.v`，搬迁后须实际验证新入口。

不批准机械到位/位置反馈、实际舵机电气兼容、摄像头驱动、双轴联动、综合实现/时序、板测、2025.2 工程创建/BD 或 one 接入。用户确认的 0～360°是命令映射，不是机械效果；本次不是阶段/整机验收。

## 本次实际运行

工具 XSim 2025.2，SW Build 6299465，`F:/AMD/2025.2/Vivado/bin`。完整命令、退出码、stdout/stderr、哈希及失败历史见[证据根](../../../results/servo-review/b1d51d4/)，由其中 `run_review.py` 执行记录。

| 检查 | 实际结果及目录 |
| --- | --- |
| 作者 TB：100 MHz、1 MHz | 各 39 项 PASS，同组两个配置，不算 78 个独立用例；`author-run-02` |
| 独立端口逐拍 oracle：1 MHz、3 MHz | 每配置全部 512 个编码、520 个启动/周期事件；分别 10,343,021、31,029,021 次逐拍比较 PASS；`independent-run-02` |
| 独立时序 | 首个有效时钟启动、完整周期、高/低阶段及边界前多次更新、最新目标生效、异步复位及完整重启；不读取 DUT 内部计数器 |
| 1.5 MHz 非法参数 | 编译展开后仿真合同拒绝，外层退出 1；`author-run-02/author-1500000.*` |
| 已有输出目录 | 调工具前拒绝，退出 1，旧日志哈希不变；`author-run-02/directory-protection.json` |
| 脉宽 +1 μs 故障副本 | 编译展开成功后 pulse width 检出，退出 1；`fault-run-01/width.*` |
| 无 PWM 故障副本 | 编译展开成功，400 ms watchdog 检出，退出 1；`fault-run-01/no-output.*` |
| 语法错误副本 | xvlog 失败正确上抛，退出 1；只证明编译失败传播；`fault-run-01/compile-error.*` |

独立 oracle 使用实数映射后取整，与 RTL 整数乘加除不同；1 MHz 检查最小分频，3 MHz 检查非二次幂分频。逐拍四态不等检查 X/Z 输出；不承诺合同外 X/Z 输入安全动作。静态检查中间位宽、分频/周期容量及参数范围未发现截断或溢出问题。

## 环境与复核自身失败历史

- `author-run-01`：Windows PowerShell 5.1 误解析无 BOM 中文 UTF-8 脚本，未进入仿真；项目既定 PowerShell 7 下通过。独立使用明确执行 `pwsh`；**未批准 5.1 兼容性**，非 RTL 缺陷，不要求作者因此返工。
- `independent-run-01`：复核新 TB 的超大单个延时在工具中于 0 时刻触发 watchdog。首次源码 `tb_initial_watchdog.sv` 与日志保留；仅修改复核 TB 为 11 次 1 s 后在全新目录重跑通过，作者源码未动。
- 本机 `vivado -version` 打印准确版本但退出 1，照实保存；实际正常 xvlog/xelab/xsim 均退出 0，不混淆版本查询与功能运行。

## 复用 / 未测 / 扩大范围

2018.3 作者历史日志仅作来源参考，未重跑、未当独立批准；2025.2 作者日志也不替代本轮执行。工程创建 Tcl 只读核查路径、拒绝覆盖与文件集，未运行。综合、系统 CDC、资源时序、实板、机械、摄像头及整机未测。

扩大检查限于原 TB 未穷尽的角度、首拍有效性、分频边界及脚本故障传播，没有扩到声学主线。未发现阻断本次限定范围的缺陷。

## 收尾

活动源码与批准候选保持相同内容，原包是来源快照，不是第二处开发入口；后续只改活动目录。活动入口、材料清单及主线核对见[发布记录](../../maintenance/servo-publication-2026-09-17.md)。旧机械路线退役与新分工不反写历史证据。
