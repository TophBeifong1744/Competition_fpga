# SoundSight 当前工作包台账

更新：2026-09-07。本地状态台账，尚未同步为 GitHub Issues。负责人负责交付，复核人签署通过；Codex 文件完成或测试通过不替代人工验收。日期是原计划，不因整理而自动顺延。

拓芙的 Git 交付路径为任务短分支 → `codex/toph-development` → `main`，自动建分支、提交、推送和合并的条件见[GitHub 工作规则](git-workflow.md)。该授权不把“待复核”自动改成“已通过”，也不绕过 M0 或后续实现准入。

## V1：9 月 10 日 M0 前

| ID | 任务 | 负责人 / 复核 | 原计划截止 | 当前状态与剩余交付 |
|---|---|---|---|---|
| WP-A0 | 基线与文档入口 | 拓芙 / hsc119 | 09-06 23:59 | 待复核：最新目录、证据状态与备份已整理 |
| WP-A1 | 实物板卡证据 | 拓芙 / hsc119 | 09-07 22:00 | 进行中：照片、用户确认和旧工程交叉核对已明确 `xc7z020clg400-2`；核心板背面、Codec 等仍待补 |
| WP-C1 | 库存与模块身份 | hsc119 / BryanZheng802 | 09-07 22:00 | 待复核：已选麦克风路线；实物型号、数量、照片、数据手册、电平和时钟清单已交齐 |
| WP-B1 | 固定演示场景 | BryanZheng802 / 拓芙 | 09-08 20:00 | 待复核：[项目计划](project-plan.md)中场景已填写，仍需实地标定和实验元数据 |
| WP-C2 | 既定 IM73D122V01/PDM 模块核验 | hsc119 / BryanZheng802 | 09-09 18:00 | 进行中：不重选麦克风；核验实际模块身份/引脚、供电、电平、同步、边沿、线数和带宽 |
| WP-A2 | 时钟、电平和 PL 引脚冻结 | 拓芙 / hsc119 | 09-10 12:00 | 阻塞：每路连接器、pin/Bank、IOSTANDARD、方向、冲突与证据未齐，不生成假定 XDC |
| WP-A3 | 四路样本合同 | 拓芙 / hsc119 | 09-10 15:00 | 进行中：[合同](../hardware/four-channel-sample-interface-contract.md)待填项、通道顺序、格式、计数/错误/CDC 须冻结 |
| WP-B2 | 既有理想阵列模型复核 | BryanZheng802 / 拓芙 | 09-10 15:00 | 待复核：仅审已有四麦 35/40/50 mm 证据，不新增四麦模拟或四/六麦对比 |
| WP-C3 | 夹具与布线 | hsc119 / BryanZheng802 | 09-10 15:00 | 进行中：指南已形成；坐标/公差/固定方式与实物安装仍待验证，V2 不提前采购 |
| WP-A4 | Vivado/仿真可复现入口 | 拓芙 / hsc119 | 09-10 18:00 | 进行中：拓芙回传的 [2025.2/器件查询](../hardware/evidence/vivado-2025-2-environment-check.md)通过；下一步独立 M0 空工程。接口、完整重建、自检与实板准入仍未通过 |
| WP-G0 | M0 评审 | 拓芙 / 全员 | 09-10 20:00 | 未开始：逐项审证据，不通过则暂停下游正式 RTL |

PYNQ 实板镜像/DDR/SD/网络/Overlay/Vivado 兼容和 DMA 路径，由拓芙主责、hsc119 复核，纳入 WP-A4/WP-G0；不满足时评审 Vitis/PetaLinux 控制层替换，AXI4-Lite/DMA/中断合同不变。

## 两个通用 Skill

| ID | 任务 | 负责人 / 复核 | 原计划截止 | 当前状态 |
|---|---|---|---|---|
| WP-S1 / SKL-001 | 工程协作 Skill | 拓芙 / hsc119 | 09-14 20:00 | 待复核：v0、静态检查及 M0 门禁前向测试已形成；待真实工作包应用复核 |
| WP-S2 / SKL-002 | PYNQ 通用 Skill | hsc119 / 拓芙 | 09-16 20:00 | 待复核：v0 与 5/5 离线用例；PYNQ 未准入，不宣称 DMA 板测通过 |

