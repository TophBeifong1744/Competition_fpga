# 离线诊断入口记录

2026-09-28，E 工程助手首次尝试直接 import 历史 `background-target-stop-20260917/finish_scene.py` 以只读复核 C 的八段原件。该文件仍用搬迁前 `docs/team-workflow.md` 查找仓库根，当前实际入口在 `document/`，故 import 在 `next(...)` 处抛出 `StopIteration`、进程退出 1；尚未读取或修改任何 BIN。此为脚本路径失配，非录音失败。

随后只在一次性 Python 进程内把该根路径字符串适配为当前 `document/team-workflow.md`，原 `verify` 和 `align` 函数体未变，八段均完成只读检查。正式复核入口 `verify_batch.py` 则从两个历史文件的 AST 中编译原函数体，避免执行旧模块初始化；源码哈希写在 `offline-01.json`。它没有修改受控旧脚本或冻结数据，也不能替代独立 B 复核。

另行对 `sound_09_22` 做了只读身份调查，未把其文件纳入本户外包，也未改变源文件。该调查只为防止两批混同；其归属仍按操作者确认处理。
