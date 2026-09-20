# 9/18 H3 集中评审回交（B → A）

实际整理/执行日期：2026-09-20；“9/18”是评审批次，不倒填完成日期。状态：**完整评审材料回交；完整 H3 仍 NEEDS_MORE_EVIDENCE**。本包不是完整实时实现，也不自行批准或合入main。

输入清单固定为 A 的 `16afda2772b37ca5e50852c0f62944cd6f541472`，先读其 REVIEW.md、再读 README.md，原件按Git引用和哈希保留；不修改A文档。发布基线 `6751664d18db077046e0a5d5a0bfc84fcefce108`；新任务分支 `task/member-b-h3-interface-20260920`。本包准确候选SHA由最终发布回执提供；在独立检出执行 `git rev-parse HEAD` 必须与回执一致。文件内不伪造自引用SHA。

现有软件候选准确SHA为 `7a17edd2b5408e10608d954f3e7fa11cb62fe34b`，目录 `tasks/h3-complete-20260918/`；其run05断流闭环已获B限定PASS并于main的a440d9b发布。原README“待B复核”是历史状态，批准范围以 `docs/reviews/h3-run05-7a17edd/B-REVIEW.md` 为准，不能扩大为全H3。

## A 一次评审的八项入口

| 要求 | 回交位置与结论 |
| --- | --- |
| 1 准确完整候选SHA | 最终发布回执为本集中包SHA；上游软件候选7a17edd；不存在已准入的完整实时H3实现SHA |
| 2 四路最终数制/FFT | NUMERIC.md：默认reference25不变，29→25软件候选与六路共同指数研究分开；生产最终数制未冻结 |
| 3 clip/错误/重启/无目标 | INTERFACE.md：保守分段、状态作废、unknown存在语义；不得将quiet判过门解释为声学通过 |
| 4 握手/帧状态/结果包 | INTERFACE.md：提交给A裁决的合同草案；硬件ABI/实现尚未冻结 |
| 5 1024/512与跨包golden | source/framing_review.py、golden/：复用真实H1读取器/分帧器；250组双槽回放、错误/重启边界及S1全部561帧逐帧PCM哈希 |
| 6 缓存/复用/WCET | SCHEDULE.md：生命周期、调度条件和可复算预算；真实最坏周期仍缺项，不以历史FFT槽相加冒充 |
| 7 冻结/研究/未测 | STATUS.md、references.json：逐项准确证据身份，旧批准不升级 |
| 8 最小模块/阻断 | STATUS.md：先评审纯分帧适配合同和golden；获准后再开发PS/PL实现，不直接接实时算法 |

## 本次实际新增与复用

新增集中合同、差距矩阵、源文件哈希引用和分帧索引/PCM golden。分帧回放是离线测试工具，**不是DMA驱动或有背压的实时适配器**。它将250组包拷出两个重复使用的NumPy槽，随后交给已批准H1读取/分帧器；逐帧与原始数组的独立索引公式比较，验证复制前后数据/通道/ID未变。包边界和FFT帧尾严格分离；1023/1024等样点边界是逻辑区间测试，不声称硬件接收了短DMA包。

本次不重跑FFT覆盖、run05整链、旧音频、S1导出或耐久；准确版本/现存批准与哈希证据引用见references.json。未新编译ARM、修改RTL/BD/Vitis、执行XSim/综合实现/上板。

## 一条增量复现

Python3.12与NumPy2.3.5；在仓库根运行，输出目录必须不存在：

```powershell
python -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/source/reproduce.py --out ../h3-interface-review-new
```

入口验证包清单与固定Git依赖、复算本包分帧golden、验证篡改负例、重算既有预算并与冻结结果比较。不会重跑旧FFT/IP或实板任务，不写原golden。结果只表示本包作者增量复现，不代替A独立评审。

请A按STATUS.md一次裁决可接入的最小范围及未决合同；本分支仅提交评审，不合入main、不触碰A实际工程。
