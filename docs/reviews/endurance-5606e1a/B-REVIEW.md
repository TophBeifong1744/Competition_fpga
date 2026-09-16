# B 独立复核：E1 耐久测试限定归档

审核 SHA：**5606e1a9d9a6183ceff7cffc1bb4f8aac44bb79c**。仓库 TophBeifong1744/Competition_fpga；分支 codex/toph/endurance-20260916；准确父提交 ad9ca72388fb676946c71b13517ab279c11cfc61。2026-09-16，成员 B。

结论：**通过，仅限 E1 实现与这一次实板记录的归档**。未发现阻断固定交付归档的问题。它不是安全构建/加载入口批准、正式 M1/H3、一小时长稳、故障恢复、音频/定位或整机验收。

唯一批准内容是 `task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/endurance-test-01/` 的准确172文件，保留原件、失败历史及早期时点说明；不向活动 ps/rtl 或实际 one 安装，不合入 timerfixed-entry 待审分支。

## 固定版本及原件完整性

先直接 ls-remote 核对 E1 分支与 main，再 fetch，独立工作树 `F:/NUEC/review-worktrees/endurance-5606e1a` 固定审核 SHA。按顺序读 publication/README.md、board-run-20260916-01/README.md、该目录 HANDOFF.md。B输出全部在包外 `F:/NUEC/review-evidence/endurance-5606e1a`。

独立 Git/原字节检查确认：相对父提交只有172项新增，范围外0；172文件逐项与 Git blob 完全一致。原138项清单加自身构成139原件；发布171项清单加自身构成172文件。46项真实构建清单、23项快照绑定均匹配，集合有重叠，不累加总数。proposed-src四文件与归档实际应用对应源码原字节相同。两个真实计时布局拒绝、旧源码pre拒绝、早期源码/日志及后续成功构建均保留。

全量 `git diff --check ad9ca723 5606e1a` 实际退出2，10438处行尾空白提示；原输出以 provenance01/diff-check.txt.gz 保存。原字节不格式化，不声称该检查通过。

## 实际命令及结果

环境：Windows，Python 3.12.14，主机 MinGW GCC 8.1。Python路径 `C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`；GCC路径 `F:/STUDY/IT/C/develop/mingw64/bin/gcc.exe`。没有使用AMD工具或接触板卡。

在独立仓库根，令 `$e1` 为上述包路径，执行：

```powershell
python -B "$e1/publication/package_manifest.py"
python -B "$e1/board-run-20260916-01/record_checks.py" verify
python -B "$e1/board-run-20260916-01/test_verify_log.py"
python -B "$e1/publication/reproduce.py" --repo . --out <包外新目录> --gcc <本机GCC>
```

实际绝对argv、cwd、返回码与原输出由 `run_required.py` 记录，见 required-run01。

- 发布171项、原138项清单通过；日志4、合同/源码7、计时布局12，共 **23个 Python 测试方法通过**。入口另执行的4个日志测试不重复计入总数。
- 提取固定 **bbe39c38dc36ccb4c0492f492b86f6c46d885fbe** 的历史依赖到新输出目录，并核对 POLICY 两项、helper两项及硬件三项。没有把旧入口安装到本次工作树或实际工程。
- UART检查和真实归档对象/ELF检查通过；首次复现器最终退出1，原因仅为旧版MinGW对测试打印 `%llu` 在 `-Werror` 下报错，原失败保留。不能把这次复现器整条命令写成退出0。
- `run_host_compatible.py` 从已记录编译命令增加 **-D__USE_MINGW_ANSI_STDIO=1**，保留 `-Wall -Wextra -Werror`，使用全新输出目录。未改C源码/测试。主机编译与执行退出0：原16场景、11段调度、配置错误/失败重用/空配置/组数不足期限检查全部通过。此为主机模型，不是ARM新构建或板上故障注入。
- `audit_provenance.py` 独立核对Git字节、四份候选/实际源、原始UART逐段首尾编号/计数/时长/44通道统计与ELF构建时间。其余独立脚本及结果见 spec、standards。

## 源码、对象与实板记录的对应

E1实现是在C1基础上增加一段300000000微秒/14400000组与十段10000000微秒/480000组调度、固定合法配置、段间间隔及终态检查。源码main实际使用endurance_schedule；对象与ELF中的十字段E1合同、22个调度字段匹配；原16字段连续采集合同的最后两字段仍是短段默认值，不能误报成长段配置。

