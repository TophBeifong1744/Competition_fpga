# 今日录音归档发布入口：连续讲话素材，非约定带标记试验

用户于2026-09-22确认：C使用错播放素材，使用了连续读六秒的讲话音频，没有使用约定带首尾标记WAV。用户明确授权将今天录音同步到远端。本批只作开发诊断，保留错误素材事实；不冒充明天正确素材的新批次，不删除今天原件。

## 原始输入

input/sound_09_22.zip为用户提供ZIP原字节副本，21589520字节，SHA256：
965095987f65e229319487fffa5abb77dbcb40ec885a564489e4ec14b4bbc6d4

压缩包内8 BIN＋8 UART LOG，未重新编码或改名。back_od为录前背景，az045为azp045，映射来自用户确认。阵列、通道顺序和采集配置未变也是用户确认；实测位置/误差、照片、metadata及准确加载哈希仍缺，不补造。

## 如何理解现有结果

- REVIEW.md：收件时原始完整性检查，8/8通过；其“待补资料”按后续用户允许诊断使用的范围理解，不视为精密摆位通过。
- USER-UPDATE-AND-DIAGNOSIS.md：用户配置确认后全4488帧开发诊断；新背景门下五个目标段有fresh，+45第二段0fresh。166是输出帧数，不是166次独立锁定或已知正确语音帧。
- ALIGNMENT-STATUS.md：旧模板24路全部UNRESOLVED是真实保留结果。现在已知素材不同，不再要求用旧chirp强行对齐；不沿旧时间表划正文。
- 连续讲话音频仍不提供精确实际活动边界、无间断声学真值或阵列干净参考。用错素材解释标记不匹配，不足以唯一解释方向不稳。未测试新正确素材，不保证重录必然成功。

## 复现（仓库根，输出目录须全新）

```powershell
python -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/c-recording-receipt-20260922/verify_zip.py --repo . --zip task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/c-recording-receipt-20260922/input/sound_09_22.zip --out F:/NUEC/validation/c-sound-published-receipt
python -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/c-recording-receipt-20260922/diagnose.py --repo . --zip task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/c-recording-receipt-20260922/input/sound_09_22.zip --out F:/NUEC/validation/c-sound-published-diagnostic
```

Python3.12.14/NumPy2.3.5；必要时只替换输出为本机可写的新目录。原运行记录保持，原始ZIP副本只作哈希核对，不因搬迁重复全部研究。

## 发布范围和下一步

本次推送B任务分支，包含本批原始ZIP、源码、输入验收、全帧诊断及失败记录；尚未由A复核本次新诊断，不自行合入main。前批e473824批准不能覆盖本批。

明天正确素材需使用新批次：先准确核对源文件并确认首段标记/正文完整，再完成新八段。今天文件不重命名为正确素材输入，不替代正式精度、音频收益或完整H3证据。
