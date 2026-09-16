# E1 首次 300 秒 + 10×10 秒实板记录

2026-09-16。拓芙实际运行并提供完整串口；已确认使用 `four_mic_endurance_app_hw_1`，只点一次 Run，随后由程序完成所有段落，期间没有人工复位、断电或再次 Run。工程实现完成只读检查及证据归档，**不自行验收、提交、推送或合入**。

结论：这份实板日志报告 11 段全部成功；本次归档解析、计数/首尾编号/状态一致性和当前文件版本绑定检查通过。段内逐组检查由板上程序执行，不是 PC 重新逐样本复核。B 的本批独立批准/入口放行记录未随本次材料取得，不追认或伪造批准。交工作执行核对并发布待审 SHA。

本记录是后续实际运行证据，不改写根 README、BUILD-ORDER-UPDATE、BUILD-RESULT 中先前“尚未上板”的时点事实。`checks-01/result.json` 内 `build_binding.board_test=NOT_RUN` 是引用的构建时点字段；本次实板证据是本目录 UART 和操作者确认，不用修改旧字段来消除时间差异。

## 1. 实际运行结果

| 段号 | 程序记录的采集命令持续时间 / s | 检查组数 | 包数 | 停止排空 / μs | 结果 |
| --- | ---: | ---: | ---: | ---: | --- |
| 0 | 300.000125 | 14400250 | 57601 | 5209 | OK |
| 1 | 10.000123 | 480250 | 1921 | 5209 | OK |
| 2 | 10.000131 | 480250 | 1921 | 5209 | OK |
| 3 | 10.000131 | 480250 | 1921 | 5210 | OK |
| 4 | 10.000132 | 480250 | 1921 | 5209 | OK |
| 5 | 10.000133 | 480250 | 1921 | 5207 | OK |
| 6 | 10.000134 | 480250 | 1921 | 5207 | OK |
| 7 | 10.000133 | 480250 | 1921 | 5210 | OK |
| 8 | 10.000133 | 480250 | 1921 | 5210 | OK |
| 9 | 10.000134 | 480250 | 1921 | 5209 | OK |
| 10 | 10.000130 | 480250 | 1921 | 5210 | OK |

- 汇总：started=11，completed=11，failures=0，normal_between_session_resets=0。
- 总检查量：19,202,750 组、76,811 包、614,488,000 字节。这是累计处理量，不是 DDR 占用，更不是已保存文件大小。
- 每段满足：groups=packets×250，bytes=packets×8000，last_id−first_id+1=groups；板上程序逐组检查 ID 递增且跨槽不中断，串口未报告 ID_ERROR。独立段之间 ID 前进且有有意停止期间的间隔，未补样、重编号或拼接。
- 每段最终 SOURCE=C100000A、DMA_SR=00001002、length=8000、active=-1、owners=0,0；在线首错均为 OK，每个已验证包包含 guard 检查。最近 16 包的双槽轮转、长度和状态可由原日志追溯。
- 四路每段均有非恒定数据，signed24 范围内，44 个通道统计的 clip_flags 均为 0。该标志不是增益/声学性能标定。
- 最大单包检查时间 56 μs；日志 max_arm_gap_us 范围 5240～5251 μs。后者包含等待下一完整包的间隔，不能直接解释为 CPU 纯计算耗时。
- 每段比最小组数多 250 组，结合完整包边界停止和排空逻辑解释；未截断最后一包来凑整阈值。
- `bad_group=249 bad_lane=3 bad_value=...` 是源码持续更新的最后检查位置/值，不是错误数量；成功时也会保留。错误判据是 first_failure/result/相关状态。

## 2. 配置、源码与真实产物绑定

实际应用 `F:/College/verilog_digital_system/Vitis/four_mic_endurance`，复用 `F:/College/verilog_digital_system/Vitis/continuous_platform`；Cortex-A9 #0 standalone，Vitis 2025.2。原 `four_mic_continuous` 与实际 one 未由本次归档操作更改。

