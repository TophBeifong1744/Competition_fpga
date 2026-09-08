# PKG-B-ALG：成员 B 完整算法包

最新增量：`robustness-sweep-0.1` 已完成4种噪声×4方向×3种合成传播条件、3个新种子的144次配对检查，167项测试及独立复算通过。详见 [适用范围报告](evidence/robustness-report.md) 和 [复核/复现说明](payload/docs/robustness-sweep.md)。单频噪声边缘方向有明确退步，β=.75继续保留为研究候选；默认算法不变，尚未取得A本轮批准。

负责人：BryanZheng802（成员 B）。指定复核及合入人：拓芙（成员 A）。当前状态：包内持续开发；已完成读取/分帧、定位/跟踪、整批标注对照、5/12捕获研究，以及GCC候选质量的新种子验证。β=0.75与5/12均为独立研究候选，原算法仍为默认；完整包尚未达到H3条件。

采用接口：`ss-data-draft-0.3`。A 交接提交 `5f0dc36fce2328ade672dd949778bc5a91f506dc`，清单 SHA-256 为 `ef09838face445cc4f2a87d56245ad64574fa3e9f4d12032e4b0723a7f1eca96`。原始参考副本按字节保存于 reference/，读取器实现没有修改 A 的样例或测试预期。

## 本轮成果和运行

依赖：Python 3.12.14、NumPy 2.3.5。本机已用现成环境完成验证；其他机器使用已配置解释器或按 requirements.txt 准备 NumPy。无硬件、MATLAB、Vivado 或 Pillow 依赖。

在本包根目录运行：

```powershell
python -B payload/model/python/h1_reader.py reference/h1-ss-data-draft-0.3/payload/examples/h1/code-pattern reference/h1-ss-data-draft-0.3/payload/examples/h1/restart
python -B run_validation.py --out evidence/reviewer-reader-run
python -B run_framing_demo.py --out evidence/reviewer-framing-demo
python -B payload/model/python/six_mic_localize.py --demo clean --out evidence/reviewer-baseline-clean
python -B run_baseline_regression.py --out evidence/reviewer-baseline-regression
python -B payload/model/python/six_mic_track.py --demo stable --config payload/config/sector-tracking.json --out evidence/reviewer-tracking-stable
python -B payload/model/python/batch_presence.py --plan payload/config/batch-presence.json --config payload/config/sector-tracking.json --out evidence/reviewer-batch-presence
```

第一条输出 H1 诊断；第二条执行当前完整回归；第三条运行四通道固定码型分帧教学；第四条运行六麦离线定位；第五条记录新旧同帧对照和轴向 golden；第六条运行范围与跟踪；第七条执行5场景×10种子的整批对照。结果写入新目录。六麦入口与对照工具要求目录尚不存在。本机若 `python` 不是所需环境，应替换为可用 Python 完整路径。最新步骤见 payload/docs/batch-presence-evaluation.md。

