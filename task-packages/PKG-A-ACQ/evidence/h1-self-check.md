# H1 候选样例自检

日期：2026-09-08；执行方：A 工作执行聊天，非 B 独立复核。

命令（在本包 payload 目录）：`python scripts/check_h1_fixtures.py`。

实际环境：Codex 工作区 Python；依赖仅标准库。运行结果：

```text
PASS fixture code-pattern: 6 rows
PASS fixture restart: 2 rows
PASS authored fixtures and 15 planned reader cases; B reader tests NOT_RUN; H1 confirmation pending
```

本次验证既有手写码型的结构与预期整数值，包括极值、编号精度、间断标记、新 acquisition_id。不代表生产读取器负例测试通过，不代表声学符号/定位、RTL、板测、H2 或 H3 通过。

未修改活动 docs/minimal-data-interface.md、旧冻结证据、Vivado 工程或硬件接口。全部新内容位于完整 PKG-A-ACQ 内；没有为 H1 另开独立包。A/B 针对准确版本的确认仍待补，不由助手代签。
