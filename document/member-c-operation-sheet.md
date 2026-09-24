# 成员C工程任务入口（原操作单入口保留兼容）

2026-09-23用户明确：C可以承担与A/B类似的工作。本文不再限制C只做简单操作；方案设计、RTL/软件、调试、实验和合格独立复核均按同一规则承担。

C=hsc119，主责：转台和摄像头的全部驱动、方案落实、最终效果；继续承担新八段采录全流程与现场系统测试。

- [#15 正确素材新录音](https://github.com/TophBeifong1744/Competition_fpga/issues/15)：9/22错素材已归档，先核对正确WAV/入口，首段检查后完成八段；不要求拓芙代录/整理。B独立诊断，A接收工程身份。
- [#19 舵机/转台](https://github.com/TophBeifong1744/Competition_fpga/issues/19)：最新接口重新固定候选，旧b1d51d4的模块批准不能覆盖d63544d；模块/机械到位/双轴效果分开验证。
- [#20 摄像头](https://github.com/TophBeifong1744/Competition_fpga/issues/20)：自己完成器件依据、接口/驱动、图像和载荷效果，不等声学算法才能开工。
- [#22 独立复用SKL-002](https://github.com/TophBeifong1744/Competition_fpga/issues/22)：核对合同、独立正负例和导出使用；必要DMA/golden风险由未参与实现的B协助，能力不足如实转配，不代签。

每次完整工作包交准确SHA与原始证据，非作者复核；自检不自批。现场操作仍遵守电气/运动安全和设备占用，采购/刷板不因派工自动获授权。时间与完成定义以Issue和[日历](project-plan.md)为准，不再要求专属日更表。
