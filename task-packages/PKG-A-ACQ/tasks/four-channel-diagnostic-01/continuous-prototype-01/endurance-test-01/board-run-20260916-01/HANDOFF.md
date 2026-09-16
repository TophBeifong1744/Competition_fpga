# 给“拓芙工作执行”的 E1 实板回报

2026-09-16，工程实现完成“一段连续 5 分钟 + 10 次 10 秒启停”的材料整理，申请完整性检查及发布待审版本，**不是自行验收**。

入口：

`task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/endurance-test-01/board-run-20260916-01/README.md`

## 实际结果

- 用户复用 continuous_platform、新建并自行修改/构建 four_mic_endurance。20:52:11 构建的 ELF：`75c7e5e2203ed1ba019c83a1123ef79eff0c877286d722eea5b8d9a275c76449`。
- 拓芙已确认选择 four_mic_endurance_app_hw_1，只点一次 Run；11 段由程序自动完成，期间没有人工复位、断电、再 Run。初次加载自身的初始化/复位不属于段间复位。
- session0 程序计时 300.000125 s，检查 14,400,250 组；随后十段各至少 10 秒、各 480,250 组，全部 result=OK。
- 合计 19,202,750 组、76,811 包、614,488,000 字节在线检查；段内编号检查、DMA、错误状态及每包 guard 未报告失败，停止排空约 5.21 ms，最终两槽释放。四路均有非恒定数据，clip_flags=0。
- `ENDURANCE_11_SESSIONS_PASS_NOT_ACCEPTANCE`；summary started=11 completed=11 failures=0 normal_between_session_resets=0。
- RX 保留范围和两槽/分包合同没变；数据检查后回收，**没有完整 5 分钟录音文件**，也没有拼接不同段冒充连续。

## 证据及审查范围

- 本目录保存完整原始 UART、OPERATOR-CONFIRMATION.md、逐段检查 JSON、4 个日志解析测试方法（含 12 种变异）、哈希及版本绑定。原日志 SHA：`6920a852e43f2f6e4f47c2f1a4aefb8c3058ff5d108fc8ec5b4ea80e9cd41fd5`。
- 本次重新只读匹配：实际应用/构建快照 23 项、原成功构建清单 46 项、BSP 88 项及 bit/XSA/ps7_init 三项。复用 `endurance-test-01/evidence/user-build-20260916-2052` 的真实源码/对象/ELF/map/命令/加载配置；不是重新编译。
- 旧 E1 准备模型、计时布局修复测试和两轮真实失败构建记录均保留，不算本次重新执行；见 README 分层结果和失败入口。
- 需发布/复核的是整个 E1 增量（proposed-src、check_endurance.py、timer_layout.py、CMake 检查入口、tests、证据与本目录），不能只提交 PASS 日志漏掉实际调度/检查器修改。其 timerfixed-entry-01/current_build/旧 C1 固定依赖应按已有版本引用，不夹带其他 Skill 或共享目录改动。
- 当前没有随交付取得 B 对计时修复构建/加载入口或 E1 的独立放行记录；不能从本次实际成功运行倒推批准。请工作执行核对相关待审记录并按职责安排 B 复核。
- SHA256.json 固定本次归档时点 E1 文件；复查命令见 README。原始串口/构建文件保留原字节，发布时注意换行转换不能悄悄改变冻结证据哈希。

## 边界与下一步

本次实板支持这一轮 300 秒及十次短段启停的作者侧证据；不是一小时长稳、完整故障注入、正式 M1/H3、定位或波束验收。PL 未改，本批不重复报告综合/时序为新结果。

工程实现没有更改 F 盘工程、没有代构建或下载、没有 Git 提交/推送/合入。请工作执行检查交付完整后发布待审 SHA，再交 B 独立复核；不要求拓芙补录或重跑本次。

当前会话未提供跨任务消息工具，本文件为待转交内容，不声称已发送到“拓芙工作执行”。
