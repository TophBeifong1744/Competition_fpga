# #15 户外八段四路采录：本地待审数据包

本包只对应 C/hsc119 提供的 `sound_otd` 八段户外原件。`sound_09_22` 单独保留，未混入本包。原始 BIN/UART 由 C 提供；本包的 CSV、试听 WAV、索引和离线检查由 E 工程助手生成，均待 B 独立复核。未修改板卡、实际 Vivado/Vitis 工程或旧录音证据。

## 输入身份与结论范围

- 八段均有一对原始 BIN/UART，原文件名记录在 `capture-index.json`；复制后的 SHA-256 与桌面原件逐项相同。每段 9,224,000 B、288,250 组，按配置 48 kHz 为 6.005208 秒。八段均通过原 S1 BIN/UART 逐字段完整性检查和 B 的 H1 读取器 `PASS_FORMAT_ONLY`。这些结果不构成声学或成员验收。
- 用户提供的 `soundsight-target-v1(1).wav` 与仓库冻结 `playback-v1/soundsight-target-v1.wav` 哈希相同：`ce28c5576eea620d8f358c0799bf8029cdc41bdeae8dcf95a02967d3bace6838`。用户保证 WAV 正确；手机端实际文件哈希和内部处理未独立核验。详见 `playback-identity.json`。
- 用户事后报告：户外使用华为荣耀9、微信播放、最大音量、无特殊音效设置；每个位置两次录音间未移动；背景段暂停播放，但户外可能有人讲话。该报告不是同步现场日志。详见 `operator-report.json`。
- 六个目标段的四路均得到首尾标记的**候选**匹配；`az045_r1_otd` 的四路两点映射都推算源文件终点超过抓取终点约 949–964 样本（约 20 ms）。尾标记本身位于抓取中，仍须人工复核波形和试听；不能声称六段均完整容纳 4.8 秒源文件。其余五个目标段候选映射显示源文件位于抓取内。标记位置不是精确声学活动真值。
- 用户事后报告三处阵列中心到声孔均约 1.5 m（尺量）、相对计划位置无明显偏移、0°沿 +X、高差在 5 cm 内，未拍照片；尺的最小刻度、三处 x/y/z 双读数和角度误差未提供。名义 0°/±45°不能写成实测方向。`positions.json` 保留未知。现场 Run/加载绑定亦待补，见 `version-binding.json`。

## 文件与处理

- `captures/<原文件名词干>/raw.bin` 和 `serial.log`：C 提供的原始字节，未改 PCM、流内 sample ID、flags 或日志；metadata 的 `acquisition_id` 增加 `c15_outdoor01_` 前缀，避免与旧批次撞名。
- 同目录 `samples.csv`、`metadata.json`：调用仓库 `source/export_four.py` 从原始 BIN 导出；坐标仍为未知，不能驱动方向评分。
- 同目录 `mic0.wav` 至 `mic3.wav`、`listening.json`：全批统一 `round-even(PCM24 × 12 / 256)` 转 48 kHz signed16，回读逐字节一致且无新增削顶；未去直流、滤波、AGC 或逐段归一化。**人耳试听尚未完成**。
- `evidence/h1-reader-current/*.json`：当前唯一批次 ID 的每段仓库读取器原始 stdout；相邻 `.stderr.txt` 为原始 stderr。早期 `h1-reader/`、`h1-reader-final/` 与 `offline-01/02/final.json` 保留处理过程身份，当前索引使用 `evidence/offline-current.json`，其中有原 S1 与标记函数的逐段结果、源码哈希、候选映射及限制。`capture-index.json` 按文件修改时间列出顺序；修改时间不是已证实的采集时间。

离线 S1/标记复核命令（在仓库根目录，输出必须选新的文件名）：

```powershell
python -B task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/measured-direction-outdoor-01/verify_batch.py --out task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/measured-direction-outdoor-01/evidence/offline-recheck.json
```

预期输出为 8 个逐段检查记录及总体 `INTEGRITY_PASS_SOURCE_COVERAGE_EXCEPTION`；它是诊断级别，不会操作板卡。原 `finish_scene.py` 直接 import 仍指向搬迁前的 `docs/team-workflow.md`，因此此脚本从原文件 AST 只编译所需函数体，未修改原函数。B 可独立检查这些函数及源码哈希，或用自己的入口复验。H1 读取器单段命令例如：

```powershell
python -B task-packages/PKG-B-ALG/payload/model/python/h1_reader.py task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/measured-direction-outdoor-01/captures/az000_r1_otd
```

输出 `PASS_FORMAT_ONLY` 只证明 H1 格式。后续由 C 补齐可追溯现场事实和异常试听，A 核对实际获批加载入口，B 独立诊断完整时间线与两次重复；真实成员批准前不声称 #15 完成。若无法补齐三处实测坐标，保留本包作为户外开发输入，不作为“测量摆位”验收或精度真值。失败与缺项不筛除、不覆写原件。
