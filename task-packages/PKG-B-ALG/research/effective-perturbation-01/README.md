# EFFECTIVE-PERTURBATION-01：扰动是否改变实际定位贡献

本轮已完成独立研究。阅读[REPORT.md](REPORT.md)：识别并纠正了“删掉无信息频段却标稳定”的情况，但未改善跟踪表现，新旧输出逐帧一致。这里的有效信息仅指实际GCC频谱贡献，不代表目标语义信息或已校准的方向可信度。

默认PHAT和30°/5/12规则未改。cap150是未准入研究对照。所有成果集中在本目录，原606个文件哈希不变；本轮待拓芙（A）复核，未提交、推送或合入总工程。

| 文件 | 用途 |
|---|---|
| protocol.json | 运行前固定的种子、10%～80%贡献门限及规则 |
| features.py | 实际删除频点、GCC幅度及f²加权贡献，分类后评价稳定性 |
| run_study.py / evidence/ | 144次配对试验、完整诊断、方法行和汇总/延迟 |
| test_features.py / validate.py / tests/ | 新6项测试和原167项回归，共173项 |
| audit.py / audit.json | 独立重算资格、标签、指标，并复核输入及频谱 |
| compare_outputs.py / output-equivalence.json | 67248对跟踪输出逐帧等价检查 |
| report.py / REPORT.md / diagnostics.json | 可重建报告和数值摘要 |
| fixed-files.json / final_check.py / verification.json / files.json | 原结果冻结、最终核对、本增量清单 |

## 复现

需要完整PKG-B-ALG布局与原NumPy环境；本目录复用原信号/RIR生成器和留一候选，不单独拷贝源文件运行。

在本目录可只读运行：

```powershell
python -B test_features.py
python -B -c "import audit; print(audit.run())"
python -B final_check.py
```

完整重跑请复制完整任务包到新目录，在副本中将本目录evidence、tests及各结果JSON/REPORT.md移到独立保留目录（保留protocol.json、fixed-files.json），依次运行run_study.py、validate.py、audit.py、compare_outputs.py、report.py。工具拒绝覆盖原结果。压缩头时间与不同浮点环境可能带来字节差异，应如实记录数值与决策差异。

## A复核重点

确认实际谱幅度与能量、语义信息没有混称；全频掩码和cap150权重确实保持不变；无变化、不可比、过弱/过量与有效比较分开；未知继续通过不被说成可信；对性能没有改善的结论如实保留。A确认准确版本与范围后负责合入，仅可复核离线研究材料，不代表实板、H2/H3或默认替换。
