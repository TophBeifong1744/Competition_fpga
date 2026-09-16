# 四路实录 → 诊断候选 → 范围跟踪入口

2026-09-15，B 作者实现与自测，待完整包交 A 复核，未合入 main。本任务属于 9/18 算法包的四路跟踪增量；沿已批准的单麦／手动对照继续，不重做音频人工试听，不改变默认 PHAT、跟踪器、reference25 或 A/C 原件。

基线为已发布 `8371f014711e04553749e6c2ffc29f34b9d5ccc9`，任务分支 `task/member-b-four-track-01`，实际工程目录 `F:/NUEC/develop`。开始时本地 main 另有其他任务的清理收据提交 `9936613e99a5ac4c2d080375697d8447f5f377fc`；完整保留在 main，本任务从 origin/main 建分支，不夹带该未发布提交，也未新建仓库副本。

## 这一步做了什么

`run.py` 复用 H1 读取器和分帧器、`c-board-algorithm-01/run.py` 的浮点相关峰／合法 lag／平面投影，以及 `sector_tracker.py` 的原规则。新代码只接入口、保存逐帧候选及拒绝原因，并给未来自动音频提供诊断路由。没有调用六麦声学模拟、AMD FFT DLL 或本轮定点链。

流程为：原始四路 PCM → 每帧 1024 点／hop 512 → 六对浮点 GCC-PHAT 与投影 → 数值一致性候选 → 允许范围与跟踪 → 诊断音频路由信息。

- 复用原条件：频点 7～85、相对幅度 2%、至少 12 点；合法 lag 沿用 +0.05 样点容差；至少 3 个合法对、二维秩 2、残差 ≤0.5 样点、投影模长 0.1～1.3。
- 原跟踪配置：+X 为中心、半角 30°，连续 5 帧、捕获角差 ≤8°，跟踪步进 ≤20°，HOLD 200 ms，输入间隔 >30 ms 重置。没有为了本批计数改阈值。
- 平面投影仅在**显式水平假设**下映射成 `[cos az, sin az, 0]`。这不是完整三维方向恢复。`numeric_candidate_valid` 与 `tracker.fresh_valid` 均不是目标存在、说话人身份或验收结论；`target_presence=unknown`、`direction_accepted=false` 始终保留。
- SEARCH／ACQUIRE 用 mic0；LOCKED 可供诊断跟踪指向；HOLD 暂用旧方向，`fresh_valid=false`。未来音频须按 `valid_through_ms` 到期回单麦，不能等下一帧才处理过期。

## 本机结果

`evidence/run01/` 保存真实命令、原始 stdout/stderr、21 项新测试、18 项原跟踪回归、24 项原分帧回归及两段实录逐帧结果。合计 **63 项测试通过**。环境：Windows 11 10.0.26200、CPython 3.12.14、NumPy 2.3.5，AMD64；未做跨 CPU 或实板测试。

| 实录（每段 61 帧） | 数值一致候选 | SEARCH | ACQUIRE | LOCKED／新鲜帧 | HOLD |
| --- | ---: | ---: | ---: | ---: | ---: |
| 阵列中心 +X、约 1.5 m | 36 | 14 | 8 | 21 | 18 |
| 旧 quiet | 35 | 61 | 0 | 0 | 0 |

两段各 32000 行；61 个重叠帧覆盖 31744 个不同样本，尾部 256 行不参与定位分析。帧计数不是独立试验次数，也不是最终音频各路占用时长。

中心录音首次锁定出现在录音起点后 **256 ms**，不是从已知发声起点测得的捕获延迟。25 帧投影未过数值门；另有 4 帧在范围外、3 帧跟踪跳变。数值一致候选角度覆盖约 −166.01°～110.22°，保留全部未锁定与拒绝记录，不挑选好帧。HOLD 的 18 帧不计为新鲜定位正确。

quiet 的 35 个一致候选约为 −139.12°～−73.38°，全在本次 +X 范围外，所以没有锁定；其 366 个麦对都产生合法时延。**这说明数值一致性不能替代目标存在门**，并不能证明在其他允许范围也不会误锁。quiet 与中心录音是不同批次，不当作同场景配对噪声。

