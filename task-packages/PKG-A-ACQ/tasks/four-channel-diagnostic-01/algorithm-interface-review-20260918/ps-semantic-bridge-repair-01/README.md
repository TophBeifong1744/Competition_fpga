# PSB-B-01～03 返修：主机 C 候选

实际日期2026-09-21。作者实现与复跑完成，待B增量独立复核；不合入main。独立返修源码入口为本目录src/，不是原候选src/，不安装到Vitis/one。

## 固定输入和批准边界

- 原候选：fbbaa161098582ba1e5e112b86d39533769bb3e7。
- B反馈：b66da3cd32cf91708cc13bc45608afa3a503bec0，docs/reviews/ps-bridge-fbbaa16/。spec/与standards/原反例按Git原字节保留在evidence/run01/feedback/。
- 本分支：codex/toph/ps-bridge-repair-20260921。待审完整SHA由发布回执及本文件所属Git提交确定，不用父提交冒充。
- 原ps-semantic-bridge-candidate-01目录1481文件、旧清单、原源码和历史失败不改。返修单列同级目录，原封闭清单仍可使用。
- 原host.c及run_host.py按原字节复制，PINS未更改：0abdc91仍仅作历史路线及原件保护；f879/F5接口/core等原引用不变。a7f70c5只作为单列的Python语义对照，不替代旧0ab，不运行a7当C测试。

## 三项修复

| 问题 | 修复及边界 |
|---|---|
| PSB-B-01 | 显式error/控制先处理；对整批有效身份的所有片段完成binding/status/payload验证与聚合，然后单独按slot顺序commit。不能因早先片段已齐status就提前提交。任一片段一致性冲突使对应事务INVALID，本批不产生任何新commit；其他未冲突事务可保留聚合状态，但必须另一次显式dispatch才有机会提交。 |
| PSB-B-02 | 先区分session，再安全判断slot/代次。当前session未知error（含slot越界、已释放、未知generation）统一保守fail-stop；非当前session仍STALE隔离，不阻断同批合法当前事务。 |
| PSB-B-03 | acquire先选第一个合法READY候选，再比较generation，UINT64_MAX仍是合法token，不再与“尚未选到帧”的哨兵混淆；下一次分配明确COUNTER故障，不回绕。 |

增加PSB_COMPLETION_ERROR审计事件（8）和PSB_COMPLETION_CONFLICT原因位（32768）。未曾提交的冲突撤销该事务；冲突涉及历史已提交事务时保守fail-stop并撤销可用性，不假称撤回已发生物理效果。原was_committed不清除。头文件新增枚举属于未冻结候选，不对外声称ABI兼容或生产批准。

status=0只触发状态/时间复查，payload仍不被采纳；非零status片段必须一致。hooks仍仅同步只读，禁止重入；实现不证明并发线程、ISR或真实硬件状态屏障。逐槽commit不承诺多事务物理输出原子性；仅保证本批一致性检查完成之前没有commit。

## 实际结果

- evidence/run01：准确B原probe在O0/O2分别对原版和修复版执行。原版同批冲突可take及当前越界error不停止均重现；修复后冲突take拒绝、当前未知error停止。检查具体输出，不以脚本退出0当修复通过。
- 原standards/generation_max.c在原版退出0记录缺陷，在修复版退出1且acquire_rc=0；这是原脚本期待旧缺陷的反向返回，不能误判成修复失败。新增断言独立验证实际acquire。
- 原33项对照全部通过，O0/O2各9组C自检、27131断言通过；原参考、host.c、run_host.py未改。run01首次新增120场景通过。
- evidence/run02仅新增两个generation相邻边界测试，最终122个场景、3949断言在O0/O2均通过，输出一致。不是120+122个独立案例；原33项复用run01，通过源码与原测试字节相同核对。
- 122场景包含72个冲突排列、24个合法重复/互补/跨事务排列、6个分批/历史提交冲突/互补、8个当前未知error、6个旧session隔离、6个generation场景。检查commit hook次数、was_committed、实际take及输出值，不仅检查dispatch返回码。
- generation覆盖合法MAX、两个READY帧顺序（含物理slot复用倒序）、MAX结果token及分配/发布时耗尽。边界通过合同允许的计数注入，不声称实板自然运行至2^64。
- GCC16.1.0；C11，O0/O2，Wall/Wextra/Wpedantic/Wconversion/Wshadow/Werror。所有成功构建stderr为空。
- ASan+UBSan及UBSan缺运行库，构建失败保留，NOT_RUN。ARM/BSP、真实并发、RTL/CDC、实板均NOT_RUN，REALTIME_BLOCKED。不重跑旧FFT/录音/耐久。

主机bridge布局仍由host33/memory-O*.json给出，不能当ARM布局或实际DDR地址。新批处理为软件有界循环，不给出Cortex-A9 WCET结论。

## 复跑

在准确候选的隔离短路径检出，确保固定依赖Git对象存在。不要在共享脏目录准备或覆盖依赖。

```powershell
$base = 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918'
# 仅当该依赖目录不存在时；已有目录先核对，不覆盖他人工作。
git restore --source=0abdc91c57787b7c868a797b88f35129de169faf --worktree -- "$base/engineering-closeout-20260923"
$fix = "$base/ps-semantic-bridge-repair-01"
python -B "$base/ps-semantic-bridge-candidate-01/tools/seal.py" --verify
python -B "$fix/verify_repair.py" --cc <GCC绝对路径> --out <包外不存在的新目录>
python -B "$fix/manifest.py" --verify
```

f879增量已在候选父历史中，0ab工作文件只作原保护校验，不暂存到本次分支。准确对象和SHA见原run_host的PINS和本轮bindings.json。verify_repair从Git导出B脚本和旧C，再用修复源码短路径快照编译，保存真实命令、stdout/stderr、源码及依赖哈希；当前版本将直接执行最终122场景和原33项，不必复跑run_boundaries.py。首次作者运行路径位于临时嵌套目录，后为保持原封闭包有效而整体移至此同级目录；源码原字节未变，历史命令路径不倒填。run_boundaries.py仅用于追溯run02增量。

本轮没有C功能测试失败后删改记录；旧B反例、旧33项失败历史、缺sanitizer库记录及中间120场景版本均保留。不把B缺陷记录器的预期退出码与真正断言失败混淆。

## 回交

申请仅PSB-B-01/02/03及相邻主机C合同回归。请B按准确新SHA独立增量裁决；旧Python返修批准不继承给C。本分支只新增此目录，旧实现不改，未合入main、未改Vitis/one，未批准生产ABI/实时/完整H3。
