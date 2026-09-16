# B 独立复核：TF-B-01～03 修复

结论：**需修改，不合入 main**。TF-B-01 的 ELF 启动检查和 TF-B-03 的封存加载保护在本轮限定范围内通过；TF-B-02 原大小写反例已修，但新增命令比较器仍会吞掉实际链接参数，保留一项 P2 阻断。

审核时间：2026-09-16，成员 B。仓库 TophBeifong1744/Competition_fpga，分支 codex/toph/timerfixed-entry-20260916，准确 SHA **17afe32cebcff742bb2f9486388e91d9403f83dd**。原版本 bbe39c38dc36ccb4c0492f492b86f6c46d885fbe；原 B 反馈 53018f9256cd209136183679d28b8949b04536f2。

唯一源码审核范围：`task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/timerfixed-entry-01/`。直接远端确认、fetch 后在 `F:/NUEC/review-worktrees/timerfixed-repair-17afe32` 固定新 SHA；先读 repair-01/README.md。作者工作树及冻结证据保持原字节。B 新证据放包外 `F:/NUEC/review-evidence/timerfixed-repair-17afe32`。

## 唯一阻断：TF-B-02-R1 / P2

位置：`command_contract.py:52-53`；调用者 `check_entry.py:179-180`。

比较器把绝对 `-Wl,` 后缀整体交给 `ntpath.normpath`。GCC 实际按逗号拆为多个链接器参数，所以它不是单个文件路径。把归档中的：

```text
-Wl,"F:/College/verilog_digital_system/Vitis/four_mic_continuous/src/lscript.ld"
```

改成：

```text
-Wl,"F:/College/verilog_digital_system/Vitis/four_mic_continuous/src/lscript.ld,-L,/../lscript.ld"
```

两者被归一为相同的 `-Wl,$app/src/lscript.ld`，完整 `verify_link_output` 函数返回 ACCEPTED，实际却多出 `-L /../lscript.ld`。在同一 token 再插入 `-e,0x01000000`、`--defsym,REVIEW_MARKER=1` 或 `--wrap=XAxiDma_SimpleTransfer`，三种变化也均被比较器错误接受。这违反本次要求“路径规范化仍保留选项及分词语义”和“未知配置拒绝”。

影响是实际链接配置的等价检查失效。无效 entry 仍会被独立 ELF 检查挡住；本复核**没有证明错误入口通过全部 gate**，也没有以变异配置执行 ARM 编译/链接。`--wrap` 等额外链接行为不能仅靠现有计时/缓冲合同代替完整命令比较。证据见 `spec/run01/result.json`、`spec/extra01/result.json`；真实主机 MinGW GCC 8.1 的 `-###` 输出仅用来确认逗号分词，不是作者 ARM GCC 13.3 或实板证据。

请 A 先解析 `-Wl,` 子参数，仅对明确的路径操作数规范化，未知复合布局拒绝；保留参数顺序、选项、宏值及引号/分词语义，补充上述负例后交回。B 没有修改作者实现。

## 原三项反馈状态

| 项目 | 本轮结论 | 独立覆盖 |
| --- | --- | --- |
| TF-B-01 | 原 ELF 启动缺陷关闭；链接参数比较仍受 TF-B-02-R1 阻断 | 原两种错误入口拒绝；7种入口、非执行/缺文件数据段、向量符号偏移等测试通过；源码绑定固定 ENTRY(_vector_table)、ARM 对齐、可执行且有文件数据的 PT_LOAD、节/段偏移及归档启动字节 |
| TF-B-02 | 需修改 | 原 -DSDT/-Dsdt、-U__clang__/-u__clang__ 已正确区分；宏值、字符串分词、普通额外参数检查通过；复合 -Wl 负例误接受 |
| TF-B-03 | 限定通过 | 检查和封存期间活动输入持锁；封存后锁内核对哈希；Tcl 读取同一封存文件，锁覆盖 fpga/source/dow/con；正常与异常退出释放 |

## 实际执行与结果

Windows Python 3.12.14：`C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`。原生 Tcl：`F:/STUDY/IT/Anaconda3/Library/bin/tclsh.exe`，通过 TF_TCL 指定。均用 `-B`，不使用 `--create` 或 `--record`。

在受检包目录，由包外 `run_required.py` 顺序执行：

```text
python -B repair-01/verify_repair.py
python -B repair-01/reproduce_b_negatives.py <包外新目录>/b-negatives
python -B repair-01/run_checks.py <包外新目录>/checks
```