`evidence/run02/` 是添加交付验证器后的再次实录回放；未改算法或阈值，也未重跑整套历史研究。`repeat-comparison.log` 逐值核对 4,580 个浮点值（本机最大差 0）和 8,972 个离散值全部一致；两份逐帧 JSON 字节一致，summary 因耗时及新增验证器来源记录而字节不同。不是跨机器独立复核。原投影的 `UNCALIBRATED_NEARFIELD_NO_TRUTH` reason 标签原样保留，只表达该旧诊断未作正式方向批准，不据此判定本次 1.5 m 为近场。

输入严格绑定已有历史清单中的 CSV、metadata、几何和接收依据，并绑定全部复用算法依赖，共 20 个 SHA-256，见 `pins.json`。新中心输入批准版本 `f9768b80e5718dcf29baf48015305780f4b9b8e8`。运行前后分别核对；没有重新生成录音或修改旧清单。本任务没有生成新的 WAV。

## 如何复现

在干净检出的项目根目录运行，需 Python 3.12 与 NumPy 2.3.5：

```powershell
Set-Location F:\NUEC\develop
python -B task-packages/PKG-B-ALG/tasks/four-channel-track-01/verify.py
python -B task-packages/PKG-B-ALG/tasks/four-channel-track-01/reproduce.py --out ..\review-evidence\four-track-rerun01
python -B task-packages/PKG-B-ALG/tasks/four-channel-track-01/verify.py --compare ..\review-evidence\four-track-rerun01\replay
```

这里 `python` 指向包含 NumPy 的解释器；B 本机用 `C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`，准确实跑命令见 `evidence/run01/commands.json`。已有输出目录会报错，不覆盖原证据；复跑换一个新输出目录。建议复跑目录放在任务包外，包内完整文件集合也会参与核对。

只跑实录可用：

```powershell
python -B task-packages/PKG-B-ALG/tasks/four-channel-track-01/run.py --out ..\review-evidence\four-track-real-only01
```

`verify.py --compare` 对全部逐帧值、拒绝／状态／路由及录音摘要做比较：离散值与原输入／源码哈希严格一致；浮点预设 atol/rtol=1e-10，超差报错。同时单独报告 JSON 文件字节是否一致。summary 的环境、运行耗时及检出 SHA 可不同，不以“字节不同”自动推断算法失败，也不把最终计数一致当作完整复现。

## 自动音频接入时怎样用

`tracking.py:DiagnosticSession` 接收投影结果和**帧末可用时间**，不接收录音标签、实际声源位置或人工方向。新录音新建 session；每个 clean interval 开始立即 `begin_interval(index)`，即使该段不足一帧也重置；未来消费者不能跨缺样／错误行延续旧方向。

`route_at(t, interval_index=...)` 按最后已处理结果查询。t 早于该帧到齐时间时回单麦；超过最后新鲜方向 +200 ms 时回单麦，即使再没有输入事件。有效截止含端点，沿用原 Tracker 的 `age > hold_ms` 规则。查询不会刷新寿命；只用于顺序处理，历史渲染必须按时间顺序回放事件。

这里的帧末时刻采用样本编号时钟、零计算延迟的离线假设；实际部署还需加处理完成与调度延迟，不能作为实时性能证据。下一步在**同一任务包**接入自动 DAS：保留共同时间对齐、允许范围、HOLD 到期与平滑切换，输出同录音单麦／手动／自动三路供 B 试听。不能用后来得到的方向倒指向这帧过去的音频。

## 未完成及批准边界

本轮只完成四路候选跟踪和未来音频路由合同的作者自测。目标存在门、自动 WAV／DAS 平滑过渡、准确定位误差／错向率、音频收益、完整定点／golden、资源时序和 H3 仍未完成。缺乏准确真值的指标保持 null。

后续需要 A 汇总提供声学输入：同配置、同场景较长的背景与目标交替录音，目标开始／停止区间、阵列中心方向参考及误差范围，沿用几何／通道映射；若要声学收益指标，还需约定可验证的参考与评价方法。这是尚缺输入清单，未通过工具发送给 A，不给 C 追加任务。现有记录继续用于软件生命周期与三路试听诊断，不等待新输入才开发。

普通离线增量不逐项等待 A 审批；下一步可继续同包自动音频。正式提交完整包后由 A 独立复核并按范围合入。不得将本轮写成默认算法替换、正式定位／降噪、完整 H2/H3 或 V1 通过。
