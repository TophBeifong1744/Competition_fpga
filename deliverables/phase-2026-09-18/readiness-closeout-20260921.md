# 9/18 A工程补缺：批准与本机发布收尾

实际日期2026-09-21。固定集成基线`f7355ed61fd9d17f706f518d28d25933945bbcdb`。本页记录已批准事实和A本机收尾，不是新的技术自审，也不宣布9/18声学基线或完整H3通过。

## 已闭环范围

| 准确版本 | 裁决 | 当前入口/限制 |
|---|---|---|
| `ca512a8be7978ab6ca2ade3d5e0b922e53a89c79` | B限定PASS，PSB-B-01～03关闭 | [B报告](../../docs/reviews/ps-repair-ca512a8/B-REVIEW.md)；有效源码在原A任务下ps-semantic-bridge-repair-01/src；原错误candidate只作历史 |
| `f08556d01821d6c3c8204fdac2c38f53b2107c05` | B限定PASS，29文件合同/缺项/条件预算获准归档 | [B报告](../../docs/reviews/readiness-f08556d/B-REVIEW.md)、[B收尾](../../docs/reviews/readiness-f08556d/CLOSEOUT.md)；不是生产ABI或部署批准 |
| `ad30bda694abc946db045192385ebdf1b8e1a956` | A另项独立批准，B工程R1/R2关闭 | [A报告](../../docs/reviews/b-engineering-ad30bda/REVIEW.md)；原d3d报告保留，不再按旧缺陷派修 |

A本轮合同候选、golden缺项计划、条件预算及PS桥返修不再待复核。生产profile、ARM/BSP、AMD/RTL/CDC、真实缓存/DMA映射及16项服务上界仍未证实，**REALTIME_BLOCKED**。真实方向/音频指标不因这些材料入库获得批准；不新增录音、M1、摄像头或Skill门槛。

保留B非阻断限制：预算检查器不是完整配置schema验证器；部分未知queue参数下不逐字段诊断，但不会据此判容量通过。以后开放配置输入再补，不为本次限定收尾重派返修。

## 活动入口与未接入原因

- [合同/预算唯一入口](../../task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/PRODUCTION-READINESS-20260921.md)，最新批准以本页及B报告覆盖作者历史待审字样。未改冻结合同稿或清单。
- 主机C有效入口在上述同父目录`ps-semantic-bridge-repair-01/src/`；未经ARM/BSP、真实异步/内存合同和对应工程选择，不迁入Vitis/one或生产ps目录。
- 没有新增获准生产RTL，不为填活动目录把研究源码迁入rtl/。后续工程仍由拓芙选择原工程/副本并操作；A负责实现和证据，B负责独立复核。

## A本机安全同步（本次实际执行）

1. 读取远端main和准确B报告，核实f7355ed。原共享main为cf026cf，本地只有其他任务未跟踪材料，无已跟踪修改或暂存内容。
2. 复用`deliverables/phase-2026-09-18/recheck-20260920/audit-local-sync.ps1`，识别**1673个**主线新增路径与本地未跟踪文件重叠；Git原字节全部一致，不相等0。该数字是重叠路径数，不是独有修改数。
3. 初次批量移出被权限审查拒绝，未执行。用户随后明确授权；只移动上述已核对的单文件到下述仓库外归档，逐项SHA-256核对，未移动其父目录或其他文件。
4. 快进共享main到f7355ed，不reset、不切换脏分支。HEAD/main/origin/main在本次核对时一致，原件归档1673项哈希全部匹配。
5. 新检出中另两份B工程报告的7个普通文本文件出现Git检出CRLF差异；原归档及Git对象保留原字节，仅将该差异独立记录，不修改旧清单。第一次要求检出文件全部原字节相同的检查因此失败，记录保留。**本次f085的29份文件仍逐字节与批准Git对象一致。**
6. 在实际E盘共享仓库最终入口运行检查器到新目录，30项/11来源通过；仅相称复跑，不重跑FFT、33/122项C全测、采录、耐久或B节点。生产状态仍BLOCKED。

原件归档（未删除，非唯一副本）：

`C:/Users/Toph Beifong/.codex/visualizations/2026/09/07/01a07c21-b7f9-74d2-92c5-7f8d235d8379/readiness-sync-backup-20260921/`

目录保留原相对路径及SOURCE-MANIFEST.json；原审计清单SHA256：`225f8bb47a19a028e159a466101d9a045e48f6da86d7035125866497ef0722f7`。恢复时先按清单核对SHA，只复制到全新恢复目录，不覆盖当前工作。此次是可恢复移动，不是删除。分支、工作树及实际工程均未清理。

## 命令与证据

仓库根执行：

```powershell
$a='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918'
python -B "$a/check_readiness_20260921.py" --out <不存在的新输出目录>
```

本机实际命令/环境/结果见[a-local证据](../../docs/reviews/readiness-f08556d/a-local-20260921/local-check.json)和[最终入口命令](../../docs/reviews/readiness-f08556d/a-local-20260921/smoke/command.json)。`approved_files_unchanged=29`通过准确Git对象与共享文件原字节双重核对；原件归档及检出差异逐项有记录。新补文档仅做链接/范围检查，不按代码变更重审。

## 批次状态与保留项

- 本批29份材料已归主线且原字节一致，没有本批未说明独有内容；阶段当前状态、工作包台账及PKG-A入口随本页更新。
- 原continuous、两项Skill、帧适配候选、A早期接口工作稿、早期未发布`recheck-engineering-20260921.md`等继续原位保留；这不是全仓干净声明，也不代签其他任务结束。那份早期未发布阶段草稿不作为当前正式入口，本页不覆盖它。
- 本页发布后再次核对实际共享main/跟踪/直接远端。最终发布SHA由本页提交历史与工作执行回报绑定，不用被核查的f7355ed冒充本页提交。
- 这是A本次批准材料的发布收尾完成，不是完整H3、实时或整机阶段通过；后续生产实现与正式声学评价保持原范围。
