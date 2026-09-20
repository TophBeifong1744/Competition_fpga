# run04 作者验证摘录

证据级别：作者软件复现，非 B 独立复核、非实板/实时、非完整 H3 验收。

## 可重复入口

在仓库根目录，Python 3.12 + NumPy 2.3.5，输出目录须不存在：

```powershell
python -B task-packages/PKG-B-ALG/tasks/h3-complete-20260918/source/reproduce.py --repo . --out ../h3-review-new-run
```

该入口依次执行包清单、输入前验、37项新测试、整数golden生成与冻结run04比较、真实输入诊断、预算、Skill范围、原三路音频入口及输入后验。作者复跑总退出码0，结果为 `PASS_AUTHOR_REPRODUCTION_NOT_INDEPENDENT_REVIEW`。主要日志摘要：

| 检查 | 作者结果 | 限制 |
| --- | --- | --- |
| 包清单 | PASS，60文件（文档最终封版前的作者运行） | 最终干净检出须以当前清单重跑 |
| 输入前/后验 | 均PASS，18项Git blob字节；本机2项CRLF→LF | 只接受精确blob或这一种换行转化 |
| 新测试 | 37/37，退出码0 | 软件单元/边界，不是RTL |
| 冻结golden | 14数组及lag、DOA、Tracker、时序、边界向量全一致 | 合成输入；14数组数值差异为0 |
| 既有三路音频 | 原入口报告50项PASS | 无客观音频收益真值 |
| 真实输入诊断 | center/quiet各61帧均过当前存在门 | quiet fresh=0不代表背景拒绝 |

冻结归档 `golden/golden-stages.npz` 原字节SHA-256：`056a084ebfb03e4b55b07e0033a9ddca6eaed79d63652d327e81afbfbf968f55`；`golden/SHA256.json` 对结果文件另列SHA。lag、DOA、Tracker事件是 `golden/golden-summary.json` 内的原冻结记录，检查器对每个字段的规范JSON哈希分别对比；测试会篡改冻结字段确认检查器拒绝。

开发期一次检查器首试因Python tuple/list与JSON数组对象比较不一致而失败；该实现误判已改为同一规范JSON内容比较，未覆盖当时的冻结run04结果文件。此处记录的是失败原因及修正，不把第一次失败说成通过。

原三路音频工具在任务包外的作者运行目录生成了含本机绝对路径的命令记录；这些记录未纳入仓库。本页只保留脱敏摘要，不声称外部运行目录等同于可发布证据。B 应在自己的干净检出独立重跑，保存其原始执行日志。
