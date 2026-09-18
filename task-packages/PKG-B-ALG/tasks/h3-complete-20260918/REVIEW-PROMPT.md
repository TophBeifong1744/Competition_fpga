# 给成员 B 的独立复核提示词

请以成员B身份对A的四路H3 run05断流闭环做**增量独立复核**。上一版 `7ea3de519c1f86832fcb03fc8d852606273a8f8a` 已被你裁决 `FAIL / RETURN_TO_A`；新作者自检不改变这个裁决，除非本轮准确SHA经你复核通过。

仓库：`TophBeifong1744/Competition_fpga`。
分支：`task/member-a-0918-h3-closeout`。
增量父SHA：`7ea3de519c1f86832fcb03fc8d852606273a8f8a`。
B报告SHA-256：`5201FA3710F9192C767C03297F2F824E23F70BEA2299358B3AA963512F605EBD`（用户提供，A未取得报告原始文件验证字节）。
最终审查 SHA：见 A 的最终交付回报，并从远端分支实际 HEAD 独立核对后在 B 报告写完整值；Git 提交无法在自身文件中嵌入自身 SHA，不得只凭源码 SHA、移动分支名或作者日志签批。
发布状态：A 已在干净检出作者复跑并非强制推送，发布核对时本地/跟踪/远端分支三方相等；B 必须自行确认这一状态仍成立。
任务包：`task-packages/PKG-B-ALG/tasks/h3-complete-20260918/`。

先 `git fetch`，确认远端分支包含增量父SHA且HEAD与A最终交付SHA一致；从最终SHA建干净独立检出，按README单命令输出到新目录。对未受影响的18项输入/Q12边界等可按既定增量规则复用原证据，但断流链、run05冻结及本次改动必须独立查证。保留首次失败，不在A工作树中复核。

重点检查：

1. 前后各18项输入封存须为 Git blob 原始 LF 字节，2个本机CRLF文件只能按明确规则归一化，不可悄悄接受其它工作区变化；检查输入清单、文件SHA和包清单。
2. 核对同一Tracker的4513控制行：距上次3072为1441样点，返回 `gap_reset_acquire`、`ACQUIRE`、`fresh_valid=false`；它必须直接进入automatic使用的control_rows，不能仍是独立未消费的 `dropout_trace`。
3. 在发声样点4521（4513+共同延迟8）核对 `DISCONTINUITY_TO_SINGLE`，target bank 1→0，旧TTL 12680→null；4522的Q12权重应为 `[9,4087,0]`，5001应为 `[4096,0,0]` 且automatic PCM等于single。检查断流前4513～4520不得提前回填，断流后不得沿用旧方向或刷新旧TTL。
4. run05提交中冻结14数组及控制行/事件；独立检查器应比较冻结的 `auto_target_bank`、`auto_weights_q12`、`automatic` PCM及lag/DOA/Tracker等，而不只比本次新生成文件。分别篡改目标、权重、PCM，检查负例能失败。
5. 核查开发首错：`first-failure.redacted.log` 记录新增测试在旧实现上因无4513行报 `StopIteration`、退出码1；原始950字节日志的SHA-256见run05/README，仓库外只读备份可向A索取。脱敏副本不可误称字节原件。
6. run01～run04必须保留；18项输入封存、Q12边/对角正负边界、manual/automatic同数组反例和原有局限不得退步。center与quiet存在门仍均61/61过门，quiet fresh=0不等于背景被拒绝。
7. 无可信参考时正式方向及客观音频收益仍NOT_RUN；73900周期不是整链实测，91080B不是BRAM映射；SKL-001/002保持原限定，真实PYNQ/实板/实时未准入。相对增量父SHA不得夹带默认PHAT、原Tracker、RTL/Vitis或Skill源码修改。

报告写明实际审核完整SHA、复现命令/环境、执行与复用、数值差异与文件字节差异、问题、可准入范围、限制及明确裁决。作者39项测试和14组一致不等于独立复核；阻断先退回A、不合入。即使限定通过，完整H3仍不能在存在门、真实指标、AMD全链对照、实时/时序和板端输出未完成时签PASS。
