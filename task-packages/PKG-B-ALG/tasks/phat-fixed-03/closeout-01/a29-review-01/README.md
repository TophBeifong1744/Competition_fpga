# B 对 A FFT29 限定候选的独立复核

2026-09-11；作为既有定点误差/预算/完整包收口任务的追加输入。A交付固定为`c0b5f8fb44643e81d8c4e6f0be457dddeae9758e`，分支`codex/toph/fft29-bitexact-budget-01`；B新增材料沿`task/member-b-fixed-closeout-01`交审，不自行合并。

来源：`task-packages/PKG-A-ACQ/tasks/fft29-bitexact-budget-01`。独立源工作树为`F:/NUEC/review-worktrees/b-review-fft29-c0b5f8f`，detached于准确A提交，未修改A原件。B输入固定`bff45e7bbedab321fc4815e1432f1575c750edc4`。已读取最新main `4957d18837f79eca7a6acc86a2757d10f41dd410` 的AGENTS.md、phase-closeout及阶段B安排，未合并主线变动。

**最终结论：B独立复跑完成，限定所选60帧前向FFT29及候选OOC核预算的技术复核通过，可作为后续研究输入；不批准默认替换或完整链。** 新运行361次/739328实虚码零差、overflow=0，check.json与A对应数值记录一致。新输出/状态/周期CSV分别完成整数数值及原始字节比较，三者均一致；新工具日志及工程报告不要求字节一致。结果见[evidence/replay02/B-replay-summary.json](evidence/replay02/B-replay-summary.json)。

## 证据层次

| 层次 | 本轮内容 | 证据 |
|---|---|---|
| A作者自测 |60/196帧、360 FFT+1背压重复；737280个唯一原件实虚码，加重复后739328码；OOC综合/核布局布线|A固定提交原evidence/run01；不当作B新运行 |
| B核验归档 |155文件/31034727字节SHA一致；9项比较器测试；资源/XCI转录；旧输出739328码零差；原始统计重聚合|evidence/archive01，各命令/环境/退出码独立保存 |
| B独立输入与来源检查 |74个复制B文件逐字节匹配原Git blob；4个A25参考文件匹配ac0ff38；11项仿真原始记录压缩前后哈希；重新生成输入/expected/selection/job-count字节相同；独立逐job/bin码及周期核对|independent_audit.py；evidence/archive01/independent-audit.json |
| B本机新复跑 |从归档整数窗生成输入，新建29位IP、OOC综合/布局布线、同60帧及背压重复XSim；状态由实际输出确认|evidence/replay02，B-replay-summary.json与check.json为最终运行依据 |

新综合、布局布线、XSim、逐码检查和无损归档命令均退出0。新核配置全部component参数与A XCI一致。正常配置到最后输出7361周期、服务槽7366、六FFT首尾44191/六槽44196、背压重复7599周期，全部与A一致。只对实际被测输入/调度成立，不扩展到未覆盖帧或任意停顿。

本机Windows11 build26200、Python3.12.14、NumPy2.3.5，Vivado2025.2 SW6299465 / IP6300035，器件xc7z020clg400-2，FFT9.1 rev15。供应商程序使用本机`D:/AMD/2025.2`，没有使用A电脑路径。未运行声学生成器/全784配置、未复跑其余136帧，未新增RTL功能。

## 审阅结果与范围

源码检查覆盖configuration、prepare、TB、build/simulate、check、test_checker、audit_reference、check_resources、打包工具及复用说明。直接用`windowed*16`进入S29，C API解释code/2^28与应用F27区分；配置0x0AAAAB、自然顺序、29位数据/24位旋转因子、逐级移1、最近偶数一致。golden为B归档wide29_raw_fft，没有先缩S25隐藏差异。TB检查bin、TLAST、状态、未知数据和背压保持，最后一个case000/ch0重复采用输入间隙/输出停收；有限背压实例不是任意阻塞上界。

公共最小右移r按六通道完整谱选取，正负舍入边界测试存在；软件适配相符不能批准适配RTL。所选帧是两个种子×两个方向×clean/noise0×指数{1,16,17,18,20,21,24}加4压力帧；其余136帧未覆盖。没有将八组基础波形当独立声学验证集。

本机核布局布线1045 LUT、2046 FF、8DSP、6RAMB18/3Tile；WNS+5.248ns、WHS+0.037ns、TNS/THS=0。原始route-status为2701条可路由网络全部布线，内部未约束端点0。85输入/88输出无系统delay，HD.CLK_SRC未指定，独立核缺PS7，DRC仍有ZPS7-1警告和6项AVAL-4建议；不因此标整机时序通过。

