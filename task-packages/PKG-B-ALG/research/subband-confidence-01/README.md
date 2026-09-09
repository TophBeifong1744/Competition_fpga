# SUBBAND-CONFIDENCE-01：子频带与边界证据

已完成独立诊断，**本轮筛选不适合接入正式算法**。阅读[REPORT.md](REPORT.md)：范围外误输出虽降至0，但正确输出几乎消失；合法窄带目标不能满足多子带前提，边界包络也未经概率校准。

全部源文件、固定协议、测试、结果和说明集中在本目录。原552个文件保持不变，原默认PHAT未改。前轮未通过的cap150只是本次对照研究对象，并未成为默认。指定复核/合入人是拓芙（A），本轮尚未取得批准，也未提交、推送或合入。

## 交付文件

| 文件 | 用途 |
|---|---|
| protocol.json | 运行前固定的频带、门限、种子和研究范围 |
| features.py | 子带PHAT、方向/时延一致性及经验边界包络 |
| run_study.py | 144次配对试验；不选择参数 |
| evidence/ | 原始诊断、方法行、汇总、延迟、输入/来源哈希 |
| test_features.py / validate.py / tests/ | 新6项测试与原167项回归，共173项 |
| audit.py / audit.json | 从落盘子带时延、方向独立重算诊断，核对指标 |
| diagnose_loss.py / loss-diagnosis.json | 事后证据可用性分析与12个无噪声辅助对照 |
| report.py / REPORT.md / diagnostics.json | 可重建报告及摘要 |
| fixed-files.json | 历史552个文件哈希 |
| final_check.py / verification.json / files.json | 最终核对及增量清单 |

## 复核与复现

依赖完整PKG-B-ALG布局及原NumPy环境；不能只复制本目录的单个脚本。主试验使用全新种子2026091500–1502，无开发选优；事后辅助对照如实单列，不用其调整主试验或宣称泛化。

在本目录可只读运行：

```powershell
python -B test_features.py
python -B -c "import audit; print(audit.run())"
python -B final_check.py
```

完整重跑请复制整个PKG-B-ALG到新目录，并在副本中将本目录evidence、tests及各结果JSON/REPORT.md移到独立保留目录，保留protocol.json、fixed-files.json和全部源文件。依次运行run_study.py、validate.py、audit.py、diagnose_loss.py、report.py。工具拒绝覆盖既有结果。gzip时间头和不同浮点环境可能导致字节差异，应比解压后的数值/决策并记录差异，勿覆盖原证据。

A重点复核：不足/冲突/边界不确定是否分开；方向包络是否被误称置信区间；减少误输出是否伴随覆盖率崩溃；真30°与32°是否分开评价；事后对照是否如实标注。A明确确认准确版本与范围后负责合入，仅批准研究材料不等于准入筛选算法。
