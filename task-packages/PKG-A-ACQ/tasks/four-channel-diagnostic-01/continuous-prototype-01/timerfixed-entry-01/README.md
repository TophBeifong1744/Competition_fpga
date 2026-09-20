# 计时修复版统一入口（增量候选，2026-09-16）

> **最新待审：TF-B-02-R1**。17afe32 经 B 复核仍有一项链接参数比较阻断；本轮修复、94 项测试/14 次 Tcl 模拟、原件映射及复跑命令见 [repair-02/README.md](repair-02/README.md)。以 `repair-02/verify_repair.py` 核对新清单；下段 repair-01 的封闭清单检查仅适用于固定 17afe32 树，新脚本逐项核对其原件映射，不改旧清单。未获 B 对本轮批准，未部署到实际工程，不合入 main。

> **B反馈修复候选**：check_entry.py、load_timerfixed.tcl已针对TF-B-01～03修改；最新入口、测试、限制及复跑方式见[repair-01/README.md](repair-01/README.md)。旧README原字节在repair-01/originals/README.md。以下正文及原OPERATOR/BUILD-RESULTS、87项旧清单属于bbe39c3历史记录，不代表修复已获批准或部署。新清单用repair-01/verify_repair.py核对；旧delivery_manifest.py仍是旧版封闭集合检查器。

状态：**拓芙已于2026-09-16 18:23完成原应用的新编译、链接；实际对象/ELF/map及受检加载dry-run核对通过。未连接、下载或运行板卡，等待工作执行检查和B独立复核。** 本轮结果与回报见 `BUILD-RESULTS.md`，不沿用历史构建充当本轮结果。

## 依据与不变项

按 Git 对象 `f4fc899462a715bd878ee05d6bbb935b10b47651` 完整读取 B-REVIEW.md、publication/README.md、board-run-20260915-02/README.md；作者 `88805ee415f137998b59b7cb197f2eeb988d17b7` 是该合并祖先。批准范围是原型及已有修复版实板记录，不含本入口的新批准。

用户已选择复用 F 盘 `continuous_platform` 和 `four_mic_continuous`。本轮不改PL/BD/XDC/CIC、格式、分包、DDR或两槽所有权，也不修改历史根ps、run.py、load_candidate.tcl、delivery-01/release、B报告和旧清单。

共享工作区仍在main=`57c50e6c99731cd57e7738ac91b02f985ad229b1`；本地origin/main=`8371f014711e04553749e6c2ffc29f34b9d5ccc9`，main相对其落后24提交。存在其他未提交工作，未切换/重置/合并/fetch。实时ls-remote的Schannel查询报SEC_E_NO_CREDENTIALS；另用单次OpenSSL参数查询仍退出128，未获得实时远端SHA。不能把本地跟踪值称为实时远端。所需批准对象已本地存在，以上核对不依赖共享目录有没有B报告文件。

## 唯一有效源码及配套

| 内容 | 入口/合同 |
| --- | --- |
| 冻结源依据 | 相邻 `board-run-20260915-02/ps`；实际应用src必须逐文件匹配POLICY.json，不使用根ps旧main |
| 实际应用 | `F:/College/verilog_digital_system/Vitis/four_mic_continuous` |
| 平台 | `F:/College/verilog_digital_system/Vitis/continuous_platform`；standalone_ps7_cortexa9_0，Cortex-A9 #0 |
| BSP | 上述平台 export/continuous_platform/sw/standalone_ps7_cortexa9_0；88项头文件/库/根配置SHA绑定 |
| bit/XSA/初始化 | 同一获批实录硬件：bit b15991bc…、含bit的XSA b84e9363…、ps7_init.tcl a158fcc7…；全SHA在POLICY.json |
| 编译 | 当前Vitis2025.2、ARM GCC13.3.0，单一main.c编译单元包含两个C文件；SDT、Cortex-A9、VFPv3、hard float、C11、O2、g3 |
| 链接 | 现有lscript.ld，DDR程序区域[0x00100000,0x01000000)；保持map/cref，链接相同BSP库 |
| 缓冲 | RX=[0x01000000,0x01100000)，250组/包、8字/组、8000字节/包，两槽各8064字节含64字节guard，总16128字节 |

BSP的88项哈希是本轮只读观察绑定，不是重建BSP或B对完整环境的新批准。本首版只支持已核对的当前工具/编译命令布局；路径通过参数传入，未知布局、宏、BSP或工具配置拒绝，不声称任意安装环境均可移植。工具路径不匹配不能靠关掉校验来通过。

## 新入口及检查内容

1. `vitis_gate.cmake`：用户在实际应用CMakeLists末尾include。每次Build先执行pre源/BSP/硬件检查；实际链接后执行post，失败使构建返回错误。脚本不自行调用编译器构建应用。
2. `check_entry.py`：复用current_build的安全文件、日志及Elf32解析器，不调用其旧PS构建合同，不调用旧run.py build/load。
3. `load_timerfixed.tcl`：新的受检加载入口；source只定义过程，默认dry_run=1。调用时先执行load检查，非零立即返回，不connect/reset/download。仅明确传0才操作硬件，本轮不要求这样做。

