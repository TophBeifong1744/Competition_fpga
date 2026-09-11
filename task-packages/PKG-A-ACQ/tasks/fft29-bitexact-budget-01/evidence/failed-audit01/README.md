# A 辅助归档审计脚本失败，原件未变

首次重聚合错误地直接累加 `peak_changed`，B 对无效麦对正确存为 null，导致 Python TypeError。保留当时脚本及原控制台输出；修正为仅统计 `is True`，未将无效麦对视为正确峰值，也未改 B 证据。此失败与 FFT/XSim 数值无关。修正后的运行结果为上一级 `reference-audit.json`，控制台为 `reference-audit-console02.txt`。
