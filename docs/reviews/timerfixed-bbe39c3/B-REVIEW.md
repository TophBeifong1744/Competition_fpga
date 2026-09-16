# B 独立复核：计时修复版构建／加载入口增量

2026-09-16，结论：**需修改，不合入 main。** 归档和这次真实产物的数值核对通过，但入口还存在两项 P1 和一项 P2 问题，不能批准本轮受检构建／加载入口。此前对 `88805ee` 的限定批准不变，不自动覆盖本入口。

准确审核 SHA：`bbe39c38dc36ccb4c0492f492b86f6c46d885fbe`；父提交：`8371f014711e04553749e6c2ffc29f34b9d5ccc9`；分支：`codex/toph/timerfixed-entry-20260916`。

唯一范围：`task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/timerfixed-entry-01/`。独立工作树 `F:/NUEC/review-worktrees/timerfixed-bbe39c3` 固定准确 SHA；本报告、命令和反例均在包外 `F:/NUEC/review-evidence/timerfixed-bbe39c3`。作者 88 文件、清单、生成配置及旧包均未修改。

## 来源与实际执行

Git ls-remote/fetch 遇连接重置/超时；GitHub 连接器和未认证 API 返回404。随后使用 Git 已保存凭据访问官方 GitHub API，凭据仅在进程内使用，没有写入或打印。API 分支查询在获取前后均指向准确 SHA；通过官方 API 取回 93 个缺失 Git 对象，每个 tree/blob/commit 都按 Git 原始对象算法验证 SHA，再写入本机对象库。没有把下载来的文本冒充 Git 提交。证据：`api-ref.json`、`api-commit.json`、`api-fetch-result.json`；脚本 `fetch_git_objects.py` 不修改共享分支或工作树。

先在独立工作树的父提交执行旧 `publication/verify_package.py`，221 项／222 文件通过；再固定新提交，按 BUILD-RESULTS.md→README.md→OPERATOR.md 顺序读取后检查源码、二进制和证据。新目录使旧封闭集合检查不再适用于整个新父包，B 没有修改旧清单；另逐项验证旧 221 项与父提交清单原字节未改。

Python 3.12.14：`C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`；原生 Tcl：`F:/STUDY/IT/Anaconda3/Library/bin/tclsh.exe`；额外独立 ARM 解码使用本机已安装 Capstone 5.0.6。没有安装或调用 AMD 构建工具，没有访问 A 的 F:/College 工程。

`PY` 表示上述 Python；`ROOT` 为独立工作树；`PACKAGE` 为审核包绝对路径；`EVIDENCE` 为本报告目录。实际命令和工作目录：

```text
在父提交仓库根：
PY -B task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/publication/verify_package.py

固定新 SHA 后，在 PACKAGE：
PY -B delivery_manifest.py
PY -B -m unittest -v test_entry

在 ROOT：
PY -B -m unittest discover -s task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/tests -p test_entry.py -v
PY -B -m unittest discover -s task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/current_build -p test_build_current.py -v

在包外：
PY -B EVIDENCE/audit_archive.py ROOT
PY -B EVIDENCE/standards/run_tcl_checks.py
PY -B EVIDENCE/standards/reproduce_artifact_race.py
PY -B EVIDENCE/negative_contract_checks.py PACKAGE EVIDENCE/negative-run01
```

后两个反例程序的原输出已存在，复跑请为 negative_contract_checks 另取新输出目录；竞态程序请复制到新的包外目录后运行，不覆盖现有结果。作者一次性 `verify_user_build.py`、`explain_elf_difference.py` 没有直接重跑，没有覆盖其 verification-01。

| 检查 | B 实际结果 |
| --- | --- |
| 提交范围／原字节 | 仅新增指定目录 88 文件，逐 Git blob 原字节一致；87 项 DELIVERY 清单与精确文件集合通过 |
| 历史证据 | 旧 221 项未变；32 项准备清单按原映射通过，旧 README/OPERATOR 从 preparation-docs 对照 |
| 快照与依赖 | 26 个 app 快照与 snapshot-binding.json 一致；7 份固定源码与已批准修复原件同字节；两个复用 helper 哈希通过。88 项 BSP 原文件未在 B 机获得，不声称独立核对其实际磁盘内容 |
| 新 Python 测试 | 18/18 通过，包括作者的合同字段变异子例；entry-tests.txt |
| 父包／安全单测 | 10/10、34/34 通过；parent-entry-tests.txt、safety-tests.txt |
| 作者 Tcl 模拟 | 4/4 通过；standards/author-four-mocks.json |
| B Tcl 补充 | 7 组通过，含11种非法dry值、空格/字面元字符、cwd变化、实参以及10种步骤失败停止；另真实 Tcl→Python 缺失应用检查在硬件调用前拒绝 |
| 归档真实产物 | 新 ELF／对象哈希、计时、16字段、内存、27字节差异通过；archive-audit.txt |
| B 负例 | 2种无效 ELF 启动入口被接受、2种不同 GCC 配置被判相同；negative-run01/result.json。2种检查后 ELF 替换仍进入 mock dow/con；standards/artifact-race-results.json |

