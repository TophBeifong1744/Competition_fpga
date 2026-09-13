# B 独立复核：FFT29 剩余归档覆盖

2026-09-13，结论：**通过**。批准仅限剩余136帧的前向FFT29归档覆盖及其复现入口。

- 仓库：TophBeifong1744/Competition_fpga。
- 分支：codex/toph/fft29-coverage-extension-01。
- 准确审核SHA：b8c5e87f6cb1054c2684719310f02f36c83ac731。
- 父SHA：bb82de16a33751fb684243a19132dbb6b5736d91。
- B数据固定SHA：bff45e7bbedab321fc4815e1432f1575c750edc4。
- fetch及直接ls-remote确认作者分支准确SHA后，在F:/NUEC/review-worktrees/fft29-extension-b8c5e87固定detached副本复核。
- 批准原件入口：task-packages/PKG-A-ACQ/tasks/fft29-bitexact-budget-01/coverage-extension-01，全部86文件保持原字节。B记录单独放在本目录，不加入作者清单。

## 实际执行

先读RESULTS.md、REPRODUCE.md，再读源码、原始编译/仿真日志、IP、哈希和映射。Python为Codex捆绑3.12.14，NumPy 2.3.5；默认系统Python未使用。Git使用Codex捆绑版本，并仅给工作树设置进程级safe.directory。

在extension目录执行（PY为实际Python绝对路径）：

```text
PY -B source/test_extension.py --log F:/NUEC/review-evidence/fft29-extension-b8c5e87/tests.txt
PY -B source/verify_archive.py
PY -B F:/NUEC/review-evidence/fft29-extension-b8c5e87/independent_audit.py F:/NUEC/review-worktrees/fft29-extension-b8c5e87
```

PY实际为C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe。独立脚本保存在本目录，接受仓库根目录参数；所用Git绝对路径在脚本内。

13/13测试通过；归档入口返回PASS_READ_ONLY_ARCHIVE_RECHECK_NOT_NEW_XSIM。其输出中的PENDING_B是作者脚本固定字段，本报告才是独立批准。独立脚本再次直接解析CSV/NPY、逐项对照Git blob及编译绑定。

## 核对结果

1. 父提交到审核SHA仅新增extension的86个文件，85项SHA256SUMS加清单自身集合完整，86份工作树字节等于准确Git blob；历史155项与准备阶段14项映射哈希全部通过，旧清单和失败记录未改。
2. 136帧×6通道=816唯一FFT，job816是case001/ch0背压重复，总817次；836608复数点、1673216实虚整数码逐项相同，overflow全部0。job/bin/通道顺序、输入mem、NPZ windowed左移4位及wide29_raw_fft均核对。没有重新生成golden。
3. 新136和旧60集合交集为空，并集恰为0..195。历史361次仅引用历史证据，本轮没有重跑它们。
4. 实际XCI与历史XCI完整SHA相同；xfft9.1 revision15，Vivado2025.2，xc7z020clg400-2，1024点Radix-2 Burst，S29、24位旋转因子、convergent、自然序、nonrealtime、0x0AAAAB配置不变。实际TB/wrapper SHA与配置报告、编译prj/log对应；wrapper只省略三组六条元数据，余下代码相同。
5. prepared哈希绑定归档mem/expected/job-count/selection；finalizer源码检查实际XSim目录mem等于准备输入。B不能访问A原E盘，因此实际运行目录字节身份依据归档日志、哈希和收集流程，未声称现场读取原目录。原simulate.log有一次817-job PASS和60182750ns结束记录；GUI journal缺失已明示，操作单不是原始journal。

## Standards

通过，0项硬性违规、0项需提出的维护性建议。固定Git对象及哈希、独占写入、新输出目录、失败保留、原字节保护和研究身份符合AGENTS.md及三人工作流。

## Spec

通过，0项阻断、0项越界。独立审查另直接用NumPy检查输出/预期数组及136+60集合、编译源哈希与日志。比较器和TB对整数码、顺序、TLAST、未知输出及限定背压实例有对应检查。

## 问题与未执行项

未发现作者阻断问题。B补充脚本首次误以16进制解析job-count，发生AssertionError；对照TB的fscanf("%d")后改为十进制，重新完整通过。这是B脚本错误，没有修改作者原件或结果；原失败说明另存。

本次仅复查已归档仿真，没有新运行XSim、综合、布局布线或上板。A原运行E:/fft29-coverage-01及GUI现场未访问；没有认证任意背压、强制overflow恢复、定位、完整定点链、H3或整机。默认算法不改，不新增阶段门槛；新main中的9/14与10/1日历保持不变。

## 集成

合入前最新main为99cf1dc2c1e7e2bd60ca843839d47906f9b84770。实际main工作树F:/NUEC/review-worktrees/member-b-to-a-pkg-b-alg原干净，已安全快进；仅合入批准extension及B本目录记录。归档使用入口保持原extension，因仅获研究覆盖批准，不替换默认算法或实际工程。

## batch-closeout

| 回报项 | 实际结果 |
| --- | --- |
| 合入与回归 | 合入提交023177cf19c7dd8b6914fea79cfd76b05b27b020，已非强制推送。合并位置再次13/13测试、归档检查和独立86份Git blob/清单/数值核对通过，见main-*回执 |
| main对齐 | 发布后从实际共享F:/NUEC/develop及实际main工作树核对local main、origin/main均为023177c，直接远端同SHA，领先/落后0/0；补交本收尾记录后再次核对最终SHA，保存在外部回执并向用户返回 |
| 本批材料 | 发布后main跟踪/暂存修改0、未跟踪0、本批忽略0。共享feature工作树本批路径状态及忽略0；B本批未处理有用材料0，未说明去向0 |
| 其他工作 | F:/NUEC/develop仍在feature/member-b-algorithm，HEAD57b86e0，52项已跟踪差异及146项未跟踪属于其他工作，全部保留；未切换或重置脏共享目录 |
| 唯一归档入口 | 批准材料原extension与B本目录已入main。外部本次原始回执保留F:/NUEC/review-evidence/fft29-extension-b8c5e87，非活动工程；完整无关文件名盘点仅在该目录batch-full.json，SHA256为46b8fd0e20b89122edde5f87eeeb678c927d61c52a10d2f487cc176aab7755a7，公开本目录batch-summary.json给出数量 |
| 清理与恢复 | 只删除本次固定审核worktree F:/NUEC/review-worktrees/fft29-extension-b8c5e87；删除前已检查准确路径，跟踪、未跟踪及全目录忽略均0。可由审核b8c5e87重建；脚本中该路径为历史运行位置 |
| 保留责任 | 作者分支仍为b8c5e87。未取得A侧后续任务/独有本地材料结束确认，保留作者分支、pub及E:/fft29-coverage-01，不代签A机检查。其他成员工作树与分支均保留 |
| 状态 | B侧本批发布、回归和材料收尾完成。A侧材料检查及短期分支清理条件由A确认后处理；这不提升为跨机器仿真或实板批准 |

本次没有覆盖任何作者清单、历史原件或失败记录。B首次补充脚本错误仅记录为B检查失误，不改写作者结果。