| 项目 | 本次合同 |
| --- | --- |
| 长段 | 300000000 μs 且至少 14400000 组，一次 |
| 短段 | 每段 10000000 μs 且至少 480000 组，十次 |
| 段间 | 先停止排空/打印，再等待 1000000 μs；不复位 PS/PL/DMA |
| 超时 | 原传输/包/排空超时 2000000 μs；全段阈值另有 run_us+2 秒期限 |
| 数据 | 每组 8×32 位，原始 64 位 ID、mic0～3 signed24/int32、flags、reserved |
| 分包 | 每包 250 组，8000 字节 |
| RX 保留范围 | [0x01000000, 0x01100000) |
| 两槽 | 各 8000 字节数据 + 64 字节 guard；stride=8064，共 16128 字节，终点 0x01003F00 |
| 程序边界 | end=0x00113890，实际 map/加载区间检查在 RX 前 |
| 缓存/所有权 | CPU 准备整槽并 flush/invalidate 后交 DMA；完成后 invalidate，再 CPU 检查，完成才回收 |
| 计时除数 | 实际对象/ELF核对 333333343，不只是版本字符串 |

沿用已有实际构建快照，不重复复制源码和二进制：

- `../evidence/user-build-20260916-2052/app/src/`：本次编译源码、UserConfig/CMake/链接脚本。
- 同目录 `app/build/`：真实 ELF、对象、memory.map、编译数据库、Ninja/CMake 信息。
- 同目录 `app/_ide/launch.json`：用户确认选择的实际加载配置。
- 同目录 `records/`：真实 pre/post/load 检查；`generated-commands.json` 是构建系统产生的完整命令，非额外编译。
- BSP 固定依赖及 88 个文件哈希：`../../timerfixed-entry-01/POLICY.json`；本次再次只读匹配。
- bit/XSA/ps7_init 沿用 `../../board-run-20260915-02/runtime/`；本次与实际加载/平台路径逐项哈希比对，不复制历史整包。

| 文件 | SHA-256 |
| --- | --- |
| 原始串口 | 6920a852e43f2f6e4f47c2f1a4aefb8c3058ff5d108fc8ec5b4ea80e9cd41fd5 |
| four_mic_endurance.elf | 75c7e5e2203ed1ba019c83a1123ef79eff0c877286d722eea5b8d9a275c76449 |
| main.c.obj | 4eeb96edabcb79b2b6df29bbdbe2c67ee3532b14a71bfbe08117f4df63a3dc15 |
| system_continuous_20260915.bit | b15991bc0f8595970361be553b542e334dbb7dca268c01864ecd80fcffbbffaf |
| system_continuous_20260915.xsa | b84e93631132a3838cc9dadc1ce9037f2685d4d10de0b1655c76291663a8f60b |
| ps7_init.tcl | a158fcc7d723b21003864159006e781ffaf5e8df24ec9b1d9279f9d14ff3ee5e |

23 项实际应用文件与构建快照一致，原构建批次清单的 46 项均未变化，88 项 BSP 及三个硬件/初始化文件一致。该绑定结合用户加载配置确认与日志构建时间；**没有做板上 bit/ELF 的独立读回或安全认证**。

## 3. 检查层级及失败记录

| 层级 | 实际证据及边界 |
| --- | --- |
| 主机功能模型（此前本 E1 批次） | `../evidence/20260916_190840_model_ca62843d`：原 16 项、11 段模拟调度及新增配置/失败/期限检查；不是实板计时。本次归档没有重跑或重计这些次数。 |
| 构建检查器（此前本 E1 批次） | 原 7 个配置/合同测试方法，计时布局修复增加 12 项并回归原 7 项；证据在 `../timer-layout-fix-01`。不是 B 独立测试。 |
| ARM 真实构建 | 拓芙在 20:52:10～20:52:12 Clean/Build；实际 pre/post 与对象/ELF/map 检查通过。本次归档没有编译 ARM。原控制台提供的是尾段，非声称有完整 IDE 控制台转储。 |
| 新 UART 检查器（本次实际执行） | `checks-01/parser_tests.log`：4 个测试方法，包括真实正例、12 种文本变异、截断、重复运行拒绝；文本变异不算板上故障注入。原 UART 解析结果在 `checks-01/log-check.json`。 |
| RTL 功能/实现时序 | PL 没改，沿用此前 C1 产物；本批没有新 RTL 仿真、综合、实现或时序测量，不能称本批新通过。 |
| 实板 | 本目录一次完整用户执行的 UART + OPERATOR-CONFIRMATION.md。无板上故障注入、无一小时连续测试、无完整 PCM 文件。 |

