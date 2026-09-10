# 单麦诊断包整理检查

2026-09-10；本分支仅完成文件整理和离线复核，等待 B 复核；没有 Git SHA、推送或合入。

## 实际执行

使用本机 Codex 依赖 Python（标准库），从交付包目录执行：

```text
python -B source/mono_delivery.py export --report evidence/export-validation.json
python -B source/test_delivery.py
```

- 两份 BIN：各 768000 字节、48000 条记录；绑定既有 SHA-256，FNV、原始 ID、符号、零标志与串口统计通过。
- 原幅度 WAV：24bit PCM 逐样本与 BIN 一致；CSV 不作任何音频处理。
- 测试 10 项通过，日志 `tests.txt`；覆盖原件/导出、截断、错误校验、符号越界、ID 缺口、溢出/未知标志、饱和保留、64 位编号进位。负例为内存中修改的测试副本，未保存为录音。
- 用 PowerShell Get-FileHash 逐一比较工程原目录与本包 originals：26 个文件字节哈希全部匹配。没有覆盖原件。
- 在系统临时目录调用同一导出器重新导出，再验证；两份 CSV 与 metadata 共 4 文件均逐字节一致，临时目录随后由 TemporaryDirectory 清理。该复跑检验可复现性，不冒称第二套独立算法。

导出器在旧 decoder 基础上复用 `<IIiI`、FNV、signed24、ID 及 flags 规则；仅本包新脚本改变来源表达和补充可追溯信息。原脚本留作参考，未修改工程候选。

## 本次可交付范围

允许 B 读取单麦 diagnostic 数据，分析码值、频谱及初步声音响应。不表示公共 H1 schema 改版；B 需使用本包独立单麦入口，不能补列凑四路或输入六麦定位。

尚未独立复现工程后续实现/时钟分析，也没有测量板卡或验证旧加载身份。A 既有复核和最新有限收尾决定已保留；本包不扩大其批准范围。全部参数未知项、低频问题和电气/IO 缺项见 metadata、README 及 ACCEPTANCE_STATUS。

**结论：单麦诊断数据整理与离线一致性检查通过，交 B 复核；完整四路 H2 未完成。**
