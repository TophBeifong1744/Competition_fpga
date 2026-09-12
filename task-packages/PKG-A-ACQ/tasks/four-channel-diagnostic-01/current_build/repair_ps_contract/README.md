# PS 缓冲区合同阻断修复

基线：050d06f5dc6fed4fa476e72fa416e9736bc7fef3。
分支：codex/toph/four-channel-engineering-review-20260912。
范围：仅 current_build/。状态：作者修复自检完成，待工作执行提交新 SHA 后由 B 独立复核。
不新增 9 月 16 日诊断门槛；未上板、未提交、未推送、未合入。

## 问题与修复

旧入口仅搜索 PS 版本字符串，却用固定 0x01000000 判断程序边界、固定报告 0x010FA040。
这不能证明实际 PS 使用相同缓冲区。修复前的独立模拟反例确实错误返回 BUILD_PASS_NOT_BOARD_TEST。

当前入口通过以下关系绑定，不依靠运行日志或一份旁置配置 JSON：

~~~text
实际 main_four_capture.c + 同一单元的只读合同常量
        → GCC 一次预处理 .i → 实际编译 .o → 仅链接该 .o → 最终 ELF
                                      │                   │
                                提取编译常量         再提取并比较常量
                                      └─ DDR/XSA/BD ──────┤
                                                   真实分配区间/end
~~~

- 首版只识别已知采集正文，正文指纹固定；七个宏行的有限表达式交由真实 GCC 求值。
  新增条件编译、重定义、未知正文、任意 C 语法等拒绝。版本字符串仍只是早期提示，不是放行依据。
- 包装单元只添加不执行的只读元数据，不修改实际采集源文件、DDR 地址、版本字符串或算法。
- 检查 BASE、LIMIT、GROUPS、WORDS_PER_GROUP、BYTES、PACKET、GUARD，以及真实编译的
  DDR_BASE/HIGH、sizeof(u32)、sizeof(UINTPTR)。
- 与 BD 的 TOTAL_SAMPLES、SAMPLES_PER_PACKET、XSA 中 PS DDR/HP0 可达范围、
  DMA 长度寄存器位数一致；数据长度、保护区、分包、对齐均检查。
- 从实际 ELF32 ARM 文件读取符号和区间，不把 nm 输出文字当依据。
  所有非空 SHF_ALLOC 区间、PT_LOAD 的内存范围（包含 BSS）、堆/栈和真实 end 均须位于 RX 前，
  end 必须覆盖这些分配。等于 RX 起点合法，超过即拒绝。
- 报告地址全部由校验后的编译合同生成。源码、包装单元、.i、.o、ELF、map、
  链接脚本、参考 XSA/BD、编译器及参数均留有绑定记录。
- 首版只放行原固定合同；不支持任意缓冲区搬迁或通用 C/ELF 布局。
  提供的 GCC/BSP/链接输入需可信；不是对恶意编译器的认证机制。

## 三类验证，分开记录

| 类别 | 本轮实际结果 |
| --- | --- |
| 修复前模拟反例 | 独立构造，复现旧入口假阳性；不是 B 原反例，也不是实板故障证明 |
| 软件测试 | 原 34 项文件不改，新增 29 项；合计 63 项通过 |
| 真实工具 | 当前配置真实 GCC 预处理/编译/链接通过；14 案例矩阵符合预期，另有同字节旧反例拒绝验证 |
| 完整硬件重建 | 本轮未运行；build_hw.tcl 未修改，原 run01～04 只保留历史自检身份 |
| 实板 | NOT_RUN；不新增采集、DDR 实板或整机结论 |
| B 的 21 项检查 | 本机指定资料搜索未取得原报告/脚本，未运行，不能写成通过 |

使用 xilinx-suite 指南区分编译、硬件构建和实板层级；
实际为 Vivado/Vitis 2025.2、Zynq-7020 Cortex-A9 standalone，不套用指南中的 A53 默认示例。

### 修复前后同字节反例

旧入口快照位于 ../evidence/run04/build_current.py，已核对与 050d06 的文件原字节相同。
其 SHA-256 为 b6414b73897fb7c3a518379c749469d20e7b4d7bd146c2a3760ed6cc927b477c。

[修复前反例](legacy-counterexample-01/counterexample-summary.json)：
CONFIG_VERSION 不变，BASE 改为 0x00100000，模拟 end=0x00112630，
旧入口返回 BUILD_PASS_NOT_BOARD_TEST。该目录的 XSA、ELF、工具等为明确标记的夹具，不能下载到板上。

[修复后真实编译结果](evidence/exact-legacy-after/result.json)：
完全相同源码字节配真实 BSP 和合法链接脚本，实际目标文件中的 BASE 为 0x00100000，
被 Unsupported changed fixed PS contract 拒绝，未进入硬件构建。
前后源码 SHA-256 均为 5a21c65da0f29707fafe64e7d1fe4c7382ef6d23e09598464a52bd0b0d394c32。

矩阵中相应 BASE 案例与此文本相同，但原始换行不同，因此没有冒称原字节相同；
专门增加的 exact-legacy-after 才是逐字节相同对照。

### 真实矩阵

最终结果：[matrix03/matrix-result.json](evidence/matrix03/matrix-result.json)。

