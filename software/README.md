# PS 软件

2026-10-13 平台补件：已从历史 XSA 提取 PS7/HWH/DDR/MIO/时钟复位/GP/HP/DMA 配置和原件身份，见[平台与PS配置材料](../docs/evidence/issue18-pynq-materials-20261013/ps-platform/README.md)。旧方向测试已确认在电脑 Python 运行，声音采集在 Vitis；PYNQ 镜像与当前 Overlay 仍未验证。

2026-10-13：本项目比赛交付须用 PYNQ on Zynq，旧 standalone 保留诊断来源。C 的[七组接入材料](../docs/evidence/issue18-pynq-materials-20261013/README.md)与[控制合同摘要](../docs/evidence/issue18-pynq-materials-20261013/control-handoff.md)供 B 沿原 #18 接续；当前现场仍经 JTAG 加载，镜像/CPU桥/匹配Overlay/真实PYNQ运行尚未验证。B 原方案的软件落点为 `software/pynq/soundsight_ps/`；本批只整理材料，尚未创建驱动树或安装环境。下文备用后端说明不授权自动切换比赛平台。

2026-09-23：本目录从 ps/ 迁入说明文档；没有迁入或改写实际固件。当前主线是 Vitis standalone、simple S2MM-only，PYNQ 未实板准入；下文保留 PYNQ 后端规划，不能读作已接通。A/B/C 按 Issue 同等承担工程和合格非作者复核，保留 [H1/H2/H3](../document/three-handoff-workflow.md)，当前事实见[工程身份](../document/project-identity.md)。

PS 端只负责非实时控制面：AXI 寄存器配置、运行状态、UI/通信、实验日志和受控数据抓取。PYNQ 已确定为首选开发、验证和演示后端；实时 GCC-PHAT、TDOA/DOA 和波束形成不得移到 PS 或 Python 作为最终比赛实现。

M0 仍需核实实际板卡的 PYNQ 镜像或板级支持、DDR、SD、网络、Overlay 加载和 Vivado 版本兼容性。若 PYNQ 无法可靠落地，可切换到 Vitis 裸机或 PetaLinux；AXI4-Lite 寄存器、AXI DMA 数据格式和中断语义不得随 Python 实现改变。

团队 Vivado 基线已固定为 `2025.2`，但 PYNQ 板级支持、Overlay 加载和 DMA 尚未完成实板验证。PS 端发布物必须记录与其配套的 `.bit/.hwh` 构建标识、Vivado 版本输出、Python/PYNQ 环境和依赖版本，不能把“版本已决定”写成“系统已复现”。

寄存器驱动必须检查硬件与接口版本号，并把采样率、阵列坐标、声速和阈值配置作为一次原子更新提交给 PL。DMA 驱动必须验证块序号、`sample_id/frame_id`、超时、溢出和恢复，且 Python 异常不得反压实时采集链。

底层 Overlay、寄存器和 DMA 访问应封装为可测试的 Python 模块；Notebook 只作为教学和实验入口，不保存唯一的驱动实现。详细要求见 [PYNQ 集成与控制面指南](../document/pynq-integration-guide.md)。

SKL-002 `pynq-overlay-dma-validation` 交付后用于复核 Overlay、寄存器、DMA、缓存、超时、loopback、golden 和性能，不成为运行时依赖，也不替代 SoundSight 自身板测。PYNQ 准入前只接收其离线验证结果；实板结论必须在当前板卡上重新执行。AI 协作记录只保存用户可见交互、人工纠正和验证结果，不保存隐藏思维链。
