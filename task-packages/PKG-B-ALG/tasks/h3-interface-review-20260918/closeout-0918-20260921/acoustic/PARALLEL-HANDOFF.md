# 发给另一个 Codex 对话：9.18 完整定点合同收口

请并行承接 B 的9.18遗留“完整定点合同与预算依赖整理”，不要处理声学回退诊断；后者由原对话负责。本单尚未通过跨对话工具送达，需要用户在新对话粘贴。

只读源工作树：F:/NUEC/review-worktrees/algorithm-closeout-20260923
固定源提交：fe67547635ff254f9f91c7f917e8dedb6daf3363
待A审核分支：task/member-b-algorithm-closeout-20260923

先读AGENTS.md、docs/phases/2026-09-13-to-10-01/B.md，以及
task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923/H3-ALGORITHM-CONTRACT.md、REPAIR-R1-R2.md、dependencies.json和source/golden.py、integer_gate.py。

交付要求：
1. 按Hann、gate去均值FFT、DOA FFT、29→25、互谱/PHAT保护、IFFT、lag/插值、DOA/置信度、DAS/饱和列统一表：输入/输出位宽与F、缩放/RNE/溢出行为、准确代码与golden出处、现有测试、实际缺项和下一动作。
2. 区分portable Q30和AMD24位twiddle，不互借逐码通过；保留reference25，固定右移4只是候选。
3. 核实新gate不能自动复用DOA FFT，列8 FFT+6 IFFT的依赖、操作量和缓存生命周期；历史103364周期/107496B不等于全链WCET或实际资源。未知上界填null。
4. 对缺项给出最小增量验证计划，区分B可做的软件整数测试与A负责的IP/RTL/调度证据；不要重跑旧FFT/八段/run05/耐久，不改研究阈值、不新增模拟或录音，不修改one。

写入边界：仅写 F:/NUEC/validation/b-0918-fixed-contract-work/ 下的独立工作材料（不存在时可创建）。不要修改只读源树、原清单、其他任务包或主流程状态；不要提交/推送/合main。不要修改 F:/NUEC/validation/b-0918-followup/（归原对话）。临时目录是归档前工作区，不是另建同名任务包。

完成后回报表格入口、准确依据、实际检查/未测及剩余阻断。原对话统一汇总到既有任务包后交A完整复核；不能代签完整H3或生产格式冻结。