| 案例 | 结果 |
| --- | --- |
| 当前合法配置 | 通过新增 PS 编译/链接合同检查 |
| 程序 end 恰好等于 BASE | 仅在隔离链接夹具中增大堆，真实链接后 end=0x01000000，通过 |
| BASE 改到程序区，版本不变 | 拒绝 |
| LIMIT 截断数据 / 扩大范围 | 两者均拒绝 |
| GROUPS 导致非整包 | 编译静态断言拒绝 |
| WORDS_PER_GROUP 改变 | 拒绝 |
| BYTES / GUARD 越界 | 编译静态断言拒绝 |
| PACKET 与 BD 分包不符 | 拒绝 |
| 两份 SDT DDR 宏一致改变 | 实际编译值与 XSA DDR 范围不符，拒绝 |
| 链接程序/栈进入 RX | 按实际 ELF 分配区间拒绝 |
| end 符号谎报低地址 | 因不能覆盖实际分配而拒绝 |
| 未知正文，版本不变 | 拒绝识别 |

保留 matrix01：DDR 夹具最初只改 xparameters.h，被 xmem_config.h 的重复定义先拦截，
未达到预期检查层，矩阵为 FAIL；不是硬件故障，也未改写为 PASS。
matrix02 同步改变隔离夹具两份宏后 13 案例符合预期；
matrix03 再加入真实 end=BASE 合法边界，共 14 案例（2 个合法通过、12 个反例拒绝）。
单元测试另覆盖 BD 总组数、每包组数改变、DMA 长度位不足、伪造文本 ELF、截断 ELF 等。

## 运行入口与完整命令

从 current_build/ 执行。所有输出目录必须不存在，不能复用已归档名字。

~~~powershell
$RepairPython = 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $RepairPython -B -m unittest discover -s . -p 'test_*.py' -v
& $RepairPython -B repair_ps_contract/reproduce_legacy_false_positive.py --source 'F:/College/verilog_digital_system/Vitis/four_mic_capture/src/main_four_capture.c' --output 'F:/College/verilog_digital_system/four_diagnostic_work/legacy_false_positive_next'
& $RepairPython -B repair_ps_contract/run_real_matrix.py --reference-plan evidence/run04/preflight.json --output 'F:/College/verilog_digital_system/four_diagnostic_work/ps_contract_matrix_next'
~~~

跨电脑需使用本机路径重新执行父 README 的 check，得到新的 reference-plan；
矩阵只借用该文件的输入位置，不从它读取缓冲区合同，每例都重新预检查并实际编译。
本机合法配置的完整 ps-check 命令及本轮各次调用见 [commands.json](commands.json)。
各例的实际编译/链接 argv 与工作目录位于对应 logs/*.command.json，矩阵顶层也保存各例完整调用。

- check：只读依赖及硬件形态，明确 PS 合同未验证。
- ps-check：真实 PS 编译/链接检查，不启动 Vivado；成功为 PS_CONTRACT_PASS_NOT_HW_BUILD。
- build：强制先执行同一 PS 检查，再构建硬件；无法跳过。新硬件还需匹配参考 BSP XSA。
  本轮只对这一阻断做编译/链接验证，没有把历史硬件构建重新标成通过独立复核。

## 产物、保存位置与限制

最新合法配置结果：[legal-ps-02/result.json](evidence/legal-ps-02/result.json)。
实际 end=0x00112630，RX=[0x01000000,0x01100000)，数据末端0x010FA000，
保护区末端0x010FA040，32000组、1024000字节、每包8000字节、128包。
这些地址从实际编译值与 ELF 提取，不再由报告模板填入。

完整受控输出均在 F:/College/verilog_digital_system/four_diagnostic_work/：
current_ps_contract_20260912_01/02、ps_contract_matrix_20260912_01/02/03、
ps_contract_exact_legacy_input_01、ps_contract_exact_legacy_result_01。
前四次 current_rebuild_20260912_01～04 未覆盖、未删除。

本目录收录原字节结果、日志、命令及实际入口快照。
[compiled-proof](evidence/compiled-proof/) 另外保存最终合法构建的真实 .o/ELF/map，
以及同字节拒绝反例的真实 .o；可直接解码检查，不只依赖 JSON 或日志文字。
它们仅用于本次编译证据检查，不是已经过实板验证的下载发布包。
预处理 .i 含工具/BSP 头文件展开，其他案例的 .o/ELF/map 和完整 BSP 夹具保留在上述受控目录，
不把整套工具库重复打包；各自 artifacts-sha256.json 是相对于原完整输出目录的索引。
新有效文件的 SHA-256 见 REPAIR-MANIFEST.json（排除清单自身）。

在 current_build 目录执行以下只读交付检查（依赖原 F 盘证据位置仍存在）：

~~~powershell
& 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B repair_ps_contract/check_repair.py
~~~

检查包含 189 份冻结文件、旧清单中未修改的 90 项、四次历史构建产物、实际输入，
以及修复后的真实对象/ELF、14 案例矩阵、63 项测试、语法、空白与新哈希清单。
--record 仅首次生成最终检查日志和清单，已有目标即拒绝；后续复核使用不带该选项的只读命令。
Git 长路径选项仅对校验进程生效，不修改全局设置；后续工作执行处理深路径证据时
同样使用 git -c core.longpaths=true，避免 Windows 默认路径限制。
校验允许后续待审提交是原基线的后代，不依赖 HEAD 永远停在修复前 SHA。

原 RESULTS.md、原 ENVELOPE-SHA256.json 和 evidence/ 原件不重写。
旧清单属于 050d06 快照；当前修改的入口/说明应使用新 REPAIR-MANIFEST，而非覆盖旧清单来掩盖差异。
实际 one、PS 采集源码、BSP 和 189 份冻结原件保持不变。

剩余：B 的独立复核及原 21 项检查（待取得）；未做新硬件构建或实板验证。
这些未做项不被追加为 9 月 16 日门槛。