归档ELF SHA256：`75c7e5e2203ed1ba019c83a1123ef79eff0c877286d722eea5b8d9a275c76449`；对象：`4eeb96edabcb79b2b6df29bbdbe2c67ee3532b14a71bfbe08117f4df63a3dc15`。实际计时除数333333343，E1常量池偏移108、立即数12，与旧池偏移112/立即数16只在受限对齐规则下比较；对象R_ARM_CALL、链接后调用目标和ARM/Thumb模式均检查。

程序end=0x00113890，归档map及程序/堆/栈加载区间在RX之前。RX=[0x01000000,0x01100000)，两槽各8000+64字节，stride8064、总16128字节，不因长段扩容。源码保留DMA与CPU所有权、缓存准备/获取、逐包guard、signed24、编号和flags检查，验证完成才回收。

UART构建时间 Sep 16 2026 20:52:11 与归档ELF字符串一致，真实构建记录、源码快照及launch配置相互支持。88项外部BSP的实际匹配是A归档中的核对结果；B没有A现场BSP，不称独立重哈希全部88个现场文件。硬件历史文件通过固定Git依赖哈希核对。这是磁盘产物/串口/操作者声明的对应，**没有独立板上bit/ELF读回，也不是加载身份认证**。完整Vitis控制台仍仅有尾段边界。

## 串口独立重算与证据边界

原UART SHA256：`6920a852e43f2f6e4f47c2f1a4aefb8c3058ff5d108fc8ec5b4ea80e9cd41fd5`。

11段分别为300.000125秒和十段10.000123～10.000134秒。长段14400250组/57601包，短段各480250组/1921包；合计 **19202750组、76811包、614488000字节在线处理**。每段满足首尾ID跨度=组数=包数×250，字节=包数×8000。停止排空5207～5210微秒，最终SOURCE=C100000A、DMA_SR=00001002、length8000、active=-1、owners=0,0；保留最后16包槽轮转。44个通道统计均非恒定、signed24范围内，clip_flags=0。

段间有意停止造成的未采ID合计551090，保留间隔，不拼成连续400秒。没有完整长BIN/CSV/WAV，B不能逐组重算全部19202750组；上述段内逐组检查是固件在线结果，B重新核算的是串口记录的内部一致性。clip_flags=0及通道非恒定不代表声学效果、独立映射或精确同步通过。计时没有新的独立时钟精度测量。

源码正常段间不调用复位，失败后才复位DMA；一次Run且无人工段间复位/断电的说法来自操作者确认。初始加载仍执行初始化/复位；没有外部电源/复位测量，不把声明扩张为独立硬件证明。

## 非阻断观察

1. `verify_log.py:55,65-66` 未约束部分字段关联：成功游标可被改成0，最后检查值可改为越界，正数min/max仍可填非零zeros而通过解析。**固定原日志没有这些矛盾**，B已独立补核游标249/3、最后mic3值的signed24/区间及zeros一致性。可接收该固定哈希归档，但复用解析器处理新输入时应补检查，不能称为通用完整日志判定器。文本变异不是实板故障注入。
2. 根README准确合同为“达到run_us+2秒仍未达到组数时失败”。独立C模型在组数已足够后推进时钟，可得到12.000140秒的OK短段；这说明它不保证任意CPU停顿后的硬性总期限，**不违反该较窄组数不足合同**。本次11段实测记录均在正常时长。保留该观察，不据此追加实板任务或新的验收门槛。

## 允许范围与明确未执行项

E1依赖bbe39c38旧检查器，不继承17afe32的启动检查或封存加载保护；旧命令比较缺陷及TF-B-02-R1不因本批归档关闭。`--stage load`仍只是预检查，作者实际GUI Run不受封存保护。本批不批准这些入口用于安全构建/下载，不部署至活动目录，不借归档批准追认历史入口放行。

B没有新ARM编译/链接、完整现场pre/post/load、XSDB下载、RTL仿真/综合实现、板测、实板故障注入或一小时长稳。允许用于E1实现追溯、在线采集/启停诊断和相应实板记录的限定归档；不代表M1/H3、定位、波束、音频收益、整机或新增阶段门通过。

## 合入与收尾

明确限定通过后，从最新main隔离集成仅批准172文件及包外B复核记录，运行相称回归后非强制推送。具体合并SHA、合并后结果、本地/跟踪/直接远端状态、其他工作保留及清理去向见本目录 BATCH-CLOSEOUT.md。A本机共享目录、实际工程与仍引用的入口不由B删除或代签。
