# #15 C 录音本地交接：室内与户外两批分列

2026-09-28 整理 C/hsc119 提供的两个原始文件夹：`sound_09_22` 为用户确认的室内八段，`sound_otd` 为户外八段，用户称同日录制。文件系统修改时间只作来源线索，不当采集时钟。两批使用用户确认的相同带标记 WAV；提供的文件与仓库冻结播放 WAV SHA-256 同为 `ce28c5576eea620d8f358c0799bf8029cdc41bdeae8dcf95a02967d3bace6838`。历史错素材证据不被本次重标或覆盖。

| 批次 | 本地入口 | 原始/格式 | 目标播放覆盖例外 |
| --- | --- | --- | --- |
| 户外 | [measured-direction-outdoor-01](measured-direction-outdoor-01/README.md) | 8/8 BIN＋UART 原样保留；S1 完整性和 H1 `PASS_FORMAT_ONLY` 均 8/8 | `az045_r1_otd` 两点映射估计源文件尾部超出抓取约 20 ms；尾标记在抓取内 |
| 室内 | [measured-direction-indoor-01](measured-direction-indoor-01/README.md) | 8/8 BIN＋UART 原样保留；S1 完整性和 H1 `PASS_FORMAT_ONLY` 均 8/8 | `az000_r1` 尾标记无法可靠匹配，素材未完整；`az045_r1` 估计源文件尾部超出抓取约 30 ms |

两批各有 `capture-index.json`、`positions.json`、`operator-report.json`、`playback-identity.json`、`version-binding.json`、逐段 metadata/CSV/统一增益 WAV、H1 stdout/stderr 和 `evidence/offline-current.json`。原始 BIN/LOG 及失败段始终保留，未用重复段补数。C 事后报告三处距离均约 1.5 m（尺量）、0°沿 +X、高差在 5 cm 内、两次重复不移动、未拍照片；x/y/z 双读数、角度误差与尺最小刻度缺失。户外背景可能有人声，室内报告无人讲话。试听 WAV 已无新增削顶且回读一致，人耳试听尚未完成。

C 另提供三张 Vitis 2025.2 截图，并确认室内与户外两批当时实际运行同一个 `vitis-capture-import_app_hw_1`，ELF/bit 自录音以来未变。[Vitis 配置补证](c-issue15-vitis-config-20260928/README.md)保留原截图、当前 `launch.json` 和当前文件哈希；ELF/bit 哈希与历史候选记录吻合。这是操作人事后确认并由当前配置佐证，缺采集当时自动 Run 日志、加载前检查和板上读回。

本批只申请**开发诊断输入的独立复核**，不得将 16/16 格式通过写成 #15 八段播放完整、测量摆位精度、声学效果、M1/H3 或真人 B 批准。A 仍需核对所报 Run/bit/ELF 是否为获批加载入口；C 如有替代原件或重录，以新 ID 补交并保留本次失败原件。B 按两批准确哈希、原始异常与现场误差独立诊断。AI 整理与自检不代替真人非作者批准；本文件不改变 Issue #15 的状态。
