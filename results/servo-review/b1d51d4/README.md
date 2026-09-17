# b1d51d4 独立复核原始证据

结论及完整范围：[REVIEW](../../../docs/reviews/servo-b1d51d4/REVIEW.md)。固定候选为b1d51d44aa2c055a145b832b7c272fd33b7d0395。

- `author-run-01`：PowerShell 5.1解析失败，原日志保留。
- `author-run-02`：PowerShell 7，两配置各39项通过、非法1.5MHz及已有目录负例。
- `independent-run-01`：复核TB首次watchdog错误和当时源码保留。
- `independent-run-02`：修复复核TB后，512编码/逐拍检查在1、3MHz均通过。
- `fault-run-01`：独立故障副本（不是候选修改）及原始失败输出；`run_review.py`可从固定候选重建副本。
- `integration-01`：活动rtl/servo和tb/servo实际加载验证，1MHz、39项通过，来源路径见result.json。
- 每轮commands.json含准确命令、cwd、退出码、耗时；完整stdout/stderr不截断。hashes.json记录保留材料SHA256。可重建XSim缓存不入Git；日志/源码不因此删除。

复现：安装好的Python执行`run_review.py --worktree <固定候选的干净工作树> --output <不存在的新目录> --mode author|independent|faults`；使用PowerShell 7和F:/AMD/2025.2/Vivado/bin，换机器需按实际工具位置调整复核脚本，不改作者源码。作者run01的5.1命令以该轮commands.json为准，当前脚本使用7。

活动目录运行：仓库根执行`pwsh -File sim/run_servo.ps1 -OutputDirectory <全新路径> -ClockHz 1000000`。这不是综合、BD或板测入口。
