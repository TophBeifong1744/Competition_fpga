# NARROWBAND-GUARD-01：窄带候选保护

本轮是PKG-B-ALG内独立研究增量，指定复核人为拓芙（A）。当前默认算法、30°允许锥角和5/12捕获规则均保持不变。本轮未获A批准，未提交或合入总工程。

阅读入口：REPORT.md；完整开发及验证结果分别位于development/、validation/。不要把开发通过等同于验证通过或工程准入，请以最终报告的两阶段判据为准。

## 实现内容

guard.py提供两种帧级候选保护。fallback035使用跨麦对的频谱集中度判断是否回退原PHAT；cap150保留β=.75，但限制强频点的权重。两者仅接受六麦帧和固定方法名，不读取方向真值、目标存在标签或将来帧。跟踪仍调用原QuorumSession。

开发按预先写入protocol.json的准则选择候选，selection.json记录源码及协议哈希。验证必须与这份选择完全一致，只跑冻结候选。开发和验证种子互斥并与历史批次分离；验证更换单频频率并扩展尾声条件。

## 文件与复现

| 文件 | 用途 |
|---|---|
| guard.py | 独立保护候选实现 |
| study.py / protocol.json | 输入生成、配对运行、事先固定判据及选择 |
| development/selection.json | 开发选择与验证锁定依据 |
| development/、validation/ | 帧结果、逐种子/汇总指标、延迟、输入哈希与运行哈希 |
| test_guard.py / validate.py / tests/ | 新增5项测试和原167项回归 |
| audit.py / audit.json | 全量落盘复算与来源锁定检查 |
| report.py / REPORT.md / diagnostics.json | 可重建的报告及数值摘要 |
| fixed-files.json | 517个前轮文件哈希，保持不变 |
| verification.json / files.json | 最终核对与本增量清单 |

依赖同一任务包的payload、reference及旧evidence，交接时保留完整PKG-B-ALG结构。解释器使用已安装NumPy环境即可。新旧证据不覆盖，本目录脚本输出若存在会拒绝写入。

在本目录可只读运行：

```powershell
python -B test_guard.py
python -B -c "import audit; print(audit.audit())"
```

完整重跑请复制整个PKG-B-ALG到新复现目录，在副本中将本目录development、validation、tests及audit.json/REPORT.md/diagnostics.json移至独立保留目录，然后执行：

```powershell
python -B study.py development
python -B study.py validation
python -B validate.py
python -B audit.py
python -B report.py
```

开发集通常需要数分钟，验证集更久。浮点平台变化可能造成边界结果或文件哈希差异，须如实记录；不能为追求字节一致而修改原结果。

## A复核重点

核查新种子隔离、开发选择准则、冻结源码、合法窄带目标误伤、32°范围外误输出、宽带收益保留和延迟/HOLD副作用。即便六麦离线判据全部通过，也不代表真实录音、四麦、实时计算预算、实板或H2/H3通过。A确认准确版本及允许范围后负责合入。
