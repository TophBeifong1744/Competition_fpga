# run05 首错原始日志的受控取回说明

2026-09-20，A/主流程实际核实文件存在、长度、只读属性和SHA-256；未运行技术测试，未公开原始日志内容。

| 字段 | 核实结果 |
| --- | --- |
| 制品编号 | `H3-RUN05-FIRST-FAILURE-RAW-01` |
| 保管人 | A / 拓芙（Toph Beifong） |
| 存放设备 | A 当前 Windows 开发电脑；非 Git 目录 |
| 存放路径 | `%USERPROFILE%/.codex/visualizations/2026/09/09/01a086de-c5a0-7ee2-b46c-c0bd5b6d3dfd/h3-private-evidence/run05-first-failure.raw.log`；这里的USERPROFILE指A的Windows用户目录，不是B电脑目录 |
| 字节数 | 950 |
| SHA-256 | `DCF5A3FBE69CA7CD1D5537371B7F7A21777D770DFCCB110F71A67DD10C3762EE` |
| 文件属性 | `IsReadOnly=true`；只读属性不等于访问控制或已完成异地备份 |
| 公开脱敏副本 | `task-packages/PKG-B-ALG/tasks/h3-complete-20260918/evidence/run05/first-failure.redacted.log`，不冒充原字节 |

取回流程：B或获授权复核人向A报制品编号与上述SHA-256；A从该位置以文件附件私下提供原字节，由接收人核对950字节和SHA-256，再记录接收时间与核对结果。原件包含个人绝对路径，不放入公开Git；不以复制脱敏件、改换行或重新运行失败实验代替原件。需要迁移时须保持原字节并补记新位置。

**当前状态：A已验证可取回位置与原件身份；本轮没有向B发送附件，也未取得B收件回执。** 本文件关闭“只有哈希、无明确存放位置/取回说明”的文档缺项，不声称B已取回原件，也不扩大run05的技术批准范围。
