# PS 软件

执行规则更新（2026-09-08）：成员间仅 [H1 最小接口 → H2 首批诊断数据 → H3 算法包集成评审](../docs/three-handoff-workflow.md)。暂定接口可版本化用于工程框架、读取器、逻辑/TB和离线算法开发；短实录不等一小时长稳，但只作诊断。A/B 负责技术开发和判断，C 只[按操作单](../docs/member-c-operation-sheet.md)执行。以下冻结/阶段门用于对应接板、正式集成或验收声明，不禁止独立离线工作；完整包交付而非逐小动作审批。

PS 端只负责非实时控制面：AXI 寄存器配置、运行状态、UI/通信、实验日志和受控数据抓取。PYNQ 已确定为首选开发、验证和演示后端；实时 GCC-PHAT、TDOA/DOA 和波束形成不得移到 PS 或 Python 作为最终比赛实现。

M0 仍需核实实际板卡的 PYNQ 镜像或板级支持、DDR、SD、网络、Overlay 加载和 Vivado 版本兼容性。若 PYNQ 无法可靠落地，可切换到 Vitis 裸机或 PetaLinux；AXI4-Lite 寄存器、AXI DMA 数据格式和中断语义不得随 Python 实现改变。

团队 Vivado 基线已固定为 `2025.2`，但 PYNQ 板级支持、Overlay 加载和 DMA 尚未完成实板验证。PS 端发布物必须记录与其配套的 `.bit/.hwh` 构建标识、Vivado 版本输出、Python/PYNQ 环境和依赖版本，不能把“版本已决定”写成“系统已复现”。

寄存器驱动必须检查硬件与接口版本号，并把采样率、阵列坐标、声速和阈值配置作为一次原子更新提交给 PL。DMA 驱动必须验证块序号、`sample_id/frame_id`、超时、溢出和恢复，且 Python 异常不得反压实时采集链。

底层 Overlay、寄存器和 DMA 访问应封装为可测试的 Python 模块；Notebook 只作为教学和实验入口，不保存唯一的驱动实现。详细要求见 [PYNQ 集成与控制面指南](../docs/pynq-integration-guide.md)。

SKL-002 `pynq-overlay-dma-validation` 交付后用于复核 Overlay、寄存器、DMA、缓存、超时、loopback、golden 和性能，不成为运行时依赖，也不替代 SoundSight 自身板测。PYNQ 准入前只接收其离线验证结果；实板结论必须在当前板卡上重新执行。AI 协作记录只保存用户可见交互、人工纠正和验证结果，不保存隐藏思维链。
