# E1：B 本机批次收尾

2026-09-16。批准对象5606e1a9d9a6183ceff7cffc1bb4f8aac44bb79c，仅E1实现与该次300秒+十次10秒实板证据归档，不是安全加载或M1/H3批准。

| 回报项 | 实际结果 |
| --- | --- |
| 批次与范围 | 仅endurance-test-01准确172文件，以及包外docs/reviews/endurance-5606e1a的B报告/复现证据；没有timerfixed-entry待审实现、Skill、活动RTL或实际工程改动 |
| 合入与发布 | E1合并ccaf24c2c6035fb4610ac9ea512f4fc20474f485；复核报告提交96e54144cff2a76b54032310a4d56c34c2412ee6已非强制推送main。直接远端核对main=96e5414、E1分支=5606e1a；本收尾记录随后作为独立文档提交发布，最终main SHA见回报 |
| 合并后验证 | 新位置171项发布清单、23项Python及真实对象/ELF/串口归档检查通过，见postmerge01。合入包字节与5606e1a完全一致；不把主机C模型或历史构建称为新实板 |
| main对齐 | 发表本记录前，本地main、origin/main、直接远端均为96e54144cff2a76b54032310a4d56c34c2412ee6，领先/落后0/0；本记录发布后再次对齐核查，不强推 |
| 实际共享目录 | F:/NUEC/develop仍在task/member-b-four-track-01，HEAD=f364a023830b105e6075d853da83cfd51127cf64。已修改/暂存/未跟踪/忽略项均0；未切换、重置或删除此其他任务。main引用对齐不等于共享当前文件已切换为E1 |
| 旧main独有工作 | 原main=9936613e99a5ac4c2d080375697d8447f5f377fc仅比旧基线多此前continuous收尾的两份文档。已保存并推送preserve/member-b-main-before-e1-20260916，直接远端确认仍为9936613。它未夹带进入E1主线；后续是否整合由对应任务处理 |
| 本批材料 | 包外原复核/集成工作树无漏交材料。通用忽略规则曾漏掉spec/deadline_boundary.log，已显式纳入Git，未改忽略规则。B原字节清单90项加自身，BATCH-CLOSEOUT及closeout-state为明确后加的独立收尾记录 |
| 材料恢复 | 原件由Git准确5606e1a恢复；复核脚本/结果已在main。完整B原始输出、依赖提取与派生主机程序留一份F:/NUEC/review-evidence/endurance-5606e1a-B-review.zip，151文件，2489374字节，SHA256=115742311f3d66984e52577c608ddb5e3b575a8fbbe49eaec66a61a5dea9f455；ZIP逐文件哈希及完整性已验证 |
| 已清理 | F:/NUEC/review-worktrees/endurance-5606e1a已在核实干净/固定SHA后正常移除；F:/NUEC/review-evidence/endurance-5606e1a重复展开目录已核实准确路径与ZIP哈希后删除。作者原始工程、日志或唯一材料未删 |
| 最后临时对象 | 本记录发布并核实后，正常移除本轮干净集成工作树endurance-main-5606e1a及已完全入main的B临时分支review/member-b-e1-5606e1a；最终执行结果见发布回报。两者均可从最终main恢复 |
| 保留与A侧事项 | A待审E1分支、A发布副本/共享目录和实际工程引用尚未由A本机确认无继续任务，保留不删；timerfixed入口分支与相关B反馈仍待修复，保留。A本机同步、实际工程入口更新及其清理均不由B代签 |
| 本批遗留 | B本批有用材料未说明遗漏0；其他任务的9936613文档提交已明确另存，不算E1漏交。A侧待核查不冒称完成；本次没有新硬件任务或新阶段门 |

传输记录：初次保留分支推送连接中断，随后一次自动权限审核超时未执行；按工具允许重试后保留分支和main推送成功。没有强推或在失败时删除源材料。

本地核查原命令/输出和备份回执见closeout-state.json。全量作者diff --check仍为退出2并保留原字节；这与归档清单验证结果分别记录。B不对无法访问的A设备声明已同步。