复核未发现阻断**所选FFT29前向核研究材料**的问题。可提交批准的范围仅A这个固定任务包的所选向量一致性与候选核实现预算；不得默认替换原配置、冻结误差限、批准单核混合位宽、整链、音频、实板或H2/H3。B新增审计源码、证据与预算改动仍由指定复核流程审查，尚未合入。

## 发现、保留限制和待补

1. A已披露B旧manifest列出但Git缺失的`dynamic-range/evidence/run01-console.log`、旧README HEAD/未推送措辞。这是旧交付记录缺口，不改变已核验输入/源码/golden；本轮不伪造补日志、不改原件。准确来源以提交和哈希为准。
2. 本机第一次受限构建在create_project遇`Common 17-539` Tcl appinit加载失败，退出1；新目录经授权正常重跑。evidence/failed-build01保留失败命令及日志，没有reset TclStore、修改全局PATH或安装。不能把失败目录标通过。
3. 29位公共右移/缓冲/指数传播RTL、剩余136帧、强制overflow与恢复、IFFT29及双核调度仍未验证。A包清单没有要求本轮从零实现这些模块，保持待补。
4. 2^-20的原wide29结果仍为120有效对、26整数峰变化、最大时延差0.879647852采样。FFT新逐码一致没有消除整链误差，参考线仍只是研究描述，非真实TDOA精度。
5. 原25位1.55526ms为21次变换及其口径；新29位六FFT服务槽0.44196ms只覆盖前向。两者不能混算成整链实测。预算页给出的双核14DSP/6Tile只是核资源算术估算，集成需实际验证。

## 准确复跑命令

先获取固定A提交并建立不冲突的独立工作树。以下从B工作树根目录执行；`$out`必须为新的短英文路径。工具会拒绝覆盖已有同阶段命令记录；构建失败保留目录，换新目录重跑。所有Python调用都使用`-B`。

```powershell
$py='C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$review='task-packages/PKG-B-ALG/tasks/phat-fixed-03/closeout-01/a29-review-01'
$aRoot='F:/NUEC/review-worktrees/b-review-fft29-c0b5f8f'
$out='F:/NUEC/b29-review-new'
& $py -B "$review/replay.py" --a-root $aRoot --out $out --mode archive
& $py -B "$review/replay.py" --a-root $aRoot --out $out --mode prepare
& $py -B "$review/independent_audit.py" --a-root $aRoot --vectors "$out/vectors" --out "$out/independent-audit.json"
& $py -B "$review/replay.py" --a-root $aRoot --out $out --mode build --vivado D:/AMD/2025.2/Vivado/bin/vivado.bat
& $py -B "$review/replay.py" --a-root $aRoot --out $out --mode simulate --vivado D:/AMD/2025.2/Vivado/bin/vivado.bat
& $py -B "$review/replay.py" --a-root $aRoot --out $out --mode check
& $py -B "$review/collect_review.py" --a-root $aRoot --run $out --out F:/NUEC/b29-review-collected-new
```

实际归档检查输出在本目录evidence/archive01；prepare/build/simulate/check成功轮在`F:/NUEC/b29-review-run02`，整理到evidence/replay02。`*-commands.json`记录原命令参数数组、工作目录、UTC时间、耗时、Python/系统版本、退出码与console位置；本轮未调用A的run.ps1总入口，而是按原逐步命令使用-B执行。

原输入字节SHA、RTL有符号整数码、job/bin/status/周期数值、CSV原字节、工具报告分别比较。新工具日志路径/时刻和工程容器无需字节相同；不得据日志退出0代替逐码结果。collected中不复制供应商生成HDL、DCP或仿真库，配置XCI、报告与原始仿真记录足够复核；完整工程留在本机短路径。

最终完整性检查覆盖当前总manifest及42个新复跑归档文件哈希。全量`git diff --check`会指出原始Vivado日志/报告的行末空格及空行；为保留证据bytes未清洗这些文件，源码/说明的限定差异检查通过。这是原始工具文本格式，不是数值验证失败。

## 收口与后续

原closeout-01/evidence/run01、analyze.py和A-C原件不变；首版manifest在previous-release-manifest.json只读保存，当前总manifest更新以包含本轮新增材料。预算新增A候选核来源，B新复跑只提升同范围证据层次，未关闭其他缺口。

本轮属于候选研究包技术复核，不是阶段整机验收；没有新增获准默认算法/活动RTL可归位，不更新公共阶段状态或已验收快照。准确范围交审后，由复核/主流程决定研究包归档及适用收尾，不自行合并B新材料。
