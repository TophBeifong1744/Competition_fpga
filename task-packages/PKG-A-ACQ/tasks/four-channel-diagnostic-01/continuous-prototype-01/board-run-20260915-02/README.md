# 连续采集 C1：计时修正后的首次实板复测

2026-09-15。状态：**日志及配套构建自检通过，可交工作执行检查/B独立复核；不是自行验收。**

## 结论

拓芙修改 Vitis 的 now_us、重新 Build 后，执行一次 four_mic_continuous Run。两段均约10秒并各自停止排空，同一程序完成一次采集重启；段间不复位 PS/PL/DMA。旧公式造成的约四倍时长矛盾已消失。本次不是单段20秒录音，也未保存完整连续音频。

| 核对项 | session 0 | session 1 |
| --- | --- | --- |
| result | OK | OK |
| 组数 / 包数 | 480250 / 1921 | 480250 / 1921 |
| 累计在线检查字节 | 15368000 | 15368000 |
| 原始编号（十进制） | 14881～495130 | 549769～1030018 |
| 请求停止时刻距启动 | 10.000129 s | 10.000133 s |
| 请求停止后排空耗时 | 5209 µs | 5208 µs |
| 按配置48kHz由组数推导的片段时长 | 10.0052083 s | 10.0052083 s |
| 单包检查最大耗时 | 56 µs | 56 µs |

比480000组多出的250组符合完整包边界停止的设计。段间有54638个原始编号未被捕获，对应主动停止、打印和重启等待；不重编号、补样或拼接。48kHz仍为配置值，并非本次独立频率测量。

两段 SOURCE=C100000A、DMA_SR=00001002、active=-1、owners=0,0；近期16包的长度、编号及槽交替检查通过。四路都有正负幅度变化且clip_flags为0。PS在线逐组检查已覆盖编号连续性、signed24范围、合法flags/reserved及每槽64字节guard，未触发对应失败；本次没有完整原始BIN供PC重新逐组独立复核，不能扩大为完全独立的数据校验。

`bad_group=249 bad_lane=3` 是程序最后检查位置：这些字段在正常检查时同样更新，不能在result=OK时解读成错误计数。`max_arm_gap_us` 含等待下一完整包的时间，不等于CPU处理耗时或DMA最大延迟。

## 实际改动与版本绑定

- 唯一应用逻辑修改：`now_us` 的分母由 `COUNTS_PER_SECOND` 改为 `(COUNTS_PER_SECOND)`。忽略空白格式后，与修复前源码的差异恰为这一处括号。
- 两个 continuous_core 文件与原候选逐字节相同；不改RTL、BD、XDC、CIC、PS配置、数据格式及DDR合同。
- 实际构建于20:57:08，ELF于20:57:09生成；与串口版本时间一致。9项构建输入MD5与当次构建记录一致。
- 从实际 `.o` 和 ELF 提取的64字节 continuous_contract 完全一致，仍为250组/8000字节每包、两槽8064字节步长、每槽64字节guard、RUN_US=10000000、MIN_GROUPS=480000。
- ELF中 now_us 反汇编的除数是 `0x13de435f`（333333343），即当前666666687 Hz CPU配置的一半，不是旧式左结合除法。
- 当前ELF SHA-256：`ebc576e2bfe87ca45c06fb62359babc36f8d474505a97ff6d121336d2a3c3fa3`。
- 当前bit SHA-256：`b15991bc0f8595970361be553b542e334dbb7dca268c01864ecd80fcffbbffaf`；与修正前完全相同，XSA内bit也逐字节匹配。
- 原始日志 SHA-256：`74916dfeb4456c620427fd2a1142d2768e6e9d465651aedadeaa702fc17a4a4e`。

上述绑定是本机实际源码、对象/ELF、启动配置、日志版本及C1状态的交叉核对，不是板上bit/ELF哈希回读证明。全部20项原件的来源与SHA-256见MANIFEST.json；复制后全部核对一致。

## 内存与数据所有权

程序（含堆栈）末端：0x00112640；实际ELF全部ALLOC/PT_LOAD与RX无交叠。RX保留范围维持 `[0x01000000,0x01100000)`。

| 槽 | 数据范围（右端不含） | guard范围（右端不含） |
| --- | --- | --- |
| 0 | [0x01000000,0x01001F40) | [0x01001F40,0x01001F80) |
| 1 | [0x01001F80,0x01003EC0) | [0x01003EC0,0x01003F00) |

