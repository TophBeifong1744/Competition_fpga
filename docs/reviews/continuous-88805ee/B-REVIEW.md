# B 独立复核：四路连续采集原型与计时修正实板记录

2026-09-15。结论：**通过，仅批准连续采集原型及修复版实板记录的限定入库**。未发现阻断该范围入库的问题；不是正式 M1/H3、音频、定位、整机、真实故障恢复或长稳验收。

审核提交：`88805ee415f137998b59b7cb197f2eeb988d17b7`，远端分支 `codex/toph/continuous-prototype-20260915`；父提交/发布基线 `058aa3095fd4df7392645004b164adb4eec52041`。直接 `git ls-remote origin refs/heads/main refs/heads/codex/toph/continuous-prototype-20260915` 确认准确远端，用户完成 Desktop Fetch 后核对本地 Git 对象，并在 `F:/NUEC/review-worktrees/continuous-88805ee` 固定 detached SHA 复核。合并前再次直接确认远端作者 SHA 未变，main 为 `e5621cae92108f480a831b4da679f40fe64631c8`。

作者唯一批准路径：`task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/`。相对父提交只有该目录 222 个新增文件；全部工作树原始字节与审核提交 Git blob 一致。此次覆盖首次发布的完整原型、源码、测试、失败史和两轮实板记录，不缩减为计时修正的 24 项。作者原件、清单、历史错误版本均不改写。B 证据保存于本目录，原执行目录为 `F:/NUEC/review-evidence/continuous-88805ee`。

## 实际命令与结果

先读 `publication/README.md`，再读 `board-run-20260915-02/README.md` 和首次问题目录 `board-run-20260915-01`，继而核对入口、核心、RTL/TB、BSP/构建与运行证据。使用 code-review 的规范与需求两轴复核及 xilinx-suite 的配置/计算/实际验证区分；没有将 Skill 文件加入本次合并。

本机 Python 3.12.14：`C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`；Git 使用相邻 `dependencies/native/git/cmd/git.exe`；原生 GCC 为 `F:/STUDY/IT/C/develop/mingw64/bin/gcc.exe`。下列 `PY` 指该 Python，`TASK` 指上述仓库相对包路径，`EVIDENCE` 指原 B 执行目录。前六项在固定工作树仓库根执行：

```text
PY -B TASK/publication/verify_package.py
PY -B TASK/board-run-20260915-02/check_evidence.py
PY -B -m unittest discover -s TASK/tests -p test_entry.py -v
PY -B -m unittest discover -s TASK/../current_build -p test_build_current.py -v
PY -B TASK/run.py host --host-gcc F:/STUDY/IT/C/develop/mingw64/bin/gcc.exe --output EVIDENCE/host-run01
PY -B EVIDENCE/audit_package.py F:/NUEC/review-worktrees/continuous-88805ee
PY -B EVIDENCE/timer_disasm.py F:/NUEC/review-worktrees/continuous-88805ee/TASK
PY -B EVIDENCE/check_with_capstone.py F:/NUEC/review-worktrees/continuous-88805ee/TASK/board-run-20260915-02
```

| 项目 | B 实际结果与证据 |
| --- | --- |
| 作者发布检查器 | 221 项哈希、222 个文件集合、历史 165 项和两轮原清单通过；`package.txt` |
| Git 字节与 ZIP | 222 个新增文件逐 blob 比对、全部发布 SHA-256、19 份 ZIP 完整成员 CRC 通过；`git-package.txt` |
| 原 `check_evidence.py` | 缺少固定位置的 ARM objdump，执行到该调用失败；`original-check-missing-tool.txt`。不称原脚本原样通过 |
| 包外 Capstone 适配 | 真实 ELF 反汇编及原检查器其余断言通过；`check-capstone.txt`。不是新固件编译 |
| 候选入口单测 | 10/10 通过；`entry-tests.txt` |
| 当前构建安全单测 | 34/34 通过；`safety-tests.txt` |
| 实际 C 核心主机运行 | 16/16 场景通过；`host-run01/logs/test.log`、编译/执行参数及 SHA256.json。IO/time/cache 为模拟回调 |

Capstone 5.0.6 安装在独立的 `F:/NUEC/review-tools/continuous-capstone-5`，未修改系统工具或作者包。复现可为本机 Python 安装相同版本 `capstone==5.0.6`，或通过 PYTHONPATH 指向该依赖；适配器附带的本机路径不要求复制 A 的 F 盘工程。`audit_package.py` 的 Git 路径可按本机安装位置适配，保留原 B 运行证据。

