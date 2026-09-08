# 噪声下捕获改进与新种子验证

版本capture-research-0.1。已有batch-presence-0.1批次作为固定参照保留原位置，reference/batch-presence-fixed/frozen-files.json记录139个参照文件哈希，实验前后均核对。旧批次、生成器、读取/分帧/定位代码、sector_tracker.py及默认配置未修改。

本轮优先研究捕获机制。原定位质量门不放宽，不修改GCC频带、范数或残差门槛；新算法位于独立quorum_tracker.py，通过QuorumSession复用既有帧时间及重置适配。默认运行入口仍使用旧跟踪器，新方案是研究候选，未自动替换或合入。

## 问题与方案

旧噪声开发集在场时原定位有效率45.571%，旧跟踪仅1.384%。10个种子合计存在52个连续五候选窗口，其中只有3个窗口的方向两两符合8°稳定要求；原捕获流程遇拒绝/不稳定就重开，最终只有一个种子产生新有效输出。窗口诊断是机会计数，不等于实际捕获次数。

新方案quorum5of12要求：

1. 当前帧必须通过原定位质量门和允许方向范围，才能提供新方向。
2. 仅查看最近12次输入（含拒绝帧），同时删除距当前时刻超过120 ms的历史。
3. 从当前有效方向开始，按从新到旧的顺序收集候选；每个加入方向与已选所有方向的夹角都≤8°。
4. 满5个才捕获，初始方向是这5个方向的归一化均值。没有足够候选时保持SEARCH/ACQUIRE，不输出旧票的方向。

这是确定性的贪心选择，不保证找到窗口中所有可能的5点组合；复杂度受窗口上界限制。拒绝帧可以间隔在候选之间，但不会成为有效票，更不能直接成为新输出。正常连续五帧仍可按原速度捕获。

锁定后的20°更新门、200 ms HOLD、超过30 ms输入间断重置、手动释放及配置变化释放均保持原策略。当前输入无效时，即便历史已有多票，也不会首次捕获。帧reset_before会清空票与锁定；异常时间不会破坏既有状态。

## 选择与验证隔离

payload/config/capture-research-protocol.json在评价候选前写入，固定两种选择：5/12、120 ms；4/10、100 ms。两者保持原8°稳定性。开发使用旧种子2026090800–2026090809，验证使用此前未参与选择的2026090900–2026090909，五场景时间表、信号生成及评分口径相同。

预先约定的开发判据：噪声在场≤10°正确输出率相对旧跟踪增加至少10个百分点；新有效帧P95≤12°；每场景不在场错误新输出率增幅≤0.5个百分点；正常场景≤10°正确率下降不超过1个百分点；噪声在场>30°错误率增幅≤0.5个百分点。两者都通过时优先5/12，否则选通过者；均失败则不推荐。

开发集5/12通过所有判据。4/10虽然噪声输出更多，却使同锥竞争者不在场错误新输出率从97.546%增至98.160%，超过预先设定的增幅上限，因此未入选。这个判据仅约束“不能明显恶化”，不表示原97.546%的身份错误率可接受。

开发结束生成selection.json，写入方案、代码和协议哈希。验证命令要求哈希完全匹配，且只运行选定的5/12方案。看到新种子结果之后没有修改或再选参数。验证仍是相同合成分布的新随机实现，不等于新场地或真实声音验证。

## 运行和文件

```powershell
cd F:\NUEC\task-packages\PKG-B-ALG
& 'C:\Users\BryanZheng\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B payload/model/python/capture_research.py --phase develop --out evidence/my-capture-development
& 'C:\Users\BryanZheng\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B payload/model/python/capture_research.py --phase validate --selection evidence/my-capture-development/selection.json --out evidence/my-capture-validation
```

目录必须尚不存在。开发从固定批次读取原定位候选进行重放，不重新生成或覆盖旧结果；验证从新种子生成连续六麦信号，先计算一次原定位，再在同帧上比较原定位、仅圆锥、旧跟踪和新跟踪。场景/存在标注和真值只用于后续评价，不传给QuorumSession。

frames.csv保留各方法逐帧新有效输出、HOLD、过渡标记及误差；per-seed.csv、pooled.json和paired.csv保留每种子、合计及配对差；latencies.csv沿用目标开始到第一个完整在场且≤10°正确输出的定义，未捕获为null。开发另有diagnosis.json与selection.json；验证有validation-inputs.json的波形和标注哈希。run.json锁定来源、种子、状态及结果文件哈希。

API可用QuorumSession(config, CaptureConfig(5,12,120))，其update/release/configure接口与旧TrackingSession一致。公开配置仍需原有Config。输入应来自可信的本包定位行。该候选尚未增加到默认六麦CLI，不改变此前操作命令的行为。

## 证据与限制

151项回归通过，包括拒绝间隔、票窗口/时限、当前帧要求、方向一致性、孤立异常、HOLD/到期与旧实现一致、配置/手动释放、帧中断和异常时间。audit_capture_research.py从开发/验证落盘数据独立复算210150行的存在标签、角度、质量/范围约束、HOLD排除、汇总分母、配对增益及延迟，并核验固定参照、源文件和种子隔离；输出见evidence/capture-research-audit.json。

读取evidence/capture-research-report.md时，应同时看有效率、≤10°正确率和P95。新方案增加可用捕获，但仍不能恢复原定位拒绝的帧；噪声下新有效率只有约36%，不能宣称稳定连续跟踪。HOLD会更常见，显示端必须继续按期限处理旧方向。

没有改进等强竞争下的缺候选，也没有解决同锥说话人身份。旧算法保留为参照；下一轮应优先检查候选估计本身或更广噪声/方向条件，并使用新的验证集。当前结果仅支持把5/12作为有证据的研究候选，不构成产品验收或H3批准。完整包仍由A复核后负责合入。
