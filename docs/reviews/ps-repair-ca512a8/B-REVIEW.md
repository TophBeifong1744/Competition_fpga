# B 增量复核：PSB-B-01～03

结论：**限定PASS，三项关闭**。准确SHA ca512a8be7978ab6ca2ade3d5e0b922e53a89c79；分支codex/toph/ps-bridge-repair-20260921，原基线fbbaa161098582ba1e5e112b86d39533769bb3e7，B反馈b66da3cd32cf91708cc13bc45608afa3a503bec0。实际日期2026-09-21。首先fetch并ls-remote核对候选精确匹配，main为cf026cf29518488f8c7275b825f3487a8d892f80；独立短路径F:/NUEC/r/psr固定检出。

## 逐项裁决

| 问题 | 裁决依据 |
|---|---|
| PSB-B-01 | 聚合/校验与commit分遍执行；payload、binding、status冲突排列先使事务失效，本批无新commit。其他事务保留聚合状态也须另次dispatch才可提交；不是多事务物理输出原子性。历史已提交结果发生冲突时保守fail-stop。原反例双排列和实际take已核对。关闭。 |
| PSB-B-02 | 先区分session，再安全检查slot和generation；当前未知error（越界slot/未知generation/释放后）fail-stop，旧session隔离。同批合法完成不能越过当前错误，旧回调不误杀新会话。关闭。 |
| PSB-B-03 | acquire先选第一个READY，再比较generation；MAX合法帧可取得。下一次分配耗尽明确COUNTER，不回绕，也不发布不可取得的READY。含两物理槽倒序复用、MAX结果token及publish内部耗尽。关闭。 |

## 实际执行与证据

Python3.12.14/NumPy2.3.5，GCC8.1.0 x86_64。沿上轮已记录的包外gcc-ansi.cmd仅添加-D__USE_MINGW_ANSI_STDIO=1以启用本机旧MinGW标准printf；C11及全部-Wall/-Wextra/-Wpedantic/-Wconversion/-Wshadow/-Werror保留，未改作者源码/测试。

仓库根命令，BASE=task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918：

1. `git restore --source=0abdc91c57787b7c868a797b88f35129de169faf --worktree -- <BASE>/engineering-closeout-20260923`，仅独立检出原先不存在的依赖目录，未暂存。
2. `python -B <BASE>/ps-semantic-bridge-candidate-01/tools/seal.py --verify`：1479项PASS。
3. `python -B <BASE>/ps-semantic-bridge-repair-01/manifest.py --verify`：516项PASS，清单SHA e8ceb18fceead5cd190ad84c99fa71212f6762bc7dda510fb8eeeeca5978b96e。
4. `python -B <BASE>/ps-semantic-bridge-repair-01/verify_repair.py --cc F:/NUEC/review-evidence/ps-repair-ca512a8/gcc-ansi.cmd --out F:/NUEC/r/psr-run01`：退出0。原33/33对照、O0/O2各9组27131断言；最终新增122场景3949断言在O0/O2均通过。数量不跨编译/历史120场景重复相加。完整argv、退出码、stdout/stderr、绑定与源码哈希见run/。
5. 原B脚本对旧版仍记录缺陷；修复版实际take/failed/acquire符合预期。generation_max旧脚本在修复版退出1是期望旧缺陷不再成立，不算测试失败；新增断言独立确认真实状态。
6. B另编译spec/spec.c，GCC O0/O2独立13场景279断言通过，stderr为空。覆盖撤销后晚错含释放、STOP/RESET后旧会话隔离、status0 payload不替换与binding冲突双排列、配置副本。没有调用作者repair.c产生期待值。

## Standards

本次517新增全部限于同级repair目录，516清单加自身。原1481候选与其封闭清单未修改；原B反馈/失败记录保留，原host.c/run_host.py字节及PINS不变。0ab路线与a7 Python结果分别有准确Git绑定，未静默换参考。已有输出在启动工具前拒绝。详见standards/；无新增规范阻断。

## Spec

三项均满足本次限定单执行者C合同；spec/REVIEW.md记录代码行号及独立边界证据。status0仅复查，不替换payload；明确error/控制优先；内部状态不可任意外改、hooks同步只读不可重入的前提不变。新增枚举属未冻结候选，不宣称生产ABI兼容。

## 复用、未测与允许范围

复用b66da3c原审明确通过的H1/分帧/所有权及原件来源子项，同时本轮实际重跑受影响33项，不把旧NEEDS_FIX整体当批准。原候选源码保留为冻结历史，有效返修入口仅ps-semantic-bridge-repair-01/src/；其host/tests/入口随包保留，不替换默认算法或安装Vitis。

ASan+UBSan/UBSan本机缺运行库，构建失败原日志保留、NOT_RUN，不计通过。ARM/BSP、线程/ISR、真实异步/CDC、实际内存/缓存/DMA映射、生产ABI、上板、实时和完整H3均未验证；REALTIME_BLOCKED。未重跑旧FFT、录音、耐久。sizeof仅主机布局，不是ARM存储/WCET。

允许按准确范围归档旧候选/发布历史与本独立修复入口，原错误版不恢复为有效运行入口。规范轴阻断0、需求轴阻断0；作者自测标记原样保留，本报告记录B实际独立执行及限定批准。
