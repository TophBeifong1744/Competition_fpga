# B 工程收口 R1/R2 增量复核：限定通过

2026-09-21，A独立复核。**R1/R2关闭，准确实现ad30bda获限定离线软件材料批准。** 原报告NEEDS_FIX保留，不追改旧结论；原数值/预算已通过部分复用，没有重跑旧FFT、声学、E01～03或PSB-B-01～03。

## 版本与申请范围

- 准确审核实现：`ad30bda694abc946db045192385ebdf1b8e1a956`。
- 原审核实现：`d3d2a3d4e78932830bf12bd84c0517b0a2092872`；旧文档头：`dbd7ab5b35c75dfe9779a0452643d4bd2df24657`。
- 直接远端分支查询为`8400e71185cd04d30007f3fd26e2c2e9b3f1582d`，比固定实现仅多3份文档补记；**没有按该分支头审批或合入**。
- 发布基线为`99bbf5fdc3b9bb44287fcc87404028e98291c75d`。ca512a8的PSB-B-01～03主机C限定批准保持，不重复派修或扩大为异步/生产/实时批准。
- 原申请范围为`task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/engineering-closeout-20260921/`。最终相对新main仅新增该路径305文件，另附A复核报告/证据。旧执行源码只有trace_scoreboard.py发生返修；新增检查器、profile及文档均在该包。

## 实际运行与证据

环境：Windows/Intel、CPython3.12.14；本轮只加载标准库及轨迹检查器，不依赖NumPy。准确提交以独立detached工作树检出，局部core.autocrlf=false，未改全局设置/B工作树。

P为上述包路径，cwd为准确检出根；全部输出使用不存在的新路径：

```text
python -B P/repair-r1-r2/run_repair.py --repo . --out NEW_RUN
python -B <A-review>/adjacent.py --repo . --out NEW_ADJACENT
python -B <original-A-review>/probe.py --repo . --out NEW_ORIGINAL_PROBES
```

- 返修入口退出0：43项（34拒绝/9允许）；48项输出、4源码绑定、145旧文件原字节通过。原实现18项指定误接收得到复现，合法路径结果与原实现严格相同。保留run05、before失败以及原报告身份；未运行有意绑定旧checker的旧check_delivery.py。
- A新增14项邻接检查退出0（9拒绝/5允许）：完成下界−1、伪造status内自报时间、延迟提交/过期边界、列表中commit排在同拍status之前、同拍error优先、其他frame较晚完成不抬高本frame下界、字符串/NaN/Inf身份、背压时物理采样时钟继续前进。NaN/Inf为Python解码/调用健壮性探针，不当标准生产JSON。
- 上次A**原probe.py**实际复跑：原两例现在分别因完成下界及整数类型被拒绝，独立expected集合缩减和背压PCM变化控制仍拒绝。B保存的重建两例仍是B重建件，不将其称作A原文件。
- 检查CORDIC profile的3项源码/golden SHA，均匹配；profile仅离线身份，未改不变实现。新43项result.json与作者validation01语义及字节均相同；runner路径属于环境差异，不要求字节相同。
- 运行、完整日志、fixture和摘要分别见evidence/、adjacent/、original-probes/。旧A数值报告和原探针随`../b-engineering-d3d2a3d/`保存，不覆盖其NEEDS_FIX。

## 两项关闭判断

**R1关闭。** 每事务status_visible_at来自捕获行now，不来自DUT自报available。先要求独立expected集合全部完成，再要求max(status_visible_at)≤available≤commit_now≤expiry；事务/epoch隔离，没有借用别帧完成时刻。同拍status先于commit、同拍error阻断commit，延迟提交仍合法。后级只有进入外部expected_units集合才被覆盖；检查器不证明实际硬件捕获时钟/status可靠性。

**R2关闭。** 所有valid拍在背压比较前验证source_sample严格int（排bool），域[-8,2^64−9]；available严格uint64，emit仍严格uint64。startup负编号保留，首次/持续/恢复接受拍均不能用Python等值绕过类型检查。原PCM及时间映射未改。

## 批准与未测

结合原报告复用1215向量、S28包含界、RNE/饱和、32极端PCM及预算结果，允许本子目录B离线候选、检查器、异常夹具、合同/profile/预算资料入库。目标活动入口仍在任务包，不迁入默认生产链。无剩余本轮阻断。

CORDIC独立profile且reference25保留；8前视/17历史、串行pending与20ms平滑回mono仍限研究取舍，不是硬停。portable Q30/AMD24证据分列，107496B/202816B/552960B不混加；未知有限服务继续REALTIME_BLOCKED。没有批准生产接口、真实异步、硬件时钟/状态、AMD/RTL、CDC、实板、声学收益或完整H3。

## 集成、发布及本地保护

在99bbf5f上三方预演仅305个包内文件变化；准确ad30bda以非快进合并形成`a78f81bc5c65088713c4e4bd473ed0f557820c35`，无冲突。合后包Git身份保持，在最终路径重新运行run_repair.py退出0（43项及145旧文件/48输出/4源码），见postmerge/；没有扩大到数值全量复跑。

本机共享main仍cf026cf，与新主线存在1001个A未跟踪路径重叠；本轮不删除/覆盖这些未完成材料，采用独立发布工作树。**技术复核与远端发布可完成，共享本地main同步收尾待主流程处理。** 不宣称三端相同；最终SHA及ahead/behind在发布后回报。此同步事项不是B返修技术阻断。

A新增本轮及上轮相关报告、检查源码、原始输出均纳入本次发布记录，发布树本批遗漏为0；共享目录中的相应未跟踪副本因main未同步保留，其余A任务不夹带。本轮没有删除任何分支、工作树、原输出或失败记录，遵守用户保留要求。阶段总验收及其他成员电脑同步均不代签。