保留的失败：`../timer-layout-fix-01/records/20260916_204259_post_9c407c3bf7` 和 `20260916_204520_post_c44c95f18c` 的真实构建后置检查失败，原因为检查器不支持合法的计时常量池对齐布局；修改仅限 E1 检查器，旧源码/失败产物/日志不覆盖。初始未接入候选的预检查拒绝也保留在 `../evidence/20260916_191156_pre_45b6e25d09`。本次实板日志没有报告失败，不用这点消除之前的失败记录。

## 4. 复查命令与运行入口

下列仅在 PC 读取日志/文件，不构建、下载或运行板卡。在 PowerShell 使用现有 Python；路径变量仅为本任务路径：

```powershell
$py = 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$runDir = 'E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/endurance-test-01/board-run-20260916-01'
& $py -B "$runDir/verify_log.py" "$runDir/endurance_300s_10x10s_20260916_01.log"
& $py -B "$runDir/test_verify_log.py"
& $py -B "$runDir/record_checks.py" verify
```

本次实际记录命令（checks-01 已存在，重跑必须选新目录，不覆盖）：

```powershell
& $py -B "$runDir/record_checks.py" record --app 'F:/College/verilog_digital_system/Vitis/four_mic_endurance' --platform 'F:/College/verilog_digital_system/Vitis/continuous_platform' --log 'F:/College/verilog_digital_system/Vitis/endurance_300s_10x10s_20260916_01.log' --out "$runDir/checks-01"
```

归档命令 `record_checks.py seal` 仅创建一次 SHA256.json；后续用 verify 验证清单，不能重写旧清单。清单覆盖归档时点整个 E1 包，新增未来证据不倒算本次；外部 BSP/既有硬件依赖另有固定哈希。归档不要求再运行硬件。

实际 Vitis 入口：`four_mic_endurance` 应用 → `four_mic_endurance_app_hw_1` → 当前应用 ELF + system_continuous_20260915.bit + ps7_init.tcl。只有首次加载初始化；段间由程序自动处理，不按 11 次 Run。完整加载配置和编译/链接命令见上述真实构建快照。恢复旧短连续版本时使用独立原应用 `four_mic_continuous` 及其计时修复入口，不把旧 ELF 改名伪装为 E1；本次没有执行回退或重跑。

## 5. 交付与停止点

- 本次只新增此目录：原始 UART 原字节副本、用户确认、日志检查脚本/测试/输出、文件绑定、SHA-256、交接说明。不改 F 盘工程、采集源码、PL/BD/XDC/BSP/默认算法，也不改旧证据清单、B 报告或其他任务。
- 这是一段约 5 分钟持续在线采集，再十次独立短段；不能写成一段约 400 秒连续录音，更不能宣称一小时长稳。
- 数据逐包检查后回收，因此没有全程 BIN、CSV 或 WAV；无独立全样本离线重放，也不能据此宣称定位、波束形成、声学收益、正式 M1/H3。
- 初始程序初始化可能复位 DMA，初始 Run 配置会复位系统/处理器；只报告成功段之间无复位。日志计时来自已检查的固件时基，没有新增独立时钟精度测量。
- 工作执行核对完整性/历史依赖，处理入口批准记录与本批送审，发布准确待审 SHA 后交 B。工程实现未提交、推送或合入；当前共享目录其他任务改动原样保留。本轮到此停止，不追加实物任务。
