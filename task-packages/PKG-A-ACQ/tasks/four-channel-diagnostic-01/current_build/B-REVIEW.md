# B 复核：PS 编译合同修复及当前四路安全构建入口

2026-09-12。**结论：通过，关闭上轮唯一P2阻断。** 批准仅限本current_build中的安全构建入口、PS合同校验及相关证据；不代表新硬件构建、实板、定位、音频、整机、正式M1/H3或9月16日阶段验收，不新增诊断门槛。

## 固定版本与实际环境

- 审核SHA：`d0ce1c28aac3e101a262036b2321f4170d34f45c`。
- 原阻断SHA：`050d06f5dc6fed4fa476e72fa416e9736bc7fef3`；原问题为实际PS BASE变化仍按固定地址输出BUILD_PASS。
- 分支：codex/toph/four-channel-engineering-review-20260912。
- fetch重试后成功，直接ls-remote核对分支头为审核SHA。独立detached工作区 `F:/NUEC/review-worktrees/a-ps-repair-d0ce1c2`。
- 按repair_ps_contract/README → commands.json → REPAIR-MANIFEST及证据顺序审查，未运行--record或改写旧清单。
- Windows PowerShell，Python3.12.14：`C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`。单测及独立检查不需要AMD工具。

## 实际命令与结果

在固定副本current_build执行：

```text
python -B -m unittest discover -s . -p "test_*.py" -v
```

63/63通过，即原34项＋新增29项。原test_build_current.py未修改。

B额外执行：

```text
python -B F:/NUEC/review-evidence/a-ps-repair-d0ce1c2/replay_b_regressions.py
python -B F:/NUEC/review-evidence/a-ps-repair-d0ce1c2/verify_repair_evidence.py
```

实际运行脚本、日志与原反例副本保存到b_review_evidence；其中绝对路径为本次运行位置，不是构建入口默认依赖。复用这些审计脚本时应按其明确变量定位固定Git副本及历史B原脚本，选新输出目录；无需复活A原盘或覆盖归档输出。

- B上轮原始反例脚本保留原字节，旧版本复跑只改输出位置，仍复现错误BUILD_PASS。
- B上轮21项等价断言保留原逻辑，只将被测模块路径指向新SHA，21项全部通过。不是沿用A结论。
- 对新入口复用B的真实源码BASE变更刺激，执行实际compile_bound_ps和validate_values；硬件合同来自合法归档，编译动作由真实归档拒绝对象代替，得到BUILD_FAILED / Unsupported changed fixed PS contract，且没有调用hardware。仅模拟编译阶段产物供应，未mock合同校验函数，未称新GCC复编。
- 被测BASE反例源SHA为 `5a21c65da0f29707fafe64e7d1fe4c7382ef6d23e09598464a52bd0b0d394c32`。原B脚本和A前后同字节反例记录相符。

## 原阻断如何关闭

1. 已知采集正文指纹固定，七个宏表达式只接受有限词法，未知正文、重定义/条件变化不靠版本字符串放行。
2. 将采集源码include到同一翻译单元，在同一单元加入不执行的只读合同数组。一次GCC预处理得到.i，实际编译此.i为.o，链接仅使用这个.o；不是另一份JSON旁置声明。
3. 直接从ELF32 ARM对象和最终ELF读取合同，验证对象/ELF一致；nm文本不再作为end判据。
4. 编译出的BASE/LIMIT/GROUPS/WORDS_PER_GROUP/BYTES/PACKET/GUARD、DDR宏及ABI共同与BD/XSA/DMA范围核对。仅固定原合同受支持，不能借表达式改变固定值。
5. 所有非空SHF_ALLOC及PT_LOAD内存区间（包含BSS）、程序end和RX前区间均核对；end必须覆盖真实分配，且end=BASE合法。报告地址由验证后的值生成。
6. build_current.py在ps_only分流和Vivado之前无条件调用合同检查；检查失败即停止。完整build没有通过正常CLI绕过它的路径。

原冻结PS布局本就正确，本次关闭的是参数化入口的边界假阳性。信任边界仍是可信GCC/BSP/链接输入与明确支持的源码和链接布局，不能外推为任意恶意工具或自定义链接脚本认证。

## 归档二进制与矩阵

compiled-proof包含合法真实.o/ELF/map以及拒绝反例真实.o。B用独立struct解析和作者解析器分别读取对象/ELF：

- 合法对象与ELF七项合同一致：BASE=0x01000000，LIMIT=0x01100000，GROUPS=32000，WORDS_PER_GROUP=8，BYTES=1024000，PACKET=8000，GUARD=64。
- ELF实际end及ALLOC/PT_LOAD最大末端=0x00112630；heap/stack及归档实际堆栈符号均在RX之前。map与ELF相符。
- 对象/ELF/map SHA与legal-ps-02 binding记录相符；拒绝对象直接解码BASE=0x00100000。
- 旧模拟反例公开源码实算SHA，与exact-legacy-after preflight的真实编译输入SHA相同；未声称访问A原盘读取两份源文件逐字比较。
- matrix01的DDR重复定义失败保留；matrix02的13例、matrix03的14例均按各自历史身份保存。matrix03有2合法/12拒绝，包括end=BASE、程序/栈越界、伪低end等；日志与result一致，不把失败改写成成功。

