# 给A：R1/R2增量复核请求

**已办结：本提示词不再派发。** A已对准确ad30bda限定通过并关闭R1/R2，报告 `docs/reviews/b-engineering-ad30bda/REVIEW.md`，发布e4ac088；以下保留原请求。8400e71尾部三文档未在A批准/合入范围，不把本完成回执当成对这些文档的批准。

准确返修实现 **ad30bda694abc946db045192385ebdf1b8e1a956** 已推送原待审分支且直接远端查询匹配；请固定此SHA。后续仅文档补记不改变实现。交付核查main已为99bbf5fdc3b9bb44287fcc87404028e98291c75d，其中ca512a8的PSB-B-01～03另获限定主机C批准，不在本次返修范围；不要重派，亦不扩为真实异步/生产/实时批准。

请沿原任务复核仓库 https://github.com/TophBeifong1744/Competition_fpga、分支 `task/member-b-h3-engineering-closeout-20260921` 的R1/R2返修；准确新实现SHA见DELIVERY后续补记。原受审实现d3d2a3d4e78932830bf12bd84c0517b0a2092872、文档头dbd7ab5b35c75dfe9779a0452643d4bd2df24657，A报告结论NEEDS_FIX。本轮不请重审未受影响数值/预算、旧FFT/声学/E01～03。

包：`task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/engineering-closeout-20260921/`；返修入口 `repair-r1-r2/README.md`。收到的原报告逐字节保存，A的probe文件未收到，两条反例按报告描述从旧fixture复建；不可将B重建件说成A原文件。

仅一处已有执行源码变化：trace_scoreboard.py。R1从独立必需status捕获行的now建立每事务完成时刻下界，要求`all_required_visible <= available <= commit_now <= expiry`，保留同拍及延迟提交。若包含后级，expected_units必须独立加入后级完成。R2在所有有效拍（包括首次/持续背压及恢复接受）先检查source_sample严格整数且排除bool、域[-8,2^64-9]，available严格uint64，再做值与背压比较；startup负编号和PCM未改。

复现（Python3.12，无NumPy依赖，准确Git检出含原d3d2a3d/dbd7ab5对象）：

```powershell
python -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/engineering-closeout-20260921/repair-r1-r2/run_repair.py --repo . --out <不存在的新目录>
```

作者实际43项（34拒绝、9允许）全部符合预期；原实现运行退出1、返修退出0，A两例及指定18旧误接收记录保留。合法路径结果与原checker严格一致。新交付检查核对48输出/4源码/145旧文件原字节。旧check_delivery.py绑定旧checker源码，当前应使用返修入口，不重写旧run05哈希。

请独立增加R1/R2邻接反例并仅签准确返修SHA；其余1215向量、S28、RNE/饱和、极端PCM及预算复用你上次报告。CORDIC独立profile文件只绑定不变实现与原golden，8/17及20ms仍限研究候选；生产接口、可靠硬件时钟/状态、AMD/RTL、CDC、有限服务与完整H3未批准。本轮无上述工具/板测/声学运行。

若通过，由A或授权主流程按限定范围合入/发布；B不自审自合，不迁入生产默认链。待审分支及证据继续保留；无可以立即删除的未完成分支/工作树。实现分叉基线cf026cf29518488f8c7275b825f3487a8d892f80；后续main核对以本页顶部为准。