`check_with_capstone.py` 先按发布清单确认原检查器字节，在内存中仅改 ROOT 定位和 objdump 相关块，以实际 ARM 指令解码替代。原清单、对象/ELF、源差异、bit/XSA、日志和算术断言继续运行，冻结脚本未落盘修改。首次小型反汇编辅助脚本把局部 `now_us` 当成全局符号未成功，随后改为读取 ELF 局部符号表；最终输出见 `timer-disassembly-pass.txt`，其中 literal pool 的诊断解码不作为执行代码，最终适配器明确将其解释为数据。

合并至实际共享 main 工作区 `F:/NUEC/develop` 后，以新的输出目录运行：

```text
PY -B EVIDENCE/run_regression.py F:/NUEC/develop EVIDENCE/postmerge03 --host-gcc F:/STUDY/IT/C/develop/mingw64/bin/gcc.exe
```

`postmerge03/commands.json` 记录每条真实 argv、cwd、UTC 开始时间和退出码；包/字节/CRC、适配检查、补充来源校验、10+34 单测与 16 主机场景全部退出 0。仅软件和归档复查，没有运行旧 build/load、XSim、Vivado/Vitis 构建或上板。

保留 B 自身补充脚本失败过程：`postmerge01` 误把 ZIP 内的早期 host 文件当成解压路径；`postmerge02` 又误将早期 host 测试等同最终测试。分别保留失败脚本及输出，修正包外引用后使用全新 `postmerge03`。早期测试缺少最终 STOP_TIMEOUT/慢消费者/OWNERSHIP 情景，差异保存在 `postmerge03/bindings.txt`；最终测试与 `publication/checks/host/test_core.c` 原字节一致，本轮 B 实际编译运行最终 16 场景，不借用早期覆盖。这些是 B 核查脚本假设修正，不是 A 固件被改动后再自审。

## 需求轴：计时、内存、所有权与证据边界

未发现阻断项。

- 当前修复 ELF SHA-256 为 `ebc576e2bfe87ca45c06fb62359babc36f8d474505a97ff6d121336d2a3c3fa3`。对象与最终 ELF 的 64 字节合同一致：`(0x434f4e31,0x01000000,0x01100000,250,8,8000,64,8064,2,16128,0x00100000,0x3fffffff,0x40400000,0x41200000,10000000,480000)`。
- 实际对象包含宏链 `COUNTS_PER_SECOND XSLEEPTIMER_FREQ`、`XSLEEPTIMER_FREQ XPAR_CPU_CORE_CLOCK_FREQ_HZ/2`、CPU 时钟 `666666687`，与 BSP 快照一致。旧表达式没有包围除数宏，展开后连续除以 CPU 频率和 2；修复 `/(COUNTS_PER_SECOND)`。1/10/40 秒算术向量的旧值为 249999/2499999/9999999 微秒，修复后为 1000000/10000000/40000000。旧计时和所有基于 now_us 的超时均受影响，主机模拟时钟测试没有覆盖 BSP 宏问题。
- 实际 ELF 的 `now_us` 在 `0x00100790` 计算 literal 地址，`0x00100794` 以 `ldrd` 读取 `0x001007a8` 处 64 位值 **333333343**，`0x00100798` 调用实际 `__aeabi_uldivmod`（目标 `0x001049a4`，符号 Thumb 位剥离）；同时核对真实 `XTime_GetTime` 调用。结论来自真实代码/数据，不只检查 banner 或版本字符串。
- `end=0x00112640`，ELF 全部 ALLOC/PT_LOAD 区间不与保留 RX `[0x01000000,0x01100000)` 交叠。每包 8000 字节；slot0 数据 `[0x01000000,0x01001f40)`，guard 至 `0x01001f80`；slot1 数据 `[0x01001f80,0x01003ec0)`，guard 至 `0x01003f00`。两槽共 16128 字节，在 DDR 内。每段累计 15368000 字节是反复复用缓冲，不是同时占用该长度 DDR。
- 核心按 FREE→DMA→CPU_READY→CPU_OWNED→FREE 转移，确认 DMA 完成后重新读取完整包 credit，再允许其他空槽启动 DMA，CPU 校验完成才释放原槽。prepare/acquire 分别有缓存维护，保护区/ID/flags/长度/源错误拒绝继续；真实缓存可见性和硬件故障恢复不能由主机模型批准。
- stop 按完整包边界停产并排空；正常第二段路径只有等待和重新 start，没有段间 PS/PL/DMA 复位。错误路径保存复位前状态并终止，不把它当成已经验证的真实自动恢复。
- 归档当前 bit 为 `b15991bc0f8595970361be553b542e334dbb7dca268c01864ecd80fcffbbffaf`，XSA 内 bit 和 ps7_init.tcl 分别与对应归档原件字节一致。HWH 配置 250 组/包、FIFO/地址及 GPIO start 配对，实际加载仅有操作者记录和日志相容性，没有 B 独立设备读回。
- 构建 source-hash-map 共 9 项，公开包可独立核对的 **7 项 MD5 一致**；`vitis-comp.json` 和 `src/README.txt` 未归档，只保留 A 本机核对声明，不记为 B 9/9。编译命令、实际 .o/ELF/宏、7 份源和配置证据支持本次归档范围；未据此批准完整环境重建。

