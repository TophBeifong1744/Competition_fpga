# 非作者独立判断

复核者：本聊天技能要求的只读 `fpga_reviewer`，`/root/control_expectations`。从需求独立建立预期，未完整继承作者对话；没有修改产品或测试资产。本文件由主代理转录其实际返回，不是 A 本人批准，也不是 GitHub 原生 Approve。

最终局部判断 **PASS WITH CONDITIONS**：准确控制器 SHA256 `8b0b6863a658b8c482568baae20d22795cb9a17fa7e3962844c439a9b68acb47`，control-7 三源及六份日志哈希实查一致，编译/展开/运行完成，无 Fatal，`CONTROL_COMPLETE checks=171 reports=1`。

- C-CONT-RECOVER-001 CLOSED：接受恢复同沿撤 run/运动资格。
- C-CONT-FAULT-002 CLOSED：START_SOURCE/RUN/DRAIN 源故障即时传播并保首因；持续故障不刷新排空期限。
- C-CONT-TIMEOUT-LOOP-001 CLOSED：timeout 不读组合 report；反馈刺激 elapsed30 可完成清零，elapsed31 到期优先、报告屏蔽，保31首因。
- 重复 RECOVER 延长期限 CLOSED：返回02，不重发 warm、不重置计时/恢复观察。

末尾 reports=1 是测试末段冷复位后统计；前段100条持续完成刺激仍实际执行。control-6 是测试声明顺序编译问题，没有冒充产品错误或通过。

**范围限制**：上述同意不批准完整 continuous、整机、上板、实际后端服务上界、全板资源/STA/CDC、声学方向精度、PYNQ 接通。完整自然多帧、在途STOP/保持STOP、真实义务排空与新SID重启、诊断背压、默认4096 warmup 首结果期限仍须各自准确证据。

争议说明：已证实的期限临界组合环不能直接归因为 full_stop-4 的1M～1.5M区间缺进度，配置期限是约8M。后续 full_probe 已实际推进至1.215M但墙钟限时，缺少完成标记，不能因此判断整链通过。

A 在其准确工程组合上的接入/非作者判断及必要物理报告另行记录；本批不替代成员批准。
