# SoundSight 工程身份

2026-09-23迁移仅改变协作配置、计划和入口；没有重建、搬迁或改动实际 one 工程。

- 仓库：TophBeifong1744/Competition_fpga；集成基线 main。
- 已有板卡：正点原子领航者 ATK-DF7010P_7020P，底板 V3.9；受控工程 part 为 xc7z020clg400-2，Vivado 2025.2。
- V1：现有 IM73D122V01/PDM 四路、C转接板、四个同源CLOCK及既定DATA映射；固定阵列二维方向。六麦三维仍为后续研究，不增加本轮采集通道。
- PL承担确定性采集/DSP；PS负责配置、状态、日志/导出和低速控制。现有主线 Vitis standalone、simple S2MM-only；PYNQ仍未实板准入，不虚构MM2S/身份寄存器。
- 原生工程在A机仓库外的 one/one.xpr，当前重建依据见[现有入口](../task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/current_build/README.md)。绝对本机路径沿旧受控记录或私有配置取用；配置中的 project_entry=null 表示仓库内没有已核定正式厂商入口，不是允许随便新建。
- sim/modules.json 是现有模块仿真清单；它是JSON，不伪装为外层CLI支持的一行一文件清单。
- layout为existing映射；IP/BD/约束在外部原生工程，不把配置空数组解读为设计没有这些依赖。真实 source view/重建适配未验证，adapter_status=UNVERIFIED。

## 工程操作权限

A机实际Vivado/Vitis遵守9/15约定：先说明目标、范围、预期，由拓芙选择原工程/副本并执行工程修改、综合实现、下载运行；Codex负责TB、仿真、诊断和结果核对。此次迁移不授权这些硬件动作。B/C在自己工作包、自己工程中依其明确授权工作；共享one与板卡只有一个操作人，不以C平等分工推定共用工程已放行。

板卡占用在对应Issue留简短“操作者/版本/时间/释放”记录；这不是跨机器原子锁。电源、针脚或运动安全冲突即时停止相关动作；精细非阻塞事项仍只在[暂缓风险](deferred-acquisition-risks.md)登记。
