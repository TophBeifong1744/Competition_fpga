# PKG-B-ALG 文件清单与合入边界

当前开发版本：robustness-sweep-0.1，新增固定候选的新噪声、方向及合成混响适用范围检查；原定位、5/12捕获、旧结果不变。精确文件SHA-256见evidence/package-files.json，固定参照另见reference/batch-presence-fixed/、reference/candidate-quality-fixed/和reference/robustness-fixed/。清单不包含自身，排除解释器缓存。

本轮新增payload/model/python/robustness_sweep.py、payload/config/robustness-sweep.json、payload/tb/python/test_robustness_sweep.py、payload/docs/robustness-sweep.md，预期将来分别置于总工程对应model/config/tb/docs位置，当前均未合入。audit_robustness.py、report_robustness.py、reference/robustness-fixed/与evidence/robustness-*保留包级；工具依赖包布局，正式移入前需由A调整定位并复验。

| 包内文件 | 预期总工程位置 | 动作 |
|---|---|---|
| payload/model/python/h1_reader.py | model/python/h1_reader.py | 将来新增，当前未合入 |
| payload/model/python/audio_frames.py | model/python/audio_frames.py | 将来新增，当前未合入 |
| payload/model/python/six_mic_baseline_core.py | model/python/six_mic_baseline_core.py | 旧模型摘录；将来新增，当前未合入 |
| payload/model/python/six_mic_localize.py | model/python/six_mic_localize.py | 离线定位入口；将来新增，当前未合入 |
| payload/model/python/sector_tracker.py | model/python/sector_tracker.py | 历史跟踪器复制；将来新增 |
| payload/model/python/six_mic_track.py | model/python/six_mic_track.py | 跟踪运行入口；将来新增 |
| payload/model/python/batch_presence.py | model/python/batch_presence.py | 连续合成批次、标注与配对评价；将来新增 |
| payload/model/python/quorum_tracker.py | model/python/quorum_tracker.py | 独立研究候选；不自动替换默认tracker |
| payload/model/python/weighted_gcc.py | model/python/weighted_gcc.py | 独立GCC研究候选；将来新增 |
| payload/model/python/candidate_quality_research.py | model/python/candidate_quality_research.py | 研究工具；集成须调整包根定位 |
| payload/config/candidate-quality-protocol.json | config/candidate-quality-protocol.json | 固定研究协议；将来新增 |
| payload/tb/python/test_weighted_gcc.py | tb/python/test_weighted_gcc.py | 新GCC候选测试；将来新增 |
| payload/docs/candidate-quality-research.md | docs/candidate-quality-research.md | 研究说明；将来新增 |
| reference/candidate-quality-fixed/ | 包级固定参照 | 原位文件哈希，不改原实现 |
| audit_candidate_quality.py | 包级独立审计工具 | 依赖audit_capture_research的文件读取辅助函数 |
| payload/model/python/capture_research.py | model/python/capture_research.py | 包布局下研究工具；集成须调整根目录定位 |
| payload/config/capture-research-protocol.json | config/capture-research-protocol.json | 冻结开发/验证方案；将来新增 |
| payload/tb/python/test_quorum_tracker.py | tb/python/test_quorum_tracker.py | 独立候选测试；将来新增 |
| payload/docs/capture-noise-research.md | docs/capture-noise-research.md | 研究说明；将来新增 |
| reference/batch-presence-fixed/ | 包级固定参照 | 原位保存文件，以哈希验证未改变 |
| audit_capture_research.py | 包级独立审计工具 | 按包内固定开发/验证目录复核 |
| payload/config/batch-presence.json | config/batch-presence.json | 冻结实验计划；将来新增 |
| payload/tb/python/test_batch_presence.py | tb/python/test_batch_presence.py | A 集成时调整包级路径并复验 |
| payload/docs/batch-presence-evaluation.md | docs/batch-presence-evaluation.md | 实验与标注说明；将来新增 |
| audit_batch_presence.py | 包级审计工具 | 独立复算落盘结果；保留任务包内 |
| payload/config/sector-tracking.json | config/sector-tracking.json | 默认范围与状态阈值；将来新增 |
| payload/tb/python/test_sector_tracker.py、test_six_mic_track.py | tb/python/ 同名文件 | A 集成时调整 reference 路径并复验 |
| payload/docs/sector-tracking-entry.md | docs/sector-tracking-entry.md | 跟踪操作说明；将来新增 |
| reference/sector-lock-v0.1/ | 包级历史证据 | 保留旧规则、失败结论与来源 |
| payload/tb/python/test_six_mic_localize.py | tb/python/test_six_mic_localize.py | A 集成时调整 reference 定位并复验 |
| payload/docs/six-mic-baseline-entry.md | docs/six-mic-baseline-entry.md | 将来新增的操作与输出约定 |
| reference/six-mic-baseline/ | 包级旧模型证据 | 不覆盖旧模型或 A 的接口 |
| run_baseline_regression.py | 包级验证工具 | 依赖包内测试 oracle，保留在包内 |
| payload/tb/python/test_audio_frames.py | tb/python/test_audio_frames.py | 包内运行；集成时由 A 调整包级样例/脚本定位并复验 |
| payload/docs/framing-and-input-adapters.md | docs/framing-and-input-adapters.md | 将来新增的接口与开发教程，当前未合入 |
| run_framing_demo.py | 包级教学复现工具 | 保留在任务包，不写入真实采集目录 |
| payload/docs/h1-reader.md | docs/h1-reader.md | 将来新增，当前未合入 |
| payload/tb/python/test_h1_reader.py | tb/python/test_h1_reader.py | 待整体包集成时由A调整样例定位并复验；当前在包内运行 |
| run_validation.py | 包级复现工具 | 保留在任务包，使用reference原始样例 |
| reference/h1-ss-data-draft-0.3/ | 原始交接只读参考 | 不覆盖A包或总工程接口 |
| evidence/ | 实际验证、诊断和哈希 | 保留在任务包，不充当硬件结果 |
| README.md、REVIEW.md、manifest.md、requirements.txt | 包级说明 | 保留在任务包 |

测试目前按独立包布局定位reference。正式移入总工程后须由复核人选定样例位置、修改定位并重新验证；不能直接复制后宣称仍已通过。读取器本身不依赖总工程或reference路径，独立输入两个文件即可运行。

本轮没有删除、替换总工程文件或更新活动台账；没有Git提交、远端推送或合并。复核人为拓芙（A），只有其确认准确版本并决定范围后负责正式合入。
