# 优化交接与责任范围

本次是用户明确授权的工程整合与远端交接。主模式 RELEASE_PACKAGING，仅复制准确源、整理配置和证据；本次行为/延迟/吞吐/时钟/复位/CDC/RDC、寄存器/IRQ/DMA 均无代码改动。没有自行批准算法或工程通过。

## A/B/C 从哪里着手

| 责任方向 | 包内源码 | 实际工作与来源 |
|---|---|---|
| A：采集、调度、缓存、前端、STOP/cancel 集成 | `project/rtl/a_frontend/` | 父候选 20 个源的原字节；FFT 包装调用 AMD 官方 FFT，不把 IP 算法称为原创 |
| B：定点数值与 DOA 后端 | `project/rtl/b_backend/` | 5 个源，绑定提交 `31c5c7bbcc9c70a943372898e9101beaac2ce9e3`；IFFT 调用 AMD 官方 IP；数学表用 SV 内嵌 case ROM |
| A/E1：集成及授权接口 | `project/rtl/integration/`、`project/rtl/runtime/` | diag_single_source_v1、signed_angle_map、runtime_servo_slice、既有 gate；来源按 source-map 保留，非所有内容都由 A 原创 |
| C：板级入口、VIO、证据保存、PWM | `project/rtl/c_board/` | 61.44 MHz PWM 适配、板级 wrapper/control/evidence/gate；four_mic_live_loop 基于 A 集成修改；sound_servo_clock 使用 AMD 7-series 原语 |
| AMD 工具/IP | `project/ip/reference-only/` | FFT9.1 rev15×2、VIO3.0 rev27、ILA6.2 rev19；Vivado 2025.2 正式生成，未手改厂商文件 |

这些是工程责任/冻结来源，不把 AI 辅助写码、官方 IP 或作者研究代码包装为全部自行原创。主包用于审阅/优化，不提供未知第三方来源的泛化许可结论。

## 稳定问题 ID（本次未修复）

### C-SYNTH-SLOW-001：B 大位宽组合运算

`b_backend/doa_math_pkg.sv:3,4,16,22,327` 的 wide_t 为 192 位；sqrt_rne 使用 96 次试乘平方的组合循环，除法/余数和动态移位亦经一般除法。backend 的状态机逐 bin 调用，不等于函数内部已分成 96 拍。原生日志存在大量 DSP 映射尝试、超出 220 DSP 的拒绝记录，支持这是主要资源/综合耗时风险。

旧诊断记录为 3884 条初步映射项、220 accepted、3658 因 >220 rejected。这些是推断/映射记录，不是最终 DSP 使用率；GB/q2 名字不能唯一反推每一个平方根表达式，也不能据此宣称最终设计一定放不下。

B 可先给定点所需宽度和多周期/流水化候选，再按原数学规格验证；若改变外部 latency/throughput/backpressure，需同时与 A 确认窗口、watchdog、valid/ready 与停止合同。不能为追求快综合直接换成近似 stub 或改变精度。

### C-SYNTH-SLOW-002：A/B 大缓存异步读推断为分布式 RAM

`a_frontend/pcm4_forward_fft_fixed4.sv` 的 8192×58 input_ram 以及两处 1024×256 pcm4_continuous_axis 队列具有异步读。旧日志初步 RAM 表映射为大量 RAM64M；B spectrum 缓存也有对应分布式资源。

板级没有意外复制 6 份完整后端：6 麦对由一份 backend 顺序处理，参数深度未由 C 意外放大。A 优先评估同步 BRAM 读/预取；改读延迟必须保持背压、数据/状态对齐和取消语义，不能只贴 ram_style 属性就声称修好。

### C-SYNTH-SLOW-003：VIO/ILA 不是当前主要证据指向

官方 VIO/ILA OOC 旧日志分别约81s/157s；主综合读取正式生成的 stub，与后续 OOC checkpoint 结合。并非从头重复综合官方核内部 RTL。C 新增结果缓存/选择器和观察信号仍占资源，也可能保持原本能裁掉的逻辑；没有做移除 VIO 的消融对比，不能说其影响为零。

### C-STA-LOOP-001：STOP/cancel 组合反馈（HIGH，OPEN）

原生日志：`[Synth 8-326] inferred exception to break timing loop: set_false_path -through u_core/u_calleri_2/a_stop_valid`。

A 原源码反馈链：caller a_stop_valid→observer.stop_valid→stop_fire/unexpected_close→local_cancel_now→adapter.local_cancel→manager.source_fault/stop_valid→caller。结构存在；lifecycle 合法状态下 closing 和 stop_ready 互斥，因此尚不能断言实际振荡或死锁。缺少正式可达性/网表/STA 证明，自动 false-path 不等于时序通过。不要另加全局 false path 掩盖问题。

本 ID 的别名为 C-SYNTH-LOOP-004。远端后来提到的 `I17-STOP-DESC-01` 属于另一候选/记录，尚未证明同因或此处已修，不能据此关闭本问题。

## 版本与接受边界

当前父 31 源 aggregate 为 `ad35f1978867fe3cbd565cc68250d9b0521ca04235673ec2fd6cab8173a7c407`；C 替换集成与 PWM 两文件并加入 5 个板级/时钟文件，实际共 36 源。逐文件以 source-map 为准。

B 准确候选已获限定接受（原接收记录 Issue14 comment6092885523）；组合曾处于 FIXED_PENDING_REVIEW。C 控制/存储/门控和 PWM 的有界测试已获各自范围非作者结论，原件放 evidence；均不覆盖整机综合、STA、真实声学和执行器行为。

2026-10-11 新的 A aggregate `784d0e79880dcb5a0f7bfa259337c896ec62c607d5ea55af72e47d3d54186f34` 与后续 PS/连续控制计划 **NOT APPLIED**。本包忠实保存 C 实际跑过的 VIO 候选，A 后续自行按原任务判断如何与新基线组合，不能用新版名字替换旧失败证据。

## 不变合同和未测

- 同一61.44MHz逻辑时钟，原50→96→61.44MHz时钟包装；没有新增命令CDC。
- 每窗口显式 START，默认观察、无运动许可；真实身份绑定/arm及STOP撤销命令资格保留。
- 不增加170～190°限制；物理机械范围须由现场事实配置。STOP并非断电急停；已开启PWM保持最后目标，冷复位默认物理输出低。
- 源字节搬运无 Cycle Contract Delta。完整功能/资源/时序/bit/LTX/板测未通过；功耗验收 NOT APPLICABLE。
- 两会话日志时间要分开：evidence/synthesis/main-runme.log 是11:33固定旧记录；latest-observed是13:03新会话的只读快照。CPU活动不能给出预计完成时间。

接收人下一步：A/B针对上述具体结构提出/实施优化，固定新源身份后有界验证；让C人工运行准确工程并回传原始综合/实现报告。交接不自动关闭 Issue17/19，不宣称任何成员已经接单。