实际占用16128字节，不是同时占用累计检查的15.368 MB。FREE槽填充哨兵、全槽flush/invalidate后才能交DMA；完成后CPU再次invalidate、检查数据与guard，检查通过才回收。不能从结束时的两个槽恢复整个10秒录音，也不使用旧短抓取导出命令生成伪连续文件。

## 当前运行入口（用户在 Vitis 操作；此次复测已完成）

- 原Vivado：`F:/College/verilog_digital_system/AMD/Competiton/one/one.xpr`。
- 平台：`F:/College/verilog_digital_system/Vitis/continuous_platform`。
- 应用：`F:/College/verilog_digital_system/Vitis/four_mic_continuous`。
- Vitis Run配置：`four_mic_continuous_app_hw_1`，一次Run执行两段。初次加载会按配置复位系统/编程PL/初始化PS，**两段之间仅重启采集**。
- ELF：`F:/College/verilog_digital_system/Vitis/four_mic_continuous/build/four_mic_continuous.elf`。
- bit：`F:/College/verilog_digital_system/Vitis/four_mic_continuous/_ide/bitstream/system_continuous_20260915.bit`。
- ps7_init：同应用 `_ide/psinit/ps7_init.tcl`；完整配置副本见configuration/launch.json。
- COM3、115200，先保存完整串口再Run；段内故意不打印UART。不在DMA运行期间读写RX或启动其他消费者。

重要：旧 `delivery-01/release`、根 `ps/main_continuous.c` 和旧 `load_candidate.tcl` 仍是历史未修计时版本，本次未覆盖它们。**它们不能作为这次修复版的加载入口。** 本目录ps/runtime是当前实际修复版快照；使用历史脚本会退回有计时问题的固件。工作执行/B需按新哈希复核并安排正式源码/入口更新，不重标旧记录。

## 本次实际检查与历史证据分开

- **本次实板**：用户完成两段各约10秒、两次停止排空、一次无复位采集重启；PC检查完整串口及对应构建。没有板上故障注入、无限运行、精密声学标定。
- **本次离线检查**：check_evidence.py 核对20份原件SHA、对象/ELF合同、ELF内存范围、唯一源码修复、XSA/bit、两段日志、近期槽轮转及4路统计。另检查计时1/10/40秒的旧式反例与新式整数结果，读取实际ELF计时除数。结果见CHECK-RESULT.json。
- **历史仿真**：此前XSim小参数5894次检查、生产参数314127次检查、四路前端检查，以及主机16场景；此轮未重新执行，不把旧模拟时钟测试计为当时已经覆盖BSP宏错误。
- **时序/资源**：引用此前原F盘one实现核对：WNS5.281 ns、WHS0.023 ns、WPWS3 ns，各总负裕量0；LUT8329、FF4368、RAMB36/18为1/1、DSP0。此轮bit未变，未新综合/实现。历史报告见连续候选RESULTS.md及用户one.runs/impl_1；4输入/4输出缺外部delay的既有边界、DRC/methodology警告未消除，不写成所有警告为零。
- B额外测试、独立验收、正式M1/H3、一小时长稳：不在此次结论内。实板超时/溢出错误恢复未故意触发；相关负例仍只有既有仿真/主机证据。

复查命令（只读）：

```powershell
& 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B 'E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/board-run-20260915-02/check_evidence.py'
```

该检查复用current_build的只读ELF解析器，并调用本机ARM objdump；不是重新构建、下载，也不是通用接收器或完整PS回归套件。

## 失败保留、回退与停止点

- 修复前日志、ELF及计时根因保存在相邻 board-run-20260915-01，没有覆盖或改写PASS/时间。
- 修复计时不涉及硬件变化，不需要重做Vivado或平台。若程序出现新错误，先保留完整串口和错误快照，不自动清零/重复Run；不要为“回退”重新使用计时错误的ELF作为正常版。
- 若需要回到原四麦短抓取，用户使用保留的 `four_mic_capture` / `c_adapter_platform` 完整配套Run流程，重新加载原四麦短抓取bit、PS初始化和ELF；不是旧单麦，不只换ELF。执行前仍需核对实际保留版本，不能假设项目名相同即匹配。
- 本次Codex只读F盘、归档并运行离线检查，没有替用户修改工程/构建/上板；未提交、推送或合入。
- 当前操作停止点：将本目录和首次计时问题记录交“拓芙工作执行”检查交付完整性，再交B复核。无需拓芙为此额外重录/扩DDR/做一小时测试。
