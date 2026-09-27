# #15 室内八段四路采录：本地待审数据包

本包只对应 C/hsc119 提供的 `sound_09_22` 室内八段，同日录制但与 `sound_otd` 户外批次分开保存。此文件夹名不是历史 9/22 错素材批次的身份判定；本包依本次原始文件、用户确认和哈希单独登记。原始 BIN/UART 由 C 提供；CSV、试听 WAV、索引与诊断由 E 工程助手生成，待 B 独立复核。未修改板卡、实际 Vivado/Vitis 工程或旧证据。

## 输入身份与结论范围

- 八段均有一对 BIN/UART，复制后的 SHA-256 与桌面原件逐项相同。每段 9,224,000 B、288,250 组，按配置 48 kHz 为 6.005208 秒；八段均通过原 S1 BIN/UART 逐字段完整性检查和 H1 读取器 `PASS_FORMAT_ONLY`。这只证明原始格式和日志配对。
- 用户确认室内批次也用华为荣耀9、微信、最大音量、无特殊音效设置播放同一带首尾标记的 WAV；每个位置两次录音间不移动、背景段暂停播放，室内背景无人员讲话。手机端文件哈希和内部处理未独立核验。提供的 `soundsight-target-v1(1).wav` 与仓库冻结源的 SHA-256 都是 `ce28c5576eea620d8f358c0799bf8029cdc41bdeae8dcf95a02967d3bace6838`。
- `az000_r1` 的四路起始标记候选约在第 97,650 样本，尾标记无法可靠匹配；约 2.03 秒才见起始标记，按源 4.25 秒标记间隔推算尾标记会落在六秒抓取之后。**该段目标素材完整性未通过**，不能拿其标记/正文做完整时间线评价，也不能用另一段替代。
- `az045_r1` 四路首尾标记有候选，但两点映射推算源文件终点超过抓取终点约 1,418–1,426 样本（约 30 ms）。尾标记本身仍位于抓取中；须人工复核波形和试听。其余四个目标段候选映射显示源文件位于抓取内。标记结果都不是精确声学边界。
- 用户事后报告三处阵列中心到声孔均约 1.5 m（尺量）、相对计划位置无明显偏移、0°沿 +X、高差在 5 cm 内，未拍照片；尺最小刻度、三处 x/y/z 双读数和角度误差未提供。`positions.json` 保留未知，名义角不能作为测量真值。实际 Run/加载身份亦待补，见 `version-binding.json`。

## 文件与复验

- `captures/<原文件名词干>/raw.bin`、`serial.log` 为 C 提供的原始字节；`samples.csv`、`metadata.json` 是仓库 `source/export_four.py` 的无滤波导出。metadata 的 `acquisition_id` 增加 `c15_indoor01_` 前缀，避免与旧批次撞名；坐标为未知，H1 读取器禁止方向评分。
- 同目录 `mic0.wav` 至 `mic3.wav` 统一 `round-even(PCM24 × 12 / 256)` 转 48 kHz signed16，全批无新增削顶且回读逐字节一致；未去直流、滤波、AGC 或逐段归一化。`listening.json` 记录转换，人耳试听仍为 `NOT_RUN`。
- `capture-index.json` 逐项绑定原文件名、哈希、派生路径和检查状态；文件修改时间只供来源排序，不冒充真实采集时钟。`evidence/h1-reader-current/` 保留当前唯一批次 ID 的每段原始 stdout/stderr；早期 `h1-reader/`、`h1-reader-final/` 与 `offline-01/final.json` 保留处理过程身份，当前索引使用 `evidence/offline-current.json`，其中有原 S1 与标记函数的检查结果及源码哈希。

在仓库根目录复验时选新的输出文件名：

```powershell
python -B task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/measured-direction-outdoor-01/verify_batch.py --batch-root task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/measured-direction-indoor-01 --out task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/measured-direction-indoor-01/evidence/offline-recheck.json
```

预期输出为八段逐字段结果与 `INTEGRITY_PASS_MARKER_UNRESOLVED`；它不操作板卡。单段 H1 复验例如：

```powershell
python -B task-packages/PKG-B-ALG/payload/model/python/h1_reader.py task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/measured-direction-indoor-01/captures/az000_r1
```

下一步由 C 对不完整段给出现场说明/可用重录及试听记录，A 核对获批加载入口，B 独立诊断完整时间线与同摆位重复。若无重录，保留失败原件和缺项，不把室内八段计为八段完整素材；真实成员批准前不声称 #15 完成或精度、SNR、H3/M1 通过。
