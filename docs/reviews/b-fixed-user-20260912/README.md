# B 两项任务：用户授权研究归档合入

2026-09-12。用户明确要求“合入未合入的两个任务，并完成A四路工程整理交付的复核”。本记录仅执行前半部分；A四路工程由根任务在另一独立工作树复核，随后另批发布，不在本批重复或删除其工作区。

## 授权与证据身份

指定输入：`task/member-b-fft-bitexact-01` / `bff45e7bbedab321fc4815e1432f1575c750edc4`，及`task/member-b-fixed-closeout-01` / `fdc2d18f2d765cad3223720a85680fd102185039`。本次为用户明确授权归档，不冒充新获A独立技术批准。最新AGENTS/team-workflow/phase-closeout已读取，初始main为`02a41b4507b4544e2fdf1d20a28996997110c337`。

A曾仅批准6cb76d1的17文件研究归档，原审批限制及交替压力帧主语澄清继续以`docs/reviews/fixed-closeout-6cb76d1/review.md`为准；该整个审核目录本轮逐字节保留。A已在main的FFT29包及B对其60帧前向核的限定复核，也不能反向批准B全包。

## 合入关系与文件范围

| 合并 | 结果 |
|---|---|
| aaf92ab | bff45e7作为真实第二父提交，纳入338个B文件；排除历史自动带入的22个A25包文件，不扩大本批目录范围 |
| fc5cffb | fdc2d18作为真实第二父提交，追加后续材料；PR11的重复add/add仅在5个文档/manifest处按指定fdc版本解决；既有原分析数据、A澄清均保留 |
| 合并后原件 | 三个B任务目录中416个文件与fdc2d18的Git blob完全一致；两个原提交均为最终main祖先，但不表示其全部历史目录树被无条件照搬 |

研究交付入口：

- `task-packages/PKG-B-ALG/tasks/fft-bitexact-01/`
- `task-packages/PKG-B-ALG/tasks/fft-window-02/`
- `task-packages/PKG-B-ALG/tasks/phat-fixed-03/`，收口入口为其中`closeout-01/README.md`，A29限定复核为`closeout-01/a29-review-01/README.md`。

本批不新增活动RTL/默认算法，不搬到rtl/tb/sim/model，不签发9/16、H2/H3或整机验收。原因：只有研究归档授权，上游软件候选及fdc新增说明尚无新增A独立技术批准；公共适配RTL、剩余136帧、IFFT29/双核调度、完整整数几何/跟踪/音频仍待相应流程。完整包/H3仍按9/22及成熟度评审。

## 找回并补交的原始日志

本机原bff工作树有两项被全局忽略规则遗漏的有用原件，本轮在原路径补交；与**既有manifest**预记SHA相符，不生成替代日志，不修改旧哈希清单：

| 相对phat-fixed-03路径 | SHA256 |
|---|---|
| dynamic-range/run01-console.log |13824b8a0e456da83ffc38d2f82ee8e9e96ef656313547e33d539ad780112b2f |
| integration/evidence/run02-console.log |e56632ce6dbd2680fae2f8a233b5cc0eb7b8b426d4b6d1ffa0d8cfcd1262332a |

旧A记录的“Git缺run01-console.log”在其固定历史版本上仍然正确；当前main的这项缺件由本补交关闭。文件原名为dynamic-range/run01-console.log，旧README提到evidence下的位置不是本件真实路径。

## 合并后实际验证

Python3.12.14/NumPy2.3.5，全部`-B`。从合并工作树运行：

```powershell
& 'C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B docs/reviews/b-fixed-user-20260912/check_batch.py --out F:/NUEC/b-fixed-postmerge-new
```

输出路径须不存在。实际本轮用`F:/NUEC/b-fixed-postmerge-20260912-run01`；命令、退出码及关键结果归档在本目录run01，各原始stdout/stderr保留。结果：

1. 416个原Git文件一致，动态范围/integration/window封存清单（包括找回日志）全部匹配，A原审核目录未改。
2. closeout完整性检查：77个清单文件（含manifest共78文件），源码/输出哈希通过。
3. 窗FFT归档重新核对哈希与22528个复数码：通过；这是旧XSim输出审计，不是新RTL运行。
4. PHAT F24、seed-offset10000的Decimal/Fraction等软件算术回归：通过，不当新硬件或声学验收。
5. analyze重算196 NPZ / 11760麦对配置 / 96幅值组：通过；8个数值/离散统计输出字节与原件一致。新verification带合并后的源路径，不要求容器SHA一致；对应元数据已归档。重复数组统计可由原件恢复，不重复提交一份。

本轮不重跑全部历史研究、不新跑21分钟A29 XSim或新综合/板测；fdc已有新复跑证据按原字节保存。原始工具日志的尾空格保持，源码/新增说明作限定diff检查。

## 固定A25依赖与复跑边界

`fft-bitexact-01/compare_cmodel.py`的历史入口要求`task-packages/PKG-A-ACQ/tasks/fft-ip-budget-01`，来自固定`ac0ff38e954dac094fd84e28b329dcb24dded7fb`。此A25包22文件未因本次B授权加入main；不能声称该历史全复跑命令已在main自包含。

本批的PHAT/窗归档/analyze入口已在main布局实际通过。需要重跑原25位DLL/XSim历史链时，用保留的bff固定工作树（该历史提交含A25依赖）及包内命令，或新建该固定提交的独立worktree；不向活动main临时复制未批准A25包。合法AMD2025.2安装路径按本机调整。此依赖不阻塞限定研究归档，正式活动入口由后续批准范围处理。

## 批次本地与远端核对

发布及后续核对结果在本节补记。实际main工作树为`F:/NUEC/review-worktrees/member-b-to-a-pkg-b-alg`，发布前干净、无未跟踪/忽略文件；本地main起于e3f4905，将在正常发布后仅快进同步。

本机长期开发目录`F:/NUEC/develop`仍在feature/member-b-algorithm，79条状态项、146个未跟踪文件、5个忽略文件，均已列表保留于run01/worktree-inventory.json；三个本批B任务路径无本批未跟踪/忽略材料。不切换该脏目录、不代替其他任务提交，不声称其工作树与main一致。同一Git库的local main/origin/main引用另作实际核对。

两个原任务分支已关联其他任务工作树，且原定点后续工作尚有未完成范围，本次保留分支及工作树，不在未确认无继续任务时删除。它们的成果已入Git历史；两份找回日志也会进入main，不能再仅留忽略区。已结束的本任务A29复核副本/构建缓存，在确认新main有全部原始证据和固定版本可复跑后安全去重；根任务A工程工作树及其他工作树不处理。