| 归档实板段 | 组/包/累计检查字节 | 原始 ID | stop 请求/排空 |
| --- | --- | --- | --- |
| session 0 | 480250 / 1921 / 15368000 | 14881..495130 | 10.000129 秒 / 5209 微秒 |
| session 1 | 480250 / 1921 / 15368000 | 549769..1030018 | 10.000133 秒 / 5208 微秒 |

两段末状态均为 SOURCE=C100000A、DMA_SR=00001002、active=-1、owners=0,0。末 16 包序号、交替槽、长度和状态符合日志；四路统计包含正负值，clip_flags=0。max_check=56 微秒，max_arm_gap=5249/5251 微秒包含等待包到达，不等于纯软件耗时。

**未保存完整 10 秒 BIN，B 不能逐组复算全部 960500 组。** 逐组正确性仅由 PS 在线检查及其汇总日志支持。段间 54638 个未采 ID 是主动停止间隔，不拼接为连续 20 秒。10.005208 秒为配置 48kHz 下样本数换算，不是独立墙钟或采样率校准。

## 规范轴与失败历史

没有阻断该限定入库的规范问题。19 份历史 ZIP 成员 CRC、原 SHA 和失败记录保留；早期 elaboration/Vivado 构建失败与成功 work12、export11 各自有来源，不将不同构建产物哈希混用。当前 4 份 RTL/TB 与历史仿真来源一致，当前 core/test 与发布主机来源一致。历史 XSim/内部时序报告仅属其原版本证据；外部 IO 未完整约束和 methodology 警告保留，B 没有新跑 RTL 或布局布线。

主机测试依赖数字 mode 与 expect 数组位置对应，属于后续可维护性观察，不是本次阻断；不为此修改冻结测试。无新增算法、门槛或活动 RTL/one 变更。

`git diff --cached --check` 返回 2，包含原始 CRLF 与空白提示；临时允许 cr-at-eol 后仍返回 2。全部为本次冻结包内原件，未格式化清单覆盖内容。精确命令、诊断数量和未压缩输出 SHA 见 `diff-check-summary.json`，完整输出以 gzip 无损保存。**此项未通过**，不能把整体限定通过写成所有通用检查均通过。

## 批准入口与未验证项

批准整个 `continuous-prototype-01/` 按原型/证据身份入库，B 报告及复跑材料保存在包外本目录。当前修复版唯一证据入口是 `publication/README.md` 指向的 `board-run-20260915-02/{ps,runtime,configuration,build}`。

根 `ps/main_continuous.c`、`run.py` 的旧 build/load 路径、`load_candidate.tcl` 及 `delivery-01/release` 保持历史未修版身份，不能当本次新固件入口。host 子命令只测试不变核心。此次不创建或批准修复固件一键安全重建器，不替换实际 one、活动 RTL 或默认算法。

未执行/不批准：A 实际 F 盘全部输入复核、完整 BSP/固件重建、新 XSim/综合/实现、B 上板/重新加载/采录、设备身份读回、完整数据逐组独立复算、独立采样率/墙钟校准、实板超时/溢出注入、故障恢复、一小时长稳、音频/SNR/定位/正式 M1/H3 或整机验收。不新增 9 月 16 日门槛，不代签 A 本机同步。

需求轴：0 阻断；规范轴：0 阻断、1 项维护观察。限定结论：**通过**。发布和本地材料去向另见本目录 `BATCH-CLOSEOUT.md`。
