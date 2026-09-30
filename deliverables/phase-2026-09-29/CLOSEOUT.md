# 2026-09-29 M1、H3 与模块准入检查点收尾

记录日期：**2026-09-30（UTC+8）**；计划检查时刻为 9/29 20:00。**裁决：检查点部分收尾，整体技术验收未通过。** 用户授权本次记录、发布及遗留承接，不新增技术批准，不将 9/30 补进展倒记为按期完成。

权威入口：[Milestone 2](https://github.com/TophBeifong1744/Competition_fpga/milestone/2)。原 Issue #17/#18/#19/#21 保持开放并承接 10/3 下一检查；关闭日期 Milestone 仅表示裁决和移交完成，不表示完整 M1/H3、Skill 或 BOARD 已通过。10/6 冻结和 10/7 10:00 总验收不顺延。

## 分项裁决

| 原任务 / owner / reviewer | 检查日前的限定成果 | 未通过或尚缺 |
| --- | --- | --- |
| [#18](https://github.com/TophBeifong1744/Competition_fpga/issues/18)：A / B | 原短采集、正常停止重启证据按实际范围复用；独立 M1 固件、主机工具及组合已形成候选。 | 正式 M1 的可测通道固定差异、一小时连续采集、超时恢复未齐。主机候选不能替代真实工程准入、DMA、消费者、实时、资源或时序。成员批准按实际时间列于证据索引，不一概当作 20:00 前已取得。 |
| [#17](https://github.com/TophBeifong1744/Competition_fpga/issues/17)：B / A | PR34 `cabe1a0cdb263fce012f99f5d32675f194dfe8d8` 获 A 限定批准，9/29 合入 `87fdb3d0029c6a18a78408b20d93efcbfcb01923`；范围 portable / SYNTHETIC_TIME 功能仿真。P1～P4 于 9/29 双方确认。 | 完整生产 H3、真实时基/消费者首次 take/完整水位/服务上界及正式声学效果未通过。软件候选不能代 PL/系统实现。 |
| [#19](https://github.com/TophBeifong1744/Competition_fpga/issues/19)：C / A | PR35 `eb50145225e703aa060328e7a2113deaca353ddf` 于 9/29 获 A 限定批准并合入 `3bf64351728dbe4bdba4e2b7836a5d96c613e444`；v2 接口与模块 FUNCTIONAL_SIM 闭合。 | 独立实物效果/系统联动另列；现场声明保持 USER_REPORTED，独立 BOARD 为 INCONCLUSIVE。不新增视频/照片门槛。 |
| [#21](https://github.com/TophBeifong1744/Competition_fpga/issues/21)：A / B | PR31 `97a04e9cb859a915a31d8a2b3cdaaaa09009019b` 的导出/包装身份已有 B 限定批准。 | PR 仍 OPEN；陌生模块、未知故障、独立安装复用与完整 Skill 未整体通过。 |
| [#22](https://github.com/TophBeifong1744/Competition_fpga/issues/22)：A / C，B 专项 | 原属 10/3，本次只核 9/29 的第二项 Skill 候选交付义务；C22-01/02 与 I22-B-01 按准确事件范围保留接受。 | 9/29 清单 git_blob 问题未闭合；真实 PYNQ/DMA 与独立复用未通过。不把后续所有要求倒加为候选交付门禁。 |

## 检查时刻之后的补进展

- 三项目标选择政策、评价器规范及后续产品/测试交付按实际事件时间列明，不能把“同一天”都当成 20:00 前完成。
- PR38 产品 `b16304defc7e847afc29c8411ccf19644cf78a58`、测试候选 `48c494e73996b734d887d1def08b30d485bbe23e` 已交审；9/30 查询 PR 仍 OPEN。作者合成证据与独立技术结论、成员批准分列，不自动算完整 H3。
- 9/30：PR32 元数据候选 `beceee335d5c6d0ce96a2150f4a2ad107854e3a9` 已推送；X 报告仅改 18 个 git_blob、143/143 核对，状态 FIXED_PENDING_REVIEW。旧 APPROVED review 不自动覆盖新 SHA。
- 9/30：用户亲自完成新 M1 两应用三源/宏、两份真实 pre 和 Build。M 核两份 PRE_PASS、48 项冻结包身份、对象/ELF/map，并从原生 IDE 日志确认 diag 13:35:13、normal 13:35:26 与 13:38:13 的 Build status_code:0。这是 9/30 的真实构建进展，不是 9/29 M1 通过。
- 原生日志显示 platform/BSP 生成；Ninja 链接规则使用 cmd.exe /C，与冻结直接 GCC checker 的支持域不同。保持工件并先有界诊断；真实 post/load、下载与板测未运行，不裁剪原命令冒充受支持记录。

## 下一检查的责任

- A / #18：处理真实构建身份和工具支持域，再按用户亲自工程操作约定推进实物采集；复用已接受主机证据，不盲目重跑矩阵。
- A+B / #14、#17：生产接口、消费者/时间和测量入口按原合同接合；上界 UNKNOWN 不填默认。PR38 既有独立复核沿原派单，不重复派审。
- C / #19：模块结论复用，10/3 独立效果及后续联动单列；#20 已缩小范围关闭，不重开摄像头任务。
- A/B/C / #21、#22：现有候选准确范围接收、发布和独立复用；PR32 只交 B 元数据短审。PYNQ 未准入保持原状态，Vitis 主线按批准范围推进。

上述是原任务移交，不新启动工程写批；接单状态仍以真实回报为准。

## 版本、入口与验证

本次集成参考为 `11053af5ab15b7593d418cfdc4bf615d549d5e66`，不是所有分项实测 SHA；分项身份和成员事件见 [EVIDENCE-INDEX.md](EVIDENCE-INDEX.md)。

已批准活动入口保持 `models/python/soundsight_h3_portable/`、`project/rtl/algorithm/fixed4/`、`simulation/tb/algorithm/fixed4/`、`project/rtl/servo/motor_drive.v`、`simulation/tb/servo/`。未合入 PR31/32/38 留在原候选；新 M1 固件/checker 按冻结包和 F: 用户工程身份区分，不借本收尾进入生产源码。

本次只核 GitHub 原事件、文件/链接、版本和保护清单；已有仿真、算法、录音及主机测试按适用范围复用，未重跑。本文件为日期快照，动态事实只回原 Issue/PR。旧失败、未跟踪/ignored、共享 fixed4 修改均保留，不清理。机械记录在 `codex_out/september-checkpoint-closeout-20260930/`；发布后检查共享 main/origin/直接远端和本批遗留。撤回治理记录应新增更正，不 reset/clean，不改变工程回退点。
