# B 限定接收与发布记录

2026-09-20。批准 SHA `21c141b223936730c2ce5139624fcedb412adafb`，结论见 B-REVIEW.md。

发布基线为实际远端 main `d63544d6c48b9cfaaf2c629536de2647b8762f84`。主线此前没有 timerfixed-entry-01，因此按准确目录快照导入完整268份候选文件；该版本包含原入口、repair-01 和此次 repair-02。没有合入作者分支的其他路径或改变当前 main 的其他成员成果。候选入口保持任务包位置，未部署 A 实际工程。

集成副本再次通过267/209/87项清单和94项Python回归（含14次Tcl模拟）；执行发生于 B 本机普通用户环境。此次导入完整候选到更新后的主线，故扩大集成回归到包内全套入口测试；后续未再重复全套。Git index 中268份文件与准确审核提交完全相同。首次导入的一处 Windows 长路径错误已通过 core.longpaths=true 重试解决，未修改冻结文件。空白检查结果及原文压缩保存于 integration-summary.json 与 integration-whitespace.txt.gz。

本批 B 新证据均位于 docs/reviews/timerfixed-repair2-21c141b；B-EVIDENCE-SHA256.json 覆盖发布时的复核证据，不覆盖后来另存的收尾说明。本地包外证据源另有同字节副本用于恢复，最终收尾时核对去重。

发布前共享仓库 F:/NUEC/develop 保持 task/member-b-four-track-01，HEAD f364a023830b105e6075d853da83cfd51127cf64，未切换或重置；全仓未提交/未跟踪检查为空，本任务路径的忽略材料检查为空。其他已有工作树、A共享工程与实际引用入口未改。此文件写入时尚未推送；实际推送 SHA、直接远端复核和本机 main 对齐结果由后续 CLOSEOUT.md 记录。

作者分支及旧 B 反馈工作树仍可能被继续任务或实际工程引用，本次不删除、不代签 A 侧同步。只对本次新建的两份 B 独立工作区在发布和可恢复性核实后清理。
