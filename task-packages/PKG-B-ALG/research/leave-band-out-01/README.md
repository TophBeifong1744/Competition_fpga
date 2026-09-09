# LEAVE-BAND-OUT-01：宽频留一频段扰动

本轮研究候选对频段删除是否敏感。结论及完整代价见REPORT.md；原默认PHAT、30°范围及捕获规则未改。cap150只是前轮未准入的研究对照。

每次从原宽频谱中删去一个频段，保留其他频点的掩码、相位和权重，检查时延和方向变化。两次以上有效且可比较的删除才作稳定/敏感判定；不足时标未知。严格方案拒绝未知，仅拒敏感方案保留未知；保留未知不代表已经确认候选可信。

## 文件与复核入口

| 文件 | 用途 |
|---|---|
| protocol.json | 运行前固定的频段、规则、种子和比较方法 |
| features.py | 保持宽频跨度的删频估计、变化量及筛选 |
| run_study.py | 144次配对试验，真值仅用于事后评分 |
| evidence/ | 完整原/删频诊断、方法输出、逐种子/汇总/延迟和来源哈希 |
| test_features.py / validate.py / tests/ | 新6项测试及原167项回归 |
| audit.py / audit.json | 独立重算留一诊断、标签、统计及延迟 |
| report.py / REPORT.md / diagnostics.json | 可重建报告与数值摘要 |
| availability.py / availability.json | 事后核查删频是否真正改变原保留信息，不改规则 |
| fixed-files.json | 原579个文件哈希，全部保持不变 |
| final_check.py / verification.json / files.json | 最终核对及本增量清单 |

## 复现

需要完整PKG-B-ALG布局和NumPy环境；工具从前轮冻结模块复用生成器、全频候选及窄子带比较。不能单独复制一个源文件后宣称完整可复现。

在本目录可只读执行：

```powershell
python -B test_features.py
python -B -c "import audit; print(audit.run())"
python -B final_check.py
```

完整重跑：复制完整PKG-B-ALG到新复现目录，将副本中本目录的evidence、tests和结果audit.json/availability.json/REPORT.md/diagnostics.json移到另一个保留目录，再依次执行run_study.py、validate.py、audit.py、availability.py、report.py。工具拒绝覆盖旧结果。gzip时间头与跨环境浮点差异需如实记录，不要求所有压缩文件字节一致。

## 交付边界

本目录是独立待复核增量，不覆盖此前成果；未提交、推送或合入总工程。指定复核/合入人拓芙（A）应核查：不删频时是否精确复现cap150；未知是否被误称可信；与旧窄子带方案是否同输入配对；覆盖率、范围外输出、HOLD和捕获延迟是否一起评估；固定参数是否在结果后变动。A确认准确版本与范围后负责合入。

该诊断不是置信概率，也不是实板、真实录音或H2/H3验收。即使某种筛选减少误输出，也须评估是否只因拒绝了大量正常候选。
