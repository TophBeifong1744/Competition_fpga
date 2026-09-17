# Testbench

2026-09-17：`servo/tb_motor_drive.v` 是获准舵机模块的活动TB，39项检查；`sim/run_servo.ps1` 可分别以100 MHz/1 MHz复跑。独立512编码/逐拍复核证据见 `docs/reviews/servo-b1d51d4/REVIEW.md`；原包是来源快照，不双处维护。

2026-09-11已归入common/和acquisition/：C001作者TB、C002作者/联合/独立TB、C003作者/独立TB，共6个文件、6组统一回归（C002作者组运行全部1～64位）。原测试激励不改，仅文件归位；顶层名可能沿用tb_independent/tb_review，由[清单](../sim/modules.json)明确映射。

使用[统一回归入口](../sim/run_regression.ps1)，每组单独编译库，DUT只从rtl/读取，避免旧任务包同名模块重复编译。当前仅基础模块功能测试，不代表四路采集或整机测试。

本目录保存自检测试平台、断言、scoreboard 和覆盖用例，不把波形目测作为通过标准。

每个 RTL 模块至少覆盖：复位、连续输入、间断有效、边界值、溢出/饱和、FIFO 满空和非法配置。算法模块使用 `model/matlab/` 生成的受控测试向量，并对输出数据、延迟和状态标志进行自动比较。

测试输出必须给出明确的 PASS/FAIL、首个错误位置和关键参数；批量波形与临时日志写入被忽略的仿真输出目录。

