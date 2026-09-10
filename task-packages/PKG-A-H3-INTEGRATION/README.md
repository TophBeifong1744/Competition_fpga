# PKG-A-H3-INTEGRATION：定位／跟踪 → DAS → 音频输出工程约束

版本 a-h3-integration-constraints-0.1；2026-09-10。A 编制，B 复核；**约束包交付，不是 H3 通过，也不是 FPGA 算法准入批准。**

基线是实际 fetch 并经 ls-remote 核实的 main：`9878ccafdda6cd5a522cc9de95c1277bcee70f08`。新任务分支：`codex/toph/h3-fpga-integration-constraints`；不向 PR #3 审核分支追加，不自行合入。

## 直接入口

1. [H3 集成约束表及接口交接](payload/H3-CONSTRAINTS.md)。
2. [B 的预算字段与测试向量清单](payload/B-SUBMISSION-CHECKLIST.md)。
3. [验证与待复核结论](REVIEW.md)。
4. `evidence/source-index.json`：每份依据的原路径、Git SHA（适用时）、字节数与 SHA-256。

本包同时保留三类证据，不能混为一谈：

- `references/main/` 是上述 main 的原始 Git blob。旧文档写“码型源/无 PDM/FFT 待定”是其当时观察，不代表最新本机状态。
- `references/mono*/` 是 9 月 10 日单麦实录阶段的采集后源码/BD与实现报告、有限收尾说明。不是加载前身份绑定，不推断实际测频或完整外部 IO 时序。
- `references/fft/` 是另一任务已提交的 FFT 候选 `ac0ff38e954dac094fd84e28b329dcb24dded7fb` 原始 blob，完整保留复现脚本与历史证据；**它不是 main 已批准模块**，当前仍待 B 复核。本包不整支引入该实现，也不改变默认算法。
- `references/policy/` 为用户已确认、采集时仍未提交的 RTL/BD 语言规则快照；不冒称 main 内容。

## B 的复核命令

Python 3.10+ 标准库即可，不需要新板测或 Vivado。仓库根目录执行，输出目录必须不存在：

```powershell
python -B task-packages/PKG-A-H3-INTEGRATION/source/verify.py --out h3-constraints-review-run01
```

重算数值、验证 47 份来源哈希、运行 11 项算术测试，并使用所保留 FFT 作者入口复算其历史输出。该入口不是再次独立运行 XSim/综合，更不是板测。若要新综合/仿真，按 FFT 原 README 在新短路径执行，但不属于本次任务或当前批准范围。

本次可复现结果在 `evidence/recheck/result.json`。字节比较和数值比较分别记录；部分来源保留 CRLF，SHA 不进行换行规范化。来源采集脚本 `collect_sources.py` 只用于首次留档，依赖 A 的原路径；B 不应重跑它或改原证据。

## 本次未做

没有修改 B 默认 PHAT、跟踪器、阈值、原研究输入；没有新算法 RTL、四麦声学模拟、四／六麦声学效果比较、采购或六路采集扩展。仅按任务要求做通道数导致的接口与运算/存储算术差异。所有改动限定本任务包，保留共享目录改动。