这些测试结果不能抵消下述未覆盖的入口缺陷。并行需求检查草稿未完成执行，`spec/reproduce.py` 不计入覆盖；主审实际运行的无 mock 反例是 `negative_contract_checks.py`。规范轴完整记录见 `standards/STANDARDS-REVIEW.md`。

## 需求轴：两项需修改

### TF-B-01 — P1：ELF 启动地址未验证，链接错配可通过二进制合同

位置：`check_entry.py:92-108`，尤其 `103-107`；实际编译/链接检查段 `204-224`。

`verify_elf` 核对合同、now_us、end、ALLOC/PT_LOAD 范围，但没有检查 `exe.entry`。B 以归档真实新 ELF 为原件，只在包外副本修改 ELF32 `e_entry` 字段：原入口 `0x00100000`，改为 RX 起点 `0x01000000`（仅2字节变化），或0（仅1字节变化）。两者都不属于任何实际 PT_LOAD；未经修改的 `verify_elf` 均接受，返回计时／内存合同成功。对象文件和其余 ELF 字节均未改，没有 mock、编译或运行固件。

入口可由链接器 `-e` 参数改变，而当前入口不绑定实际链接命令／选项；map检查只核对end、DDR区域和指定三种BSP库，不建立启动入口约束。因此不能据已检查合同声称错配链接配置已被拒绝。这里证明的是检查器的接受缺口，并未声称 A 实际交付 ELF 的入口有误，亦未实际执行一次带错误参数的 ARM 链接。

修改要求：绑定受支持的实际链接配置；检查 ELF entry 的模式/地址、与可执行 PT_LOAD 及预期启动符号的对应关系，拒绝 RX、零地址、其他未加载区域和不支持的启动入口。若只支持当前固定布局，应按该合同严格拒绝未批准变化。补充对应负例，保留本次真实产物原件。

证据：`negative-run01/result.json`。RX入口副本SHA为 `182dd83ce3ea97e8ae7e62b3172aac9f11ac2ac671716f2399d31eb281f86af8`；零入口副本为 `940a9f8002b814ea67289a673840b0a6816ee4bdcefcaa2e89f97777da47f278`。这些是 B 专用无效测试输入，绝不可下载到板卡。

### TF-B-02 — P2：整条编译命令 casefold 丢失 GCC 配置语义

位置：`check_entry.py:140-145` 及调用处 `204-208`。

Windows 路径可以按平台规则比较，但 GCC 选项和宏名区分大小写。B 直接调用原 `normalize_command`，将 POLICY 的 `-DSDT` 改为 `-Dsdt`，或 `-U__clang__` 改为 `-u__clang__`，两组比较均为相同。前一组改变宏名；后一组从取消宏定义变成不同的选项含义。未调用编译器，也未修改 POLICY；这是比较器本身已复现的语义缺口，不声称这些改动生成了某种实测 ELF。

修改要求：按实际工具参数规则解析并比较命令，只对已识别路径做必要规范化，保留选项、宏名和值及字符串参数的大小写/引号语义；补充这些负例。不能靠全命令转小写声明未知宏/工具配置会拒绝。

证据同 `negative-run01/result.json`；需求轴总计2项需修改。

## 规范／加载行为轴：一项需修改，一项维护观察

### TF-B-03 — P1：检查字节与实际下载字节未固定

位置：`load_timerfixed.tcl:8-9`、`16`、`18-25`。

Python检查结束后，Tcl依次connect/reset、等待3000ms，再按活动路径重新读取bit、初始化脚本和ELF。此间并发构建或其他正常文件替换可改变待加载产物。B 在 `after` mock 中替换 ELF，原 Tcl 仍执行 `dow` 和 `con`：