| 路径 | 用途 |
|---|---|
| payload/model/python/h1_reader.py | 未来目标路径 model/python/h1_reader.py；当前只在包内运行 |
| payload/model/python/audio_frames.py | 四通道 H1 和六麦浮点独立适配、1024/512 分帧及六麦入口守卫 |
| payload/model/python/six_mic_baseline_core.py | 旧六麦数值代码原文摘录，NumPy 依赖 |
| payload/model/python/six_mic_localize.py | 六麦离线输入、定位、统计、运行入口 |
| payload/model/python/sector_tracker.py | 旧跟踪器按字节复制，冻结原规则 |
| payload/model/python/six_mic_track.py | 跟踪接入、配置、连续示例和运行入口 |
| payload/model/python/batch_presence.py | 连续多种子生成、目标存在标注、三方法配对与统计 |
| payload/model/python/quorum_tracker.py | 独立5/12捕获变体，不替换原tracker |
| payload/model/python/weighted_gcc.py | 独立部分白化GCC，选定β=0.75，不替换原PHAT |
| payload/model/python/candidate_quality_research.py | 候选质量开发/验证、原始及捕获后配对 |
| payload/config/candidate-quality-protocol.json | 新种子隔离、两个指数候选及预定判据 |
| payload/tb/python/test_weighted_gcc.py | β=1一致性、符号/缩放/静音及真值隔离 |
| payload/docs/candidate-quality-research.md | 最新候选质量操作与解释 |
| reference/candidate-quality-fixed/files.json | 前一捕获研究及基础算法固定哈希 |
| evidence/candidate-development-01/、candidate-heldout-01/ | 选定前开发和选定后新种子验证 |
| evidence/candidate-tests-final/ | 当前161项完整回归 |
| audit_candidate_quality.py、evidence/candidate-quality-audit.json | 独立统计/标注/质量门和来源审计 |
| evidence/candidate-quality-report.md | 本轮改善、退步与适用范围 |
| payload/model/python/capture_research.py | 开发集方案选择与新种子验证 |
| payload/config/capture-research-protocol.json | 预先固定的两候选、种子拆分及判据 |
| payload/tb/python/test_quorum_tracker.py | 票窗口/时限、重置与旧锁定语义测试 |
| payload/docs/capture-noise-research.md | 最新研究方法、运行和限制 |
| reference/batch-presence-fixed/frozen-files.json | 139个固定参照文件哈希，前后保持一致 |
| evidence/capture-development-01/ | 开发候选对照和冻结selection.json |
| evidence/capture-heldout-01/ | 10个未参与选择的新种子、五场景验证 |
| evidence/capture-tests-final/ | 上一捕获阶段151项历史回归 |
| audit_capture_research.py、evidence/capture-research-audit.json | 独立复算、来源/分母/种子隔离审计 |
| evidence/capture-research-report.md | 新旧同验证集结果及后续依据 |
| payload/config/batch-presence.json | 预先固定的场景、种子和目标时间表 |
| payload/tb/python/test_batch_presence.py | 标注、统计、无真值泄漏和批次复现测试 |
| payload/docs/batch-presence-evaluation.md | 最新整批运行、统计和标注说明 |
| audit_batch_presence.py | 独立从落盘结果复算标注、角度、分母、配对与延迟 |
| evidence/batch-validation-final/ | 固定批次阶段的139项历史回归 |
| evidence/batch-presence-run-01/、batch-presence-run-02/ | 两次整批运行，65个生成文件按字节一致 |
| evidence/batch-presence-audit-final.json | 独立审计结论 |
| evidence/batch-presence-report.md | 本轮整批结果及开发依据 |
| payload/config/sector-tracking.json | 用户选定策略的默认参数 |
| payload/tb/python/test_sector_tracker.py、test_six_mic_track.py | 原规则及集成测试 |
| payload/docs/sector-tracking-entry.md | 最新跟踪操作说明 |
| reference/sector-lock-v0.1/ | 历史来源、策略、报告和测试快照 |
| evidence/tracking-validation-final/ | 历史跟踪接入回归，128 项通过 |
| evidence/tracking-demo-*-final/ | 五类连续教学输入、输出和追溯记录 |
| evidence/tracking-entry-report.md | 本轮结果、已知失败与限制 |
| payload/tb/python/test_six_mic_localize.py | 新旧一致性、符号与边界回归 |
| payload/docs/six-mic-baseline-entry.md | 最新定位操作教程与输出约定 |
| reference/six-mic-baseline/ | 原始完整代码按字节快照与提取记录 |
| run_baseline_regression.py | 同帧对照及轴向 golden 复现工具 |
| evidence/baseline-validation-final/ | 历史基线接入回归，94 项通过 |
| evidence/baseline-regression-final/ | 当前 162 帧对照、六轴理想时差和波形 golden |
| evidence/baseline-demo-*-final/ | 当前四类演示的输入、逐帧输出和统计 |
| evidence/baseline-entry-report.md | 接入结论和限制 |
| payload/tb/python/test_audio_frames.py | 分帧、适配与教学程序回归测试 |
| payload/docs/framing-and-input-adapters.md | 开发边界、接口和手把手运行教程 |
| run_framing_demo.py | 无硬件教学例子，保留输入与分帧 JSON |
| evidence/framing-validation-final/ | 历史分帧版本回归结果 |
| evidence/framing-demo-01/ | 实际教学输入和四帧输出证据 |
| evidence/framing-report.md | 本次开发的结论与限制 |
| payload/tb/python/test_h1_reader.py | 读取器行为测试；使用包内 A 的只读样例副本 |
| payload/docs/h1-reader.md | 输入、返回数据、异常与限制说明 |
| run_validation.py | 按 A 的 15 项计划映射真实测试结果并记录源码哈希 |
| reference/h1-ss-data-draft-0.3/ | A 的原始接口、样例、预期和历史交接状态副本 |
| evidence/reader-validation-final/ | 历史读取器版本验证结果 |
| evidence/reader-report.md | 成果说明、已验证内容及剩余事项 |
| manifest.md / evidence/package-files.json | 文件目标、职责、精确版本与哈希 |
| REVIEW.md | A 的完整包复核记录；当前未批准、未合入 |

H1 读取器错误输入返回退出码 2、stderr 结构化错误，包含字段与 CSV 物理行号；成功状态为 PASS_FORMAT_ONLY。六麦入口处理完成状态为 COMPLETE_SYNTHETIC_ONLY，即使全部帧无效也可能正常完成；错误返回 2。既有输入文件只读；--demo 在新输出目录内生成自己的合成输入。

## 后续工作在同包内继续

原定位候选质量已完成新种子研究，结果见evidence/candidate-quality-report.md，运行见payload/docs/candidate-quality-research.md。β=0.75在噪声下改善，但同锥竞争者的一项准确率退步；后续应测试更广噪声/方向/混响条件，并补音频对照与定点准备。包内实验不逐次等待签字。H1 0.3及原默认算法保持不变。

旧 SIM6-001 复核和 SIM6-002-01 独立实验的成果不作废，原结果保留在原交付位置。基线源码与跟踪器来源已分别登记到 reference/six-mic-baseline/ 和 reference/sector-lock-v0.1/，后者包含原策略及失败报告副本；不将历史实验当作已通过 H3。

按三交接点安排，读取器可在 H1 签署记录补齐期间连续开发；测试通过不是代签双方确认。H2 尚无真实诊断录音，H3 尚未批准。形成完整算法版本后交 A 复核，只有复核人对准确版本确认后负责合入。本文列出的目标路径不是当前合入动作。
