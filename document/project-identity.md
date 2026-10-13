# SoundSight 工程身份

2026-09-23治理迁移之后，Issue #26 另形成[仓库实体迁移候选](layout-migration.md)，活动路径以配置与移动清单为准；没有重建、搬迁或改动实际 one 工程。

- 仓库：TophBeifong1744/Competition_fpga；集成基线 main。
- 历史采集工程身份（非当前live-loop报告的part证明）：已有板卡：正点原子领航者 ATK-DF7010P_7020P，底板 V3.9；受控工程 part 为 xc7z020clg400-2，Vivado 2025.2。
- V1：现有 IM73D122V01/PDM 四路、C转接板、四个同源CLOCK及既定DATA映射；固定阵列二维方向。六麦三维仍为后续研究，不增加本轮采集通道。
- PL承担确定性采集/DSP；PS负责配置、状态、日志/导出和低速控制。现有主线 Vitis standalone、simple S2MM-only；PYNQ仍未实板准入，不虚构MM2S/身份寄存器。
- 原生工程在A机仓库外的 one/one.xpr，当前重建依据见[现有入口](../task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/current_build/README.md)。绝对本机路径沿旧受控记录或私有配置取用；配置中的 project_entry=null 表示仓库内没有已核定正式厂商入口，不是允许随便新建。
- simulation/modules.json 是现有模块仿真清单；它是JSON，不伪装为外层CLI支持的一行一文件清单。
- layout为existing映射；IP/BD/约束在外部原生工程，不把配置空数组解读为设计没有这些依赖。真实 source view/重建适配未验证，adapter_status=UNVERIFIED。

## 工程操作权限

工程授权以当前[AGENTS.md](../AGENTS.md)为准，9/15的旧修改限制已由2026-10-10更新取代。Codex可在明确工作包授权内修改项目自有RTL、BD脚本/连线描述、XDC、IP生成脚本及Vitis源码/配置并做必要自测；关键架构、接口、精度、时钟、资源、器件/IP/版本及方案取舍由人选择，厂商产物用正式工具生成。

首次可运行、综合/实现、集成/上板按现行约定由人操作Vivado/Vitis并保存原始结果；下载、复位、接线和执行器动作仍由现场获授权人员执行。总工程维护权不永久固定；当批组合/构建/现场责任按原Issue接续。A使用已收工程计算副本，C使用现场工程，不再重复建同功能工程。共享checkout/EDA输出只有一名写入方，实物操作按实际板卡占用安排，不因流程文档更新推定任何新硬件动作已获授权或完成。

板卡占用在对应Issue留简短“操作者/版本/时间/释放”记录；这不是跨机器原子锁。电源、针脚或运动安全冲突即时停止相关动作；精细非阻塞事项仍只在[暂缓风险](deferred-acquisition-risks.md)登记。


## 2026-10-13活动组合

真实入口与作用见team-workflow.yaml的actual_engineering_entries。A live-loop Tcl实际part为xc7z020clg400-1；历史采集记录为-2，不能混用报告。由现场责任人在下一次加载前核实际板卡/器件及匹配配置，本次不猜测兼容。A/B新三个源已替换；C最新a3cc8415共享选字尚未在A本机源中。最新综合异常终止，细节见current-status.md。比赛PS要求PYNQ只适用于此项目，既有standalone作为诊断历史保留。