- 检查的新ELF为 `726a91fe…`，替换为旧错计时实录ELF `7b5630de…`；独立再检查该替换文件会因错误计时除数拒绝，但 mock dow 实际读到了它。
- 替换为另一合同有效但与这次构建收据不同的旧修复ELF `ebc576e2…`，同样继续到 mock dow/con。

反例使用实际 Tcl 和真实归档 ELF；初始检查真实调用 `verify_elf`，其余完整gate条件模拟满足，全部硬件命令mock。没有 ARM 编译、真实下载或板测。问题是受检加载流程内部的文件竞争窗口，与操作者另点GUI Run绕过入口的已知边界不同；也不依赖把README“检查后替换拒绝”解释为涵盖任意恶意操作者。

修改要求：校验并使用同一受保护产物集合，至少包含ELF、bit、初始化脚本，并与并发构建/写入协调，使下载所用字节就是已核对且绑定post收据的字节。单在dow前增加一次hash仍有重新打开文件的窗口，不能宣称已经固定该绑定。保留默认dry、错误先于硬件动作等现有行为，并新增并发替换拒绝或使用已封存正确快照的回归。

证据：`standards/artifact-race-results.json`、`reproduce_artifact_race.py` 和各Tcl/JSON原输出。规范／加载行为轴1项需修改。

非阻断维护观察：Python和Tcl分别硬编码相同产物路径；作者原Tcl测试仅检查调用顺序，未断言全部路径实参。当前实参经B检查一致，可在修复TF-B-03时补充共享合同和参数断言，不作为额外验收门槛。

## 已确认的归档产物事实与覆盖边界

新ELF确为 `726a91fe19fd9b9e67cca6f3c8668bf484df92d1bbb2ec2e5f2619cc0237324c`，新对象为 `0fc486cf671402f1d62041e94e8ec947ebc24961f852114f03ba4baed04f6469`。实际16项合同与声明一致，`end=0x00112640`，所有ALLOC/PT_LOAD均在程序DDR内且不重叠RX `[0x01000000,0x01100000)`；两槽16128字节、250组/包、10000000微秒目标不变。

独立Capstone读取新ELF：`now_us` 实际从 `0x001007a8` 读取64位除数333333343，调用实际XTime_GetTime与除法符号；对象now_us代码与原修复对象同字节。没有仅靠banner或版本字符串判定。

新旧ELF都为296612字节，节表/布局一致；逐字节比较只有27处不同。`.rodata` 两个实际日期/时间字符串有7字节变化；`.text` 中链接器标为 `.note.gnu.build-id` 的 `0x00106478` 是长度36的合法GNU note，20字节build-id内容改变。除此之外全部字节相同，未把这20个元数据字节当成CPU指令变化。

新pre记录对象此前不存在，post记录fresh=true，post/load的对象、ELF和源码集合与快照匹配；Ninja归档显示pre→编译→链接及post顺序，执行索引与用户编译尾段相容。这是B对归档的核对，不是B亲历编译。完整Vitis原控制台缺失，整理后的尾段不能称完整日志。新构建行为由用户报告与归档产物/检查/命令索引共同支持。

原生Tcl四项模拟在B路径复跑成功；A报告的初始化/隔离路径问题作为环境记录保留，不当作固件代码测试失败。归档的真实产物dry-run确有默认dry输出和硬件命令禁用，但B缺少完整AMD工具/BSP环境，未重跑这条真实现场检查链。没要求重建替代BSP、重跑采录或上板。

`git diff --check` 返回2，3415条原件空白诊断，输出无损保存在 `diff-check.txt.gz`，命令及哈希见 `diff-check-summary.json`。此项不通过；为保持原件未格式化，也不把它替代为本次实质阻断。

未执行/未批准：完整AMD编译/链接/BSP重建、实机工具链迁移、新硬件下载/运行、B上板、真实缓存/故障恢复、长稳、M1/H3、音频、定位或新阶段门槛。作者F盘实际工程/平台/共享目录未被B修改或同步签字。

## 交回与状态

请A修复 TF-B-01～03，新增上述有意义的拒绝/固定产物回归后，发布新的准确SHA交B；保留本次88文件原件与全部失败历史。普通增量复用旧对象时如实标记fresh=false本身不是阻断，不要求额外实板操作或新增9月16日门槛。

本轮不修改作者源码，不合并该候选，不推送main，没有本轮合并SHA；作者分支与实际工程引用入口全部保留。共享工作区属于其他在做任务，本次仅建立独立detached复核工作树和包外B证据。报告可直接转交A；本轮未代签A本机同步。
