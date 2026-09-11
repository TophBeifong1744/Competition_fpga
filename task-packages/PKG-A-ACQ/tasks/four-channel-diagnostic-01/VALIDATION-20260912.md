# 本次发布整理检查

日期：2026-09-12。环境：Windows，Python 3.14，隔离发布工作副本。只运行 Python 标准库测试；未安装依赖、未修改源码、未运行 Vivado/下载/板测。

- 原件复制：189 个文件与来源 SHA-256、字节数一致，清单验证入口为 `verify_delivery_20260912.py`。
- `python -B -m unittest discover -s source -p "test_*.py" -v`：17/17 通过，包含采集日志完整性、配置、DMA 错误、符号位、顺序、编号溢出/间断与导出来源。
- `python -B source/check_sim_export.py evidence/c-adapter-sim01/accepted_words.csv <新输出目录>`：PASS，3 次、57 组、456 个字逐值一致。使用历史仿真输出重新验证导出链，不是本轮重新运行 RTL 仿真。
- 附带说明、来源、恢复依赖与敏感令牌模式检查；原 epro2、账户目录、旧恢复工程和可执行缓存不公开。

这些是本次整理者的复制/软件回归结果，不是 B 的独立工程批准、声学效果、外部时序闭合或实板验收。以前的失败和成功日志保留原字节；未以新结果覆盖它们。
