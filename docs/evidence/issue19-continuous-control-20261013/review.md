# 非作者独立判断

复核者：本聊天技能要求的只读 `fpga_reviewer`，`/root/control_expectations`。从需求独立建立预期，未完整继承作者对话；没有修改产品或测试资产。本文件由主代理转录其实际返回，不是 A 本人批准，也不是 GitHub 原生 Approve。

**最终自然链判断：PASS WITH CONDITIONS。** 七源候选 `f57493cf6d547d697f8430d3a3afa22a8a84c33d99e188936c46bcb85cd55f5a` 在限定范围内通过：三条自然合格报告、实际转台命令、一般在途STOP、保持STOP、真实排空、warm恢复及SID4首条合格结果。当前范围没有OPEN BLOCKER/HIGH，无需必要重测，不因包装重复运行。

- `full_noise-1` 的38个源及运行副本、8份日志哈希全部匹配；四个实际编译/展开/运行阶段退出0，无Fatal或墙钟超时。
- 完成标记 `cycles=5481560 reports=5 accepts=4 aborts=1 restart_sid=4`。CSV中SID3 generation1～3 eligible1；3,521,092周期ABORT与3,521,101周期eligible0报告身份完全一致；最后SID4 generation5 eligible1、raw Q8=0、映射180度。
- `natural-observations.json` 与完整CSV逐条一致，CSV哈希匹配；包中该运行10份原件与原目录逐字节一致，34项reference manifest全部匹配。
- 4次 `servo_angle_valid` 是送入motor driver的同S沿真实RTL命令。STOP关联不合格报告没有增加命令计数。
- 最终first_fault=0且首因跨warm保留；测试在首次HELD前未发RECOVER，超时进入HELD必锁存31。因此本次通过完整pipeline_quiet与capture_drained要求的正常排空路径。

**保留条件**：C-NOISE-COV-001通过限定“一般在途窗口STOP”解决声明范围，不证明活动FFT/IFFT IP中STOP。9M整链、默认4096 warmup、声学方向精度、全板资源/STA/CDC、实板转台及PYNQ仍UNVERIFIED/NOT_RUN。本判断不批准整机或上板。

最终局部判断 **PASS WITH CONDITIONS**：准确控制器 SHA256 `8b0b6863a658b8c482568baae20d22795cb9a17fa7e3962844c439a9b68acb47`，control-7 三源及六份日志哈希实查一致，编译/展开/运行完成，无 Fatal，`CONTROL_COMPLETE checks=171 reports=1`。

- C-CONT-RECOVER-001 CLOSED：接受恢复同沿撤 run/运动资格。
- C-CONT-FAULT-002 CLOSED：START_SOURCE/RUN/DRAIN 源故障即时传播并保首因；持续故障不刷新排空期限。
- C-CONT-TIMEOUT-LOOP-001 CLOSED：timeout 不读组合 report；反馈刺激 elapsed30 可完成清零，elapsed31 到期优先、报告屏蔽，保31首因。
- 重复 RECOVER 延长期限 CLOSED：返回02，不重发 warm、不重置计时/恢复观察。

末尾 reports=1 是测试末段冷复位后统计；前段100条持续完成刺激仍实际执行。control-6 是测试声明顺序编译问题，没有冒充产品错误或通过。

**范围限制**：上述同意不批准完整 continuous、整机、上板、实际后端服务上界、全板资源/STA/CDC、声学方向精度、PYNQ 接通。完整自然多帧、在途STOP/保持STOP、真实义务排空与新SID重启、诊断背压、默认4096 warmup 首结果期限仍须各自准确证据。

争议说明：已证实的期限临界组合环不能直接归因为 full_stop-4 的1M～1.5M区间缺进度，配置期限是约8M。后续 full_probe 已实际推进至1.215M但墙钟限时，缺少完成标记，不能因此判断整链通过。

A 在其准确工程组合上的接入/非作者判断及必要物理报告另行记录；本批不替代成员批准。

运行前自然链测试资产的非作者静态判断为 **PASS WITH CONDITIONS**，不能替代尚未完成的运行。宽带刺激仅作用于物理 mic_data，未替换内部结果或旁路资格；`servo_angle_valid` 是 runtime_servo_slice 接给 motor_drive 的实际同沿命令，注册 accept_pulse 仅为观察。有限断言覆盖三报告、至少两条命令、记录消费、STOP保持、warm恢复和新SID首报告；不签声学真值。

**C-NOISE-COV-001（MEDIUM，范围条件）**：STOP 触发 `ff_busy || doa_ip_obligation`，前者包含采集和预处理，不保证 FFT IP 已启动。交付限定“一般在途窗口 STOP”；活动FFT/IFFT停止仍UNVERIFIED。HELD不能独立充当排空证据，须核真实义务、控制转换条件及跨warm首因，运行完成后再作有限判断。

非作者已核 C 的6626位拼接与 B frontend_t 完全同序、同宽；这属于接口布局静态证据，不证明每个字段在首报告时符合数值预期。`full_first-1` 的数值资格失败保留，不能靠此静态核对将它改记PASS。

随后对 `full_first-1` 实际run源与日志哈希及完整6626位记录独立解码：16 unit_state全部OK=1；hardware_started/physically_retired=FFFF/FFFF；8路FFT输入/输出均1024，fixed4输入/输出/qualified均513；FFT status_seen/raw=FF/0；source_received=8192；cancel/protocol/numeric/first_error全零；source_report/abort=1/0；fixed4 context=1～8、retire_accepted=FF。结合B首错0及映射、gate、lease、report_current有效，目前没有已证实的前端拼接、终结合同或资格接合错误。

`numeric=0 && first_error=0` 可由有效频点不足、时延越界、有效pair不足、不可解几何矩阵、残差或方向范数拒绝产生；取消亦可能不给首错。缺少同报告的direction_reason、pair_state/valid/mask_counts、IFFT启动/计数、残差/范数及B取消字段，具体分支仍UNKNOWN，不凭较早报告或angle0定因。

冻结noise测试若真实完成且first_fault=0，可证明此前正常排空：其HELD前未发RECOVER；DRAIN正常进HELD要求完整pipeline_quiet和capture_drained，而超时进HELD会锁存31；first_fault跨warm不清除。该推论依赖最终完成日志，运行前未提前记通过，现已由上述最终复核核实。活动FFT/IFFT STOP范围条件不变。
