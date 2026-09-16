# 首次ARM构建后的计时检查误拒绝修复

2026-09-16。用户Build ID=6c8d0172-45ee-4de7-8ca9-c370000c1d22，20:45:18～20:45:20。编译、链接和size输出成功，后置检查报Object timer code differs from fixed computation，整次Vitis构建因此返回失败；不能把这次失败写成原构建成功。

## 根因

原E1适配器复用C1检查器的对象计时函数原始字节比较。增加E1程序后，now_us从对象地址0x290移动到0x2bc，仍是完全相同的27条运算/调用/返回指令，但编译器为8字节除数常量池所做的对齐变化：

| 项目 | 固定C1参考 | 此次E1实际产物 |
| --- | --- | --- |
| 对象now_us | 0x290 | 0x2bc |
| ELF now_us | 0x00100738 | 0x00100764 |
| 常量池相对函数起点 | 112字节 | 108字节 |
| ADD r3,PC,#imm | #16 | #12 |
| 返回后的对齐NOP | 一条 | 无 |
| 常量池64位除数 | 333333343 | 333333343 |

因此直接比较整个函数字节会误拒绝；旧timer_code也只支持#16，不能只删掉前一个检查来修。源表达式仍为t * 1000000U / (COUNTS_PER_SECOND)，未改回旧计时表达式。

## 修复边界

仅修改本E1目录check_endurance.py并新增timer_layout.py、测试及本证据。不改实际F盘应用/源码、PL、BSP、旧timerfixed-entry-01或历史冻结对象/ELF，不后台重编译。

- 新验证器只接受已明确的两种ARM常量池对齐布局，不开发通用反汇编器。
- 要求精确27条指令形状；仅规范化经计算证明正确的池偏移和经验证的调用位移。#12/#16必须实际寻址到函数内8字节对齐常量池；可选填充必须是指定NOP，除数高低字都检查。
- 对象中两处R_ARM_CALL必须精确引用XTime_GetTime和__aeabi_uldivmod，禁止额外函数内重定位、错符号、错类型或不同addend。
- ELF实际调用目标及ARM/Thumb模式必须与符号一致；规范化后的全部运算/返回指令必须与固定参考一致。不是任意忽略NOP、地址常量或函数哈希更新。
- 原16字段RX/分包合同、E1十字段合同、11段实际调度表、源码/编译配置、map/所有分配及加载区间检查保留。
- pre/post/load记录新增本E1检查器及CMake入口哈希绑定；检查器变更后不能复用旧成功记录当新放行。

## 证据和实际验证

before保存修复前E1检查器和POLICY。records保存本机20:42及20:45两轮真实pre/失败post原件；build和src保存20:45实际产物/相关配置。旧失败不覆盖、不删除。新ELF SHA-256=f4ebe8462c103b5c32776917e88993cca3808b2775410170423487ea8d2c56f4，程序end=0x00113890，未侵入0x01000000起始的RX。

verify_fix.py执行12项新增布局测试（含双布局正例、原始误拒绝复现、运算/除数高低字/池寻址/NOP/调用目标/重定位负例），全部通过；本批原7项配置/合同测试重新运行通过。完整命令、退出码、输出和新旧反汇编/重定位保存在recheck_*目录。

对用户此次生成的真实对象、ELF、map和当前源码/BSP再跑完整pre/post，通过E1_ARTIFACT_PASS_NOT_LOAD_NOT_BOARD。此次是**事后只读复查，不是重新构建**，日志fresh_compilation_observed=false；原用户构建仍保留失败状态。证据在本包evidence/recheck_*，本目录相应result.json指向该位置。未执行加载配置检查、下载、实板、RTL仿真或综合实现，不宣称5分钟测试或独立复核通过。

## 用户下一操作

不用再复制C文件，不改计时宏、优化等级或POLICY。检查脚本是现有CMake引用的仓库路径，已更新。由用户只对four_mic_endurance再Clean→Build，得到同一次Vitis调用中的新pre、实际新编译和post通过；不要Clean平台或原应用，暂不Run。预期末尾E1_ARTIFACT_PASS_NOT_LOAD_NOT_BOARD和Build Finished successfully。构建后再检查真实产物与配置。

复现本次只读测试：用现有Python运行本目录verify_fix.py，每次生成新recheck目录。FIX-SHA256.json是本次修复时点的增量文件清单，不重写原PREPARATION清单；后续新运行需追加新的时点清单。没有提交、推送或合入。
