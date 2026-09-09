# TONAL-EDGE-01：单频噪声边缘退步诊断

状态：B已完成本地研究，待拓芙（A）复核；不是新算法验收。阅读入口：[REPORT.md](REPORT.md)。

本轮完成81次配对试验，保存43,200条稳定有目标诊断记录，28,800条原始/跟踪记录与本地已批准参照吻合；170项测试通过。主因是β=.75增大强单频成分的权重，定位偏差被30°方向边界放大，主要增加候选出锥。存在混响残余效应，不能只归因于单频成分。

## 文件

| 文件 | 用途 |
|---|---|
| study.py / protocol.json | 冻结的诊断实现与控制变量；不调参 |
| test_study.py / validate.py / tests/ | 新诊断测试及原167项回归，共170项 |
| evidence-run-02/ | 81次试验的输入哈希、活跃帧诊断和运行清单 |
| analyze.py / analysis.json | 全部配对分解、原结果对照和逐种子统计 |
| report.py / REPORT.md | 可从落盘统计重新渲染的结果说明 |
| fixed-files.json | 前轮496个文件的固定哈希，全部保持不变 |
| approval-context.json | 用户提供的前轮A批准依据；本轮未获批准 |
| evidence/attempt-01.json | 首次生成检查中止及修正记录，无算法结果 |
| final_check.py / verification.json | 最终来源、数字结论和报告一致性检查 |
| files.json | 本增量包的文件哈希，不包含自身 |

## 复核与复现

本目录依赖同一PKG-B-ALG内冻结的payload、reference及前轮evidence。交付时保留完整PKG-B-ALG布局，不能只复制study.py。前轮清单仍描述已批准版本，本轮另有files.json，避免改动已批准文件。

在本目录可只读执行：

```powershell
python -B test_study.py
python -B final_check.py
```

完整重跑：复制完整PKG-B-ALG到新的复现目录；在该副本中把本目录的evidence-run-02、analysis.json、REPORT.md及tests移到另一个保留目录，再依次执行study.py、analyze.py、validate.py、report.py。工具拒绝覆盖旧结果；不要在原固定包内移走或覆盖已完成证据。第一次中止是正弦重构的浮点运算顺序不同，已匹配原生成器并增加整段分解测试，未改变算法、协议或种子。

A重点复核：干预是否控制同一目标与RIR；频谱幅度权重与能量是否区分；净损失是否包含挽回帧；40°是否仅作为解释性对照；原种子是否如实标明回溯用途。A应记录通过版本、范围和限制，确认后由A合入。本轮尚未提交或推送，未覆盖总工程。

后续建议：另设开发集研究窄带集中度诊断和候选保护，冻结后用全新验证集验证；不直接扩大允许锥角，不继续仅放宽捕获。
