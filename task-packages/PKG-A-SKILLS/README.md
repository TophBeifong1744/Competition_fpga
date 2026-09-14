# PKG-A-SKILLS 当前交付入口

SKL-001现为`fpga-module-verification`技术候选0.3.0，A制作、B待独立复核。SKL-002仍由原PYNQ任务独立制作；本包没有包含或批准其未审源码。

- 唯一SKL-001源码：[skill/fpga-module-verification](../../skill/fpga-module-verification/README.md)。不在payload保留另一份在做源码。
- 当前完整演示：[evidence/xsim-02/summary.json](evidence/xsim-02/summary.json)，含两个正常模块、两个故障变体及恢复复测；各子目录有result.json、命令日志和编译源快照。xsim-02对应补齐X/Z控制检查及运行环境记录后的当前源；xsim-01保留早期演示原始证据，不是另一活动源码。`work/`为可再生仿真缓存，收尾移除，不是交付源码。
- [运行器单元测试日志](evidence/unit-tests.log)：7项测试方法及多个子用例，不能当7次板测或7个迁移项目。完整文件身份见manifest.json，manifest不包含自身；B仍须固定真实任务SHA。
- [可见纠正与技术报告素材](report-material.md)、[复核入口](REVIEW.md)。准确远端SHA未生成，尚未提交/推送/合并；不能自签B批准。
- [旧版本归档](../../archive/2026-09-13-before-skl001-technical-upgrade/README.md)：旧活动v0、旧0.2.0完整包及旧计划原件。原包清单和作者测试不改写，新版不继承其批准状态。

本轮不动正式rtl/tb/sim/PS/BD/XDC或PYNQ候选；代码示例放在Skill内部，仅行为仿真，不是生产模块接入或阶段总验收。正常例复跑不是要求C重做已验收交付。复现命令在Skill README；每次使用新输出目录。

收尾：41份旧原件哈希一致，37份PYNQ及正式rtl/tb/sim文件前后不变。移除10个可再生work缓存目录及2个已核对等价的首次试跑目录，共355个文件、约1.69 MB；保留xsim-01/02的全部正式日志、结果、输入和故障源快照。缓存可按命令重建，首次试跑证据由xsim-01等价记录替代；没有永久删除旧Skill/旧包原件。包级.gitignore只解除原始日志的忽略，不隐藏未审材料。
