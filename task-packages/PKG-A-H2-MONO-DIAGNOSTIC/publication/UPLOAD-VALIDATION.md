# 上传前复跑记录

2026-09-10，A 执行任务 01a07c21-b7f9-74d2-92c5-7f8d235d8379，独立发布工作区；Python 为本机 Codex 依赖运行时。未操作板卡。

- source/file_manifest.py verify：PASS，原清单 41 文件全部一致，不覆盖额外文件。
- source/mono_delivery.py verify：两段各 48000 样本 PASS，BIN/FNV/ID/CSV/WAV 一致。
- source/test_delivery.py：10/10 PASS。
- publication/mono_closeout_20260910/all-files-manifest.json：21 项 SHA-256 全部匹配。
- 所有命令使用 Python -B；本次没有重跑历史低频分析、综合实现或 B 完整读取器回归。

以上是 A 上传前自检，不是 B 复核批准，更不是单麦完整板级或四路 H2 验收。
