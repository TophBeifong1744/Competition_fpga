# 转接板绘制要求：交付与作者自检

日期：2026-09-10；版本：adapter-requirements-0.1；所属包：PKG-A-ACQ。

作者侧：A的硬件指导执行任务。复核及正式合入：B BryanZheng802。状态：待复核；未批准、未合入、未打板或上电。未修改父包既有批准版本和冻结证据。

## 清单

| 包内文件 | 目标活动文件 | 操作 | SHA-256 |
|---|---|---|---|
| payload/hardware/microphone-adapter-board-requirements.md | hardware/microphone-adapter-board-requirements.md | 新增，待复核 | 010504d95dfa6d5737d0a872204518ffa31f7313d8f6df76aeaa4e68998942af |

输入为同包payload/hardware/microphone-wiring-candidate.md的mic-wiring-draft-0.1及现行模块归档、H1接口、成员C操作单和包级交付规则。J4映射沿用待复核候选，未通过本稿提升为现场确认。未新增产品调研或修改接口设计。

## 自检结果

- 文内相对链接存在性：通过。
- 行末空白及代码围栏配对：通过。
- 新文件git diff --no-index --check：无空白错误输出。
- 范围：新增要求文档与本记录；未覆盖活动硬件文档，未修改他人未提交文件。
- 设计验证：未运行ERC/DRC，未生成EDA设计或生产文件；不是电气、时序、机械及声学验收。
- 待人工明确：汇线板/一体阵列板形式、真实封装/尺寸、J4与供电电平、制造参数及装配表。

## 复核记录

批准人、日期、准确版本哈希、通过范围、确认定位和合入授权：均待提供。作者自检不代替B批准；修改上述要求后须重新计算哈希并复核。C后续绘图是同一完整包内的执行子项，不为每次修订单独增加交接。