其他矩阵案例（含end=BASE）的.o/ELF在A受控目录，公开包没有全部二进制；B对此核对日志/结果/哈希索引，未重新编译矩阵，不能把归档审查称独立真实重编译。

## 清单及原件范围

- 相对050d06f确有714个变更文件（4修改、710新增），全部限定current_build；逐文件工作区字节与Git blob一致。
- 新REPAIR-MANIFEST的713项大小与SHA通过，排除清单自身；不覆盖新增B记录。
- 原ENVELOPE属于050d06f，94项中未改90项核对通过；变化为.gitattributes/.gitignore/README.md/build_current.py，使用新清单。原ENVELOPE、RESULTS及evidence历史文件未改写。
- 原189份冻结材料大小、SHA及前后Git身份一致。build_hw.tcl未改，BD/wrapper/CTI原规则通过B21项回归。

## 未验证项

B本机没有A实际one、AMD2025.2、匹配BSP/XSA、实际PS源及原构建目录；不运行依赖这些位置的check_repair.py，也不照抄参数重建替代输入。没有重新做真实GCC矩阵、完整Vivado构建、BSP重建或上板。

原run01–04是历史硬件构建自检；本次不提升其身份。外部IO、同步/采集、声学精度及A原盘118项实际输入/构建产物核对须由A负责，B未代签。

## Standards

未发现新增阻断。源码、对象、ELF、命令与归档身份分开，失败记录保留；独立解析二进制支持合同一致性。任意自定义堆栈符号/链接布局不在本次通用认证范围。

## Spec

原BASE假阳性机制关闭，无已证实未关闭阻断；B原反例、21项补充检查、63项单测及清单/归档证据检查完成。两个轴均无阻断，批准范围严格限安全入口和PS合同校验。

## 集成与批次收尾

候选使用入口保持本current_build，不迁移到活动RTL，不覆盖实际one。合入以前直接远端main为228b8e3714e773712574b79f632a09d12be5eb4f；实际本地main位于 `F:/NUEC/review-worktrees/member-b-to-a-pkg-b-alg`，原add40fd落后4提交且工作区干净，已安全快进后按限定范围合并。

本报告与b_review_evidence为B新增回执，不属于A清单；原记录保持原字节。最终main对齐、发布后验证、本批材料计数及清理结果在后续本节批次记录中追加，不以合并成功替代收尾。

### batch-closeout 实际回执

| 项目 | 结果 |
|---|---|
| 合入提交 | `9f0bd3724d2c986bdadc7b100270e0d46ab2afa9`，非强制推送main，包含准确批准d0ce1c2；相对合入前main只有current_build变化 |
| 合并后验证 | main实际工作目录重跑63项测试、189原件验证、714个修复blob和713清单核对均通过；日志06/07及post-merge-evidence-verification.json已保存 |
| 三方main对齐 | 发布后本地main、origin/main、直接ls-remote main均为9f0bd3724d2c986bdadc7b100270e0d46ab2afa9，领先/落后0/0；本记录补交后再次核对最终SHA，并在用户回报中给出 |
| 实际main工作区 | F:/NUEC/review-worktrees/member-b-to-a-pkg-b-alg，发布后跟踪修改0、未跟踪0，本批忽略项0；全部批准材料已在此正常版本管理 |
| 其他共享工作 | F:/NUEC/develop仍在feature/member-b-algorithm，52项已跟踪差异、146未跟踪；本批current_build差异/忽略项0。保留其他任务，不切换/重置、不混入本批，不声称整个共享目录干净 |
| 本批有用材料 | 入口/修复/作者证据+B-REVIEW和b_review_evidence已入main；审计时的外部原始回执与API获取记录保留F:/NUEC/review-evidence/a-ps-repair-d0ce1c2供追溯，不是另一份活动工程。完整无关工作文件名清单只在本地留存，其哈希见batch-closeout.json |
| 遗留数量 | B本批未提交/未跟踪/忽略的未处理有用内容0；未说明材料去向0。无关工作52/146不算本批遗留 |
| 已清理 | 仅本轮新建、干净且无忽略独有文件的审核worktree F:/NUEC/review-worktrees/a-ps-repair-d0ce1c2；可由准确审核SHA重建。执行脚本中该路径是历史运行位置，重新运行前可恢复固定副本 |
| 保留/责任 | A原分支头仍d0ce1c2；分支/pub仍可能关联采集准备，未确认任务结束故不删除。A实际one、旧四次构建、修复编译矩阵和原盘核对由A确认，不由B删除或代签。旧B阻断证据保留供追溯 |
| 最终状态 | B侧本批批准、集成、相称验证和收尾完成；A侧继续任务及本机材料核对待A负责，未冒称跨机器同步/构建或阶段通过 |

本次归档源码没有修改实际one、活动RTL或采集数据；原ENVELOPE、RESULTS及历史失败证据保持其原版本身份。
