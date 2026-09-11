# 004-R1 独立复核：技术验证通过，交付清单待收尾

日期：2026-09-11。固定输入：69dd471aa064aacd61d94965db8255d0fea5b2cb。

结论：TECHNICAL_PASS / NEEDS_DELIVERY_FIX。上一轮空格路径问题已关闭，不需C继续修改RTL或重跑仿真/BD；但当前包的清单和状态文字尚未对齐，待唯一收尾任务004-R2后再正式交B复核。此结论不是B代签、main合入或整机验收。

## 实际验证

- 比较99a48b0与本提交：核心、包装、TB、功能复现脚本及旧仿真/BD日志未变化。功能结论沿用[上一轮独立重跑](../99a48b0-20260911/README.md)的1/3/默认32/64位共228次核对PASS，本轮没有重复运行。
- BD脚本唯一代码修正为TB导入参数增加list包装。将当前submission原样复制到含空格的临时路径，直接运行作者脚本；输出工程路径也含空格。
- Vivado 2025.2，SW Build 6299465，xc7z020clg400-2；本次退出码0。源码类型检查、默认32位和修改3位的模块引脚/外部端口检查、两次Validate及ALL BD TESTS PASS均通过。
- 导入工程中的核心、包装、TB各只有一份，SHA-256逐一与固定提交的源文件匹配，未偷用其他同名源文件。
- 本轮保留4条预期警告：19-5661无关联数据总线、19-11770无FREQ_HZ、两次41-2925导出Tcl依赖RTL提示。孤立模块测试不虚构板上频率，正式集成由A依据真实时钟合同处理。

### 命令及原始证据

工作目录：C:/Users/Toph Beifong/AppData/Local/Temp/C004 R1 be5bec。使用本机F:/AMD/2025.2/Vivado/bin/vivado.bat执行：

```powershell
vivado.bat -mode batch -source submission/scripts/rebuild_bd.tcl -log bd-review.log -nojournal -tclargs 'project with spaces'
```

非受限独立进程执行，避免上轮已确认的受限环境建目录错误；未改全局环境或共享one工程。仅在进程缺架构变量且系统X64时临时补AMD64并于结束恢复。

原始[BD日志](logs/bd.log)、[32位端口](logs/ports-32.txt)、[3位端口](logs/ports-3.txt)及两份导出Tcl集中保留在logs/。运行时间20:37:19至20:37:32，UTC+08:00。

## 唯一未关闭项：交付清单及状态说明不同步

规范/交付轴1项问题；功能/BD需求轴未发现新问题。

当前file-manifest.json共33项，32项字节数及哈希匹配；README.md不匹配。另有6份新成功证据未列入清单：

- logs/rework_01_20260911_194059/bd.log
- logs/rework_01_20260911_194059/exit_code.txt
- logs/rework_01_20260911_194059/evidence/bd-default32.tcl
- logs/rework_01_20260911_194059/evidence/bd-width3.tcl
- logs/rework_01_20260911_194059/evidence/ports-3.txt
- logs/rework_01_20260911_194059/evidence/ports-32.txt

当前README开头说明无空格路径BD已成功，但版本行仍称“验证未完成”，历史段仍写“R1仍待成功BD验证”；应明确各次运行的日期和历史/当前状态，不覆盖原失败日志。上述遗漏不否定本轮技术PASS，也不能直接宣称当前完整包的清单已通过。

原清单SHA-256：d672c884b92b5a35c346c62480c3fa18bde81c0c3a9b6ebf0092bf13ac502613。不由验收方改写作者清单，C按[004-R2收尾操作单](../../instructions/rework-02.md)完成。

## 收尾及未接入项

按docs/phase-closeout.md核对：这是单包独立技术复核，不是9月16日阶段验收；本轮无新增获正式批准的源码。004尚待交付清单收尾及B正式复核，暂不归入活动rtl/tb/sim，不改9月10日冻结归档。本轮没有综合、时序、布局布线、板测或实际系统BD接入。

后续由B固定修正后的完整包批准，主流程/A再按阶段规则安排包装、TB和BD恢复入口的活动目录归位，并在新位置验证；本报告和原始日志作为后续阶段归档输入。不得将TECHNICAL_PASS写成活动集成或阶段收尾完成。
