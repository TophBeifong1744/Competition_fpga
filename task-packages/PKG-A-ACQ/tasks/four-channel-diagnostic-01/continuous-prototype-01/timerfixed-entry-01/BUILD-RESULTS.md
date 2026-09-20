# 实际构建与加载预检查结果（2026-09-16）

结论：原 `continuous_platform` / `four_mic_continuous` 已接入本增量计时修复版检查入口，用户完成新编译。实际新产物与加载预检查通过作者自检，等待工作执行检查及B独立复核。本轮没有实板操作，不扩大之前的限定批准。

## 实际改动和入口

- 用户在F盘应用src/CMakeLists.txt末尾接入本目录vitis_gate.cmake；采集源码、UserConfig、链接脚本与已批准修复快照一致。没有创建工程副本，没有改Vivado/PL/BD/XDC/BSP。
- 用户执行Vitis Clean/Build；Codex仅只读核对F盘文件，在本增量目录保存检查脚本、测试和证据。没有代为编译、下载或运行。
- 构建入口：原应用Build，自动pre → 编译/链接 → post。编译与链接实际生成命令原文在 `user-build-20260916-01/verification-01/ninja-commands.json`；该命令枚举是只读检查，不是第二次编译。
- 加载入口：`load_timerfixed.tcl` 内 `c1_timerfixed_load`，完整参数见OPERATOR.md；默认只检查。不得使用历史root run.py build/load、load_candidate.tcl或delivery-01/release代替。GUI直接Run可绕开检查，不作不可绕过的安全承诺。
- 同一bit/XSA/ps7_init继续复用；完整固定哈希在POLICY.json。本轮无必要重建硬件或重录两段实板数据。

## 新构建证据

用户Vitis Build ID：`2ca1e2ac-3eaf-4813-8875-00d62ae56561`，18:23:48开始、18:23:50完成。用户提供的控制台尾段关键信息转存于 `user-build-20260916-01/user-console-excerpt.txt`（整理了排版，非逐字原文），**没有取得完整Vitis控制台原文**，不补造缺失行。

完整检查记录已从实际应用c1_checks复制，保留原目录名和内容：

- `20260916_182349_pre_c92deb3201`：PRECHECK_ONLY，编译前对象不存在。
- `20260916_182350_post_92bd309638`：ARTIFACT_CHECK_PASS_NOT_BOARD，fresh_compilation_observed=true。
- `20260916_183019_load_a85a38a914`：本轮重新检查真实F盘产物，通过load阶段及默认dry-run；读取上述复制记录。没有执行XSDB硬件命令。

快照保存实际src（包括用于post绑定的缓存）、新对象、ELF、map、编译数据库、CMakeCache、build.ninja、rules.ninja、.ninja_log、应用/平台配置及launch.json。`snapshot-binding.json`逐文件确认快照与当时F盘实际文件一致。未复制整个平台或研究包，BSP88项依赖和硬件由POLICY哈希绑定。

| 实测检查项 | 结果 |
| --- | --- |
| ELF SHA-256 | `726a91fe19fd9b9e67cca6f3c8668bf484df92d1bbb2ec2e5f2619cc0237324c` |
| main.c.obj SHA-256 | `0fc486cf671402f1d62041e94e8ec947ebc24961f852114f03ba4baed04f6469` |
| 实际计时除数 | 333333343；对象计算指令及ELF实际调用/常量寻址核对通过 |
| 程序end | 0x00112640；ALLOC、PT_LOAD、堆栈均在RX之前 |
| RX保留区 | [0x01000000,0x01100000)，未扩大 |
| 分包与两槽 | 250组×8字×4字节=8000字节；每槽64字节guard、槽步长8064；两槽共16128字节，终点0x01003F00 |
| 时限/目标组数合同 | 10000000微秒、480000组，直接从对象及ELF的合同检查 |
| 加载配置 | four_mic_continuous_app_hw_1，Local/Zynq/Cortex-A9 #0；当前build ELF、匹配bit及ps7_init |
| ELF尺寸表 | text44668、data1648、bss25936，总72252；不是DDR预留区大小 |

新旧ELF均296612字节，完整字节比较仅27字节差异：`.rodata`编译时间由Sep 15 2026 20:57:08变为Sep 16 2026 18:23:50，7字节变化；链接器GNU build-id在地址0x00106478的note内，20字节变化。该note被链接脚本收进.text，不能把这20字节误判为CPU指令变化。除这些字节外完全相同。说明及可执行核对见 `explain_elf_difference.py`、`verification-01/elf-difference-explained.json`；未修改golden或实际ELF以求相同哈希。

## 本轮验证范围

- 准备阶段已实际运行18项新Python测试、4项Tcl模拟案例、原10项入口测试与原34项安全测试；原始日志及初次失败记录在evidence。不是18/34次真实固件构建，没有宣称另一个B补充21项通过。
- 本次用户真实编译一次，pre/post证据与新对象匹配；Codex随后执行真实gcc版本查询、objdump反汇编、ELF/map/源码及配置检查。
- Tcl加载dry-run使用真实Tcl/Python检查链和真实新ELF，不模拟编译器结果；同时禁止connect/targets/rst/fpga/dow/con，保证本次只验证检查入口。不能以此称实际XSDB下载或实板通过。
- 没有新RTL仿真、综合、布局布线或时序结论；硬件未改。没有新10秒实录、长稳、故障注入、M1或H3验收。

## 复查命令与输出保护

工作目录设为本文件所在目录，使用现有Python：

```powershell
$py = 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $py -B check_entry.py --stage load --app F:/College/verilog_digital_system/Vitis/four_mic_continuous --platform F:/College/verilog_digital_system/Vitis/continuous_platform --tools-bin F:/AMD/2025.2/Vitis/gnu/aarch32/nt/gcc-arm-none-eabi/bin --record-root "$PWD/user-build-20260916-01/records"
```

此命令只读工程，向增量records新建唯一结果目录；使用已复制的真实post记录，不下载。实际执行Tcl和Ninja枚举的完整argv/stdin/stdout/退出码保存在verification-01。一次性核对脚本 `verify_user_build.py` 和 `explain_elf_difference.py` 拒绝覆盖已有输出；不要为重跑删掉旧证据，可在另一个新验证目录适配输出后重跑。

已知限制：当前入口只支持固定工具/合同布局；src编辑器缓存变化也会导致保守拒绝，应保留失败记录定位，不绕过检查。完整Vitis控制台未提供，现有真实检查日志/命令/执行索引不能称作完整原控制台。共享main脏目录与远端核对限制沿README所述；本任务未切换、提交、推送或合入。

## 给工作执行的回报与停止点

本轮交付为 `timerfixed-entry-01` 独立增量：受检构建/加载入口、固定合同、18+4新测试及10+34复用测试、实际新构建快照、真实产物加载预检查、全部保留失败、文件SHA清单。修复计时源码未被改回历史版本，新ELF差异已解释。请工作执行检查交付完整性后发布待审SHA交B；工程实现不自行宣布独立验收。

现在无需用户再次Run。撤销工程接入须由用户移除CMake末尾三行并重新配置；仍保留计时修复源码和已批准冻结固件，不回退到旧计时ELF。