- `required-run01`：清单及4个原 B 负例通过。原18、父10、安全34通过；repair组因沙箱祖先目录锁 WinError 5 失败，Tcl组在读取临时目录初始ELF时失败。失败原输出和14个Tcl输入/输出均保留，不把无关失败当拒绝验证成功。
- `required-run02`：同字节脚本、同依赖在沙箱外普通用户环境复跑，新输出目录；三条命令均退出0。18+14+6+10+34＝**82项 Python 测试通过**，加载组含 **14次实际 Tcl 模拟**。未降低锁强度、未修改冻结测试。
- 包外 `audit_bytes.py`：Git diff 为**3修改、122新增**，范围外0；当前**210文件全部原字节匹配审核提交**；新清单209项加自身，旧清单87项及自身未改；三个修改文件和旧 test_load.tcl 的 originals 匹配旧提交；两个 B 脚本匹配53018反馈原件。历史失败文件均在新清单及准确提交内。
- `spec/check_arguments.py --package <受检包> --output <新目录> --gcc <本机GCC>`：六组大小写/宏值/字符串负例正确区分，四种普通附加参数拒绝，复合 -Wl 误接受。`spec/extra_link_flags.py` 的3个加强负例仍误接受。实际参数和输出存对应 JSON。
- `spec/quotes_probe.py`：10种引号/反斜杠示例与主机 GCC 的只打印结果一致。首次缺输入夹具的 quotes01 保留、不计通过；补夹具后 quotes02 通过。
- `standards/independent_guard_checks.py`、`independent_keeper_checks.py`：七组独立补测通过，含可写mmap冲突、硬链接写拒绝、部分锁获取失败回收、RELEASE/EOF/未知命令退出、con步骤故障。检查期间7种活动输入写入及app祖先更名拒绝；封存三文件写/替换/删和三级祖先更名拒绝；活动app随后更名不影响封存字节，退出后锁均释放。原生Tcl、keeper、NTFS锁和归档ELF真实参与，其余完整gate前提与硬件mock。

完整命令、cwd、退出码和输出见 JSON；各脚本一次性输出应指向不存在的包外目录。独立 standards 脚本中的 ENTRY/TCL 是本机审查路径，异机须在包外副本适配；不要覆盖本轮证据。

## 归档及未验证边界

归档对象/ELF通过计时除数333333343、16项合同、启动入口0x00100000、程序end=0x00112640及RX范围检查。新ELF仍为 `726a91fe19fd9b9e67cca6f3c8668bf484df92d1bbb2ec2e5f2619cc0237324c`；本修复未改它。原始加载缺陷对照、run01～05失败/修正历史、live-link01查询结果均为保留的A归档，不能改称B新编译。live-link仅枚举Ninja命令、审查现有ELF。完整Vitis控制台缺失仍保留为边界。

B未运行现场完整pre/post/load gate、ARM新编译/链接、真实XSDB下载、板卡、RTL仿真、综合/实现或长稳。文件锁仅限支持的本地Windows NTFS环境；真实XSDB共享模式兼容性未验证。GUI直接Run仍可绕过。A共享目录和实际工程仍引用旧入口，本轮没有部署或代签同步。

本结论只涉及构建/加载入口修复及离线证据，**不批准本候选合入，不代表M1/H3、长稳、音频、定位、整机或新阶段门通过**。旧publication/清单不改写，原件不格式化。没有运行修复实现diff --check来宣称原日志/快照空白提示已消除。

## 规范轴与需求轴

规范/加载保护轴无新增阻断，报告见 `standards/STANDARDS-REVIEW.md`；需求/参数语义轴1项P2阻断，报告见 `spec/REVIEW.md`。前者限定通过不能抵消后者阻断。

## 发布及本机材料处置

只将B复核记录、可复现脚本和结果追加到独立反馈分支 `review/member-b-timerfixed-bbe39c3` 的 `docs/reviews/timerfixed-repair-17afe32/`，不改旧53018反馈，不推作者分支，不合入main。精确反馈提交以本次回报及直接远端查询为准。

冻结审查树、A分支、实际工程引用入口及本批包外证据保留，用于下一轮修复。重复fixture的完整本机路径及哈希登记在 `LOCAL-MATERIALS.json`；发布副本只保存可复现脚本/结果，原对象与bit从准确A提交恢复。未删除任何A工程、原件或共享工作。

共享目录为 `F:/NUEC/develop`，仍在其他活动任务 `task/member-b-four-track-01`（f364a023830b105e6075d853da83cfd51127cf64）。本地main 9936613e99a5ac4c2d080375697d8447f5f377fc 比既有origin/main 8371f014711e04553749e6c2ffc29f34b9d5ccc9领先1个此前收尾文档提交；本次未代推、未重置。实际状态/未跟踪/忽略项与远端查证见 `state-before-feedback.json` 及后续发布回执。因本候选阻断，main合并批次收尾不适用；不能声称main已同步或A本机已同步。
