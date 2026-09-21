# 交付/基线记录

**2026-09-21批准接收：R1/R2已由A关闭，准确ad30bda限定通过且远端已发布e4ac088。** 本页下文NEEDS_FIX/待审是历史。技术结论引用 [A正式报告](../../../../../docs/reviews/b-engineering-ad30bda/REVIEW.md)，B不重复自审或代签生产。

**A复核后状态覆盖（2026-09-21）：原d3d2a3d整包NEEDS_FIX；R1/R2作者返修已完成、待A增量复核。** 返修入口 [repair-r1-r2/README](repair-r1-r2/README.md)，原报告字节保存，旧数值/预算证据不重跑。以下原交付记录保留历史。

实际日期2026-09-21。原共享主仓库 `F:/NUEC/develop` 保持 `task/member-b-four-track-01` / `f364a02`，本轮未切换/重置它，也未处理其他工作树的在途改动。使用 `F:/NUEC/r/h3e`，待审分支 `task/member-b-h3-engineering-closeout-20260921`；这是既有任务包的工程增量分支，不是新建同名任务包。

提示基线 `db549b55f134d2b9dbfa5baef7d1ec19e288664b`。Git直连多次失败后，只读发现用户系统已启用 `127.0.0.1:7897` 代理；单命令 `git -c http.proxy=http://127.0.0.1:7897 fetch origin` 成功，未改变全局代理/Git配置。最终开发基线为 **cf026cf29518488f8c7275b825f3487a8d892f80**，隔离分支从db549b5依次快进至eb3a448、cf026cf；没有合入自己的实现到main。

已读该基线AGENTS、current-status、B执行单、9.18 recheck、status-b0643b1/B-REVIEW、b-dynamic-268e526/REVIEW。db549b5之后新增e473824声学机制限定批准及cf026cf复核证据原字节收尾；只读批准边界，无进一步生产profile/AMD/RTL/实时/H3批准。未重跑声学研究，也未写其目录。

已关闭项事实固定：fe67547635ff254f9f91c7f917e8dedb6daf3363；b5913e596e28b30f9e04cf2c9ba365430b8914df；349501c560f7f9d195ebbf52a4c47f34695bfeae；f879a54cf40359209895af955bcef92accdf79ea；a7f70c5149a6503effdbbf16a9903d42c2d39e6d；268e52627d091b8909890b43586c70564563132e。引用既有批准，不借本轮作者测试扩大其范围。

提交范围限定为 `task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/engineering-closeout-20260921/`。源码/配置、测试夹具、旧函数反例、运行命令/日志/结果、合同/缺项/预算齐全。根/父冻结清单没有重写；父 `* -text` 原字节策略继续生效。被全局忽略的本批13份 `.log` 明确强制加入，不能留在忽略区假称完整交付。

候选准确提交与远端确认由本页后续发布补记绑定。技术状态为**作者自测完成、待A独立审**；保留当前工作树/任务分支供审查，不清理未完成任务。共享main本地引用没有由本任务强行同步；这不是main发布批次，不宣称三端main同步完成。

## 发布补记

准确实现候选 **d3d2a3d4e78932830bf12bd84c0517b0a2092872** 已推送同名待审分支；直接 `ls-remote` 确认远端匹配，main仍为cf026cf，未推main。相对cf026cf仅本子目录151个新增文件，无外部路径变更。随后仅本页与A提示词绑定该准确SHA，不改变实现/配置/测试结果。

最终run05三阶段退出码0/0/0；delivery-check02核对28份输出、7份运行源码/配置及14条本地文档链接通过，所有13份日志均已跟踪。工作树本批无未说明的ignored材料。旧原件/声学目录/main状态无本轮写入。推送不是批准，A尚未通过工具收到或接单；提示词由用户复制转交。

## R1/R2返修记录

本轮起点dbd7ab5；安全fetch后origin/main仍cf026cf，未见本包后续批准。唯一改变的已有执行源码为trace_scoreboard.py；新增增量验证/运行/交付检查、原A报告副本、前后记录与CORDIC独立profile绑定。旧run05、原数值/预算源码、A/C、声学研究及主流程状态文件不改。

实际 `repair-r1-r2/run_repair.py --repo . --out <包内>/repair-r1-r2/validation01` 退出0；43项（34应拒绝/9应允许）均符合预期，先前before退出1保留。48份输出、4份运行源码、145份旧文件原字节校验通过；A原报告SHA256为13fab2584b5e16ac9c367a207871723f204f8280d8d142d4e89b13160b25dbd8。旧checker与数值依赖不是用放宽哈希处理，新入口分别校验旧证据和新实现。

本轮没有运行CORDIC数值、FFT/IFFT、AMD/RTL、one/Vitis、板测或声学测试；A此前通过部分按报告复用。状态是作者修复完成而非A已关闭R1/R2；REALTIME_BLOCKED不变。返修准确提交与远端确认在随后补记绑定，仍在原待审分支，不推main。

返修实现准确SHA **ad30bda694abc946db045192385ebdf1b8e1a956** 已推送原任务分支，ls-remote精确匹配；305份包内文件与提交blob原字节一致。随后只补文档绑定，不改该返修实现。

交付时远端main更新为 **99bbf5fdc3b9bb44287fcc87404028e98291c75d**，已fetch并读 `docs/reviews/ps-repair-ca512a8/B-REVIEW.md`：ca512a8be7978ab6ca2ade3d5e0b922e53a89c79 的PSB-B-01～03获限定单执行者主机C通过，不能继续按全未实现派工。该更新未改变本包、AGENTS或FG依赖，不需重跑本返修。真实ARM/BSP、异步/CDC、生产ABI、实际DMA/cache、实时/H3仍未批准。当前任务实现仍在cf026cf分叉的待审分支，本轮没有将其合入main或代签该PS工作。

## A批准后的B本机核对

- 准确批准ad30bda694abc946db045192385ebdf1b8e1a956；A合并a78f81bc5c65088713c4e4bd473ed0f557820c35，远端报告/发布e4ac088bd7c071c8cc2bbdfd741235cc0e9ffad8。A已完成合后43项/145旧文件/48输出/4源码检查，B只核对报告及Git身份，不重复算法或轨迹测试。
- 本机 `F:/NUEC/develop` 的main引用从99bbf5f安全快进到e4ac088，使用祖先检查、确认main未在任何工作树检出及旧值条件更新；origin/main同SHA、ahead/behind=0/0。实际共享目录仍保持用户原 `task/member-b-four-track-01` / f364a02，未切换或重置；main引用同步不等于把该目录切成最新main。
- 当前 `F:/NUEC/r/h3e` 将已批准远端main合入原任务分支，合并48c69d1，无冲突，原尾部8400e71三文档保留；没有反向合入/推送main。A明确未批准这三文档，另加本完成回执也仅留任务分支。不能为删分支而将未审尾部夹入main。
- 本批执行源码/冻结证据以准确ad30bda与A报告为准；没有新的数值、AMD/RTL、板测或生产接入。活动入口保留包内repair-r1-r2，不迁默认算法。
- 本任务工作树本批未提交/未跟踪/忽略的有用材料已核查；此前3份尾部文档及本回执都纳入任务分支，不仅留本地。技术交付已关闭；未审文档分支保留，删除对象为无。
- A报告所述另一设备1001个未跟踪路径及main同步遗留由A/主流程处理，本机无法代签。B本机引用同步与A共享目录收尾分别报告，不能混成整仓/三台机器均已同步。
