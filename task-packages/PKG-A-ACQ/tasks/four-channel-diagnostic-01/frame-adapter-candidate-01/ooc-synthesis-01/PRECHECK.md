# 冻结候选只读核对

核对日期：2026-09-17。未切换、重置或清理共享工作区，未修改冻结 RTL。

| 项目 | 只读结果 |
|---|---|
| 固定提交 | `a7d944a2268fff6215b2c619d2d6440235ff5752`，对象类型 commit |
| 本地候选分支 | `refs/heads/codex/toph/frame-adapter-candidate-20260917` 准确指向固定提交 |
| 远端跟踪分支 | `refs/remotes/origin/codex/toph/frame-adapter-candidate-20260917` 准确指向固定提交 |
| RTL SHA-256 | `f0da9259a2c5407f003e527dc097fb57ef514a2335c20a528655427294f77585` |
| RTL Git blob | `f4091c77e0f9b5f5bb163735a750b13b4d6db8eb`；当前文件与提交内 blob 一致 |
| 功能仿真 | 固定提交中的 `evidence/run-20260917-03/xsim.log`；XSim v2025.2，出现 `PASS frame_adapter RTL: frames=7 events=9` |
| 本机 Vivado | v2025.2 64-bit，SW Build 6299465；仅执行了版本查询，没有运行本 OOC 综合 |

功能仿真 PASS 只说明既有 TB 范围内的帧内容、重叠、背压和错误事件行为；它不是资源、时序、布局布线、CDC、工程接入或实板证据。`run_ooc.tcl` 会在每次综合前重新检查分支指针、提交对象、RTL SHA-256、Git blob 和 XSim PASS 标记，任一不符即拒绝运行。