BryanZheng802 提供 golden、指标与失败案例；制作流程与模块交接见[团队分工](team-tasks.md)。两个 Skill 的三维适配当前只修指南，不改驱动或 Skill 本体。

## V2：六麦软件预研与后续门禁

无新的硬件交付日期；人力/真实输入确认后重新排期。已撤回四通道复用前提下的 3～5 周估算。

| ID | 任务与输出 | 负责人 / 复核 | 状态 / 完成定义 |
|---|---|---|---|
| 3D-P1 | [原理与评审指南](three-dimensional-doa-principles-guide.md) | BryanZheng802 / 拓芙 | 待复核：只六麦；方向符号、指标分母、坏通道、golden 和失败边界 |
| 3D-P2 | [工程指南](three-dimensional-doa-engineering-guide.md) | 拓芙 / hsc119 | 待复核：六路采集准入、版本兼容、调度/存储预算、回退 |
| 3D-P3 | [阵列与标定指南](../hardware/three-dimensional-array-guide.md) | hsc119 / BryanZheng802 | 待复核：原麦克风、上下声孔/结构/公差、供电时钟与数据线 |
| 3D-P4 | [工程 Skill 适配指南](three-dimensional-doa-workflow-skill-guide.md) | 拓芙 / hsc119 | 待复核：通用门禁、证据分级、失败与回退，非专用新 Skill |
| 3D-P5 | [PYNQ Skill 适配指南](three-dimensional-doa-pynq-skill-guide.md) | hsc119 / 拓芙 | 待复核：四/六通道元数据与离线/实板区分，不改现有驱动 |
| SIM6-001 | [首轮六麦浮点与合成音频](six-mic-acoustic-software-review.md) | BryanZheng802 / 拓芙 | 软件检查完成、待人工科学复核：2700 帧、21 自检、15 产物复现；3D-G0 未通过 |
| SIM6-002 | 目标锁定与错误峰/低 SNR 改进实验 | BryanZheng802 / 拓芙 | 未开始：先冻结目标身份与重捕获规则，再同输入比较；同时报精度/有效率/错误率，不自动批准 SRP-PHAT |
| SIM6-003 | 自然语音、房间实录/RIR、装配误差与遮挡数据 | hsc119 / BryanZheng802 | 待输入：记录来源、授权、标定与条件；两条人工反射不算真实房间验证 |
| ENG6-001 | 六路周期/缓存/定点与资源预算 | 拓芙 / hsc119 | 未完成：6 FFT/15 IFFT 计数不是实现预算；3D-GA 前须闭合采集/DMA/PL 预算 |
| REL6-001 | [独立报告材料包](../deliverables/six-mic-acoustic-review-v1/README.md) | 拓芙 / hsc119 | 待复核：源码、报告、重要结果、配置/依赖/哈希和独立复现齐全；非完整比赛提交包 |

五个领域 Codex 任务统一 GPT-6 Astra/high，负责各自指南；人类负责人不变。V1 四麦二维先验收，六麦硬件须经 V1 保底、3D-G0、3D-GA 后另行授权。三维是 az/el/单位向量，不含测距/离地高度；转台仍后置。

## 执行与交接

2026-09-08 新规：三人的任务成果集中到 `task-packages/<工作包ID>/`，经指定复核人明确确认通过后，由复核人合入总工程；作者不得自审自合。目录、批准版本和合入记录要求见[任务包交付与复核规则](task-package-handoff.md)。

每项交付必须列输入依赖、文件、复现方法、预期/实际结果、失败条件、版本和复核结论；计划/浮点/定点/仿真/时序/实板分别登记。完整模块 ID 与依赖见[团队任务分解](team-tasks.md)，赛题缺项见[验收台账](competition-acceptance.md)。三人每周小时数、固定时段与器件保管/借用实际进度仍需人类补齐。

旧日期版已移入[清理前备份](../archive/2026-09-07-before-materials-cleanup/README-ARCHIVE.md)，不得继续在旧表派工。