`pre` 将实际源码、配置及BSP绑定到修复快照，拒绝旧表达式、额外编译单元/影子头文件和缺依赖；CMake主体仅允许原版加本检查include。

`post` 检查真实compile_commands（宏、选项、包含路径、specs及工具），实际.o/ELF的64字节合同，全部ALLOC/PT_LOAD与程序末端、map和BSP库路径。读取实际局部now_us符号，比较获批对象计算指令，解析ELF的真实XTime_GetTime/除法调用目标与literal装载地址，除数必须333333343；不是只搜版本字串或任意位置的常量。只允许受支持的ARM指令序列及调用地址重定位，未知优化/指令布局拒绝。

`load` 再执行上述检查，核对Vitis启动配置必须选本应用ELF、匹配bit和ps7_init、Local/Zynq/Cortex-A9 #0，且要有本入口post成功记录、相同源码和对象/ELF哈希；仅历史audit通过不能放行加载。旧计时ELF、旧release路径或在检查后被替换的产物均拒绝。

GUI直接Run本身不提供本脚本不可绕过的安全承诺。以后需要受检加载时使用本目录Tcl入口；本轮只核对配置和dry-run，不要求真实Run。操作者绕开新入口使用旧脚本仍可能加载旧固件，因此旧入口明确不在本次工作流内。

## 证据、输出保护与新编译判别

- 每次调用生成一个时间+随机ID的新子目录，请求、外部工具argv/输出、结果或failure单独保存；从不重用/覆盖旧记录。
- Vitis接入后默认记录在应用 `c1_checks`，在build目录之外，Clean不会清掉检查记录。拒绝记录目录与src/build/_ide、平台、历史release/实录或检查器依赖重叠。
- pre记录编译前对象状态，post报告 `fresh_compilation_observed`。本轮请Clean应用后Build以得到实际新编译；增量链接复用旧对象不被冒称新编译。
- 准备阶段audit的ELF是获批的ebc576e2…，标记HISTORICAL_ARTIFACT_AUDIT_ONLY，不是本轮新构建。本轮新ELF为726a91fe…；完整字节对比仅27字节变化：编译日期/时间7字节、GNU build-id20字节，指令字节未变。证据见新构建快照。
- 记录中的配置路径不是独立授权合同：缓冲、时限、计时计算另从对象/ELF验证，地址不从操作者JSON直接照抄。

## 已运行的检查（原始输出见evidence）

| 检查 | 实际结果/边界 |
| --- | --- |
| 新入口Python单测 | 18/18；含16个合同字段变异子例、旧真实ELF、旧表达式、计时指令/除数变异、路径/CPU/连接/配置错配等 |
| 新Tcl加载入口 | 原生Tcl运行4个模拟案例：source无动作、默认dry、校验拒绝先于connect、正确调用顺序；所有硬件命令被mock，没有上板 |
| 保留候选入口测试 | 10/10，本次实际重跑 |
| 保留current_build安全测试 | 34/34，本次实际重跑，含其模拟工具/负例；不是34次真实构建 |
| 当前实际文件audit | 88项BSP依赖、获批源/硬件、真实.o/ELF/map及加载配置核对通过；只对现有产物只读检查 |
| 未接入hook的pre检查 | 预期拒绝、退出1；证明不能拿历史audit直接当受检Build |
| 新Vitis Clean/Build | 用户已执行；pre对象不存在，post观察到新编译，真实对象/ELF/map核对通过；新ELF 726a91fe… |
| 实际新产物加载预检查 | 原生Tcl调用真实Python检查器，针对当前F盘产物及复制的真实pre/post记录通过；硬件命令额外禁用，不使用模拟ELF |
| 新硬件下载/采录/RTL仿真/综合实现 | 本轮未执行，不要求重复已有实板采集 |

失败保留：entry-tests-01.log记录测试自身把Windows短路径与解析后的长路径直接比较而失败；改为解析同一实际路径后复跑entry-tests-02.log通过。初次尝试Python内置Tcl缺init.tcl，未安装新环境；后改用现有AMD Git附带Tcl，mock测试通过。历史首次计时失败和旧包证据均未修改。

## 当前停止点

工程实现已完成本轮源码/构建/加载绑定的自检和证据整理，现在交工作执行检查，由其发布待审SHA交B复核。本轮无需再次Run；没有提交、推送、合入或宣布本入口获独立批准。用户贴回的Vitis输出是尾段，不称完整控制台日志；已另存完整pre/post检查记录、实际生成命令、Ninja执行索引、对象/ELF/map与源码配置。

`PREPARATION-SHA256.json`保留准备时快照，不改写成完成时清单；其中README/OPERATOR旧版本原字节在 `user-build-20260916-01/preparation-docs`。本轮当前文件以 `DELIVERY-SHA256.json` 为交付清单。检查仍包含src下编辑器缓存的哈希，缓存变化也可能保守拒绝；遇到拒绝应保留记录定位，不关闭检查强行加载。

完成后的范围仍是计时修复版可核对构建/加载入口；不扩大B原批准，不属于正式M1/H3/长稳。旧冻结包未动；撤销本次工程接入只需用户移除CMake末尾3行并重新配置，**保留已修计时源码，不换回旧ELF**。
