# E 派工执行：生产差异准备与测量入口

本轮交付收口以 `E-HANDOFF-20260921.md` 为一页入口。最新派工704407e明确由C完成新八段，覆盖本文先前单段描述；拓芙不代采整理。本文算法建议和16服务测量计划未变，未成为生产批准。

已接收 dispatch 顶部 2026-09-21 E 小节；已采用2026-09-17增量复核。输入 main=`aadb30a14a42d1567de2d0d62f8ab1d24787e2be`，本机 main/origin/main/直接远端一致；fetch 无需快进，未移动其他工作。本文件及 `prepare_production_delta.py` 是原任务包新增内容，不修改冻结合同和历史清单。

执行期间新增派工 `3592b5178aa5ed25770a7ebb455aa4a49cc806d0`，仅修改dispatch且无本地冲突，已纯快进共享main。最新单项覆盖：本次一段试录全流程由C完成；E提供入口技术信息及接收检查，不要求拓芙现场操作。下文已按此更新，不代签C接单或完成。

## 1. 本轮实际完成与停止点

- 读取 readiness 收尾与 B 对 `f08556d01821d6c3c8204fdac2c38f53b2107c05` 的限定批准。原稿“ca512待审”“d3d缺陷待修”按最新报告覆盖：ca512 PS桥、ad30bda R1/R2已关闭，不重新派修。
- 集中形成下表供 B 一次确认；不是代签，不修改 reference25/阈值或生成生产 profile。
- 补 fixed4 **仿真输入/整数期待准备**，只检查独立有理数期待的少量手算锚点、输入域、覆盖类别及服务项绑定。没有待测 RTL，因此不是 RTL逐码PASS；不重跑既有262401个软件用例或FFT196帧。
- 将16服务映射到测量位置、计数口径、争用与停止条件；真实上界不伪填。未分配DDR地址，未创建后级RTL、IP或工程。
- positioned-single-source-01 只有旧preflight失败，尚无本次BIN/UART/照片。失败是加载检查器依赖哈希不同，不证明硬件出错；未放宽或替换检查器。

## 2. 给 B 的一次确认表

以下是A建议，要求B回复准确实现/参数来源及同意或调整。B此前限定同意候选路线，不等于最终profile冻结。

| 决策 | A建议/需B确认 |
|---|---|
| 数制/尺度 | 新profile显式选择fixed RNE4到S25；DOA窗S24、activity去均值窗S25分域；明确FFT29输入界、AMD24 twiddle对应golden。portable Q30期待不得用于AMD逐码。确认epsilon/band/mask对应单位和确切参数对象。 |
| 后级 | 采用已批准节点的准确实现；新S23F20/S28归一化CORDIC分别绑定实现与输入域，不能用容纳位宽冒充误差证明。 |
| 完整状态集合 | A提议每事务要求transport、frame-domain、window、FFT config/data/status、fixed4、gate、PHAT、IFFT、lag/DOA、tracker及binding闭合；是否存在合法跳过stage必须由profile声明SKIPPED及原因，不把缺状态当成功。B确认算法必需项；A负责传输必需项和错误合并。尚不指定生产bitmask。 |
| 身份 | config/geometry/numeric三份32B不可变身份；内部session/generation uint64不回绕。boot身份、规范化hash字段排序/单位/schema与固件绑定A负责草案，B确认算法字段全集。token不复用至回调退役。 |
| 样本时间 | 保留H1原ID，frame末ID决定TTL；all-required-visible ≤ available ≤ commit_now，commit/take双查。DAS采用268e526的8前视/17历史，source=emit−8，状态时基转换显式+8。 |
| 输出/停止 | 2beam+最新pending；audio_smooth_stop最多960样点平滑回mono，不是fatal/session_abort。后者撤销未消费逻辑结果并运输排空；晚错追溯，不承诺回滚已输出声音。 |
| 所有权 | RX完成/cache核对→成功复制入算法自有环→释放RX；帧借用到算法最后读完；结果/审计各自释放。B确认算法读取结束及结果状态闭合事件，A实现cache/屏障/队列。 |

## 3. 16项服务测量操作设计（本轮没有实测）

共同要求：每份后续证据绑定源码commit/hash、ELF/map或XCI/DCP、工具版本、实际频率与时钟锚；记录请求、首项接收、最后payload及最后必需status时刻。启动延迟、II、完整服务/最大等待分别计数；样本最大值不是WCET证明。禁止以UART打印计时关键段。

| 服务 | 推荐位置及准确构建入口 | 测量/可证量；资源与暂停条件 |
|---|---|---|
| capture_dma_cache_copy | 现有continuous_platform/S1采集作为参考；未来PS桥集成另选应用 | DMA完成→invalidate/guard→复制结束，CPU计时器及实际CPU频率；最多3包/hop；DDR仲裁/cache最坏情况未界定，环满fail-stop。 |
| accepted_row_frame | ca512a8 PS桥修复src，ARM构建NOT_RUN | worker入口→帧READY，按实际代码测跨包/滑动/双槽HELD；CPU频率未知；消费者持有不能覆盖，背压等待分开计。 |
| mean_two_windows | 新独立PL候选尚未建立 | 每hop8192窗乘；均值累计/除法/RNE另计；ROM端口与乘法器共享、II/启动均未知；S25新增域先准备。 |
| fft8 | 既有FFT29配置准确对象复用，新增组合构建无 | 8事务各config握手→最后status，拟100MHz；7366仅历史无背压槽，输入/output ready停顿另算。 |
| fixed4 | 本轮只产整数测试向量，无RTL | 8208分量/hop；拟100MHz；若单分量II=1仅条件吞吐项8208周期，不是服务上界；预取、背压、overflow闭合均另计。 |
| gate_power_state | 已批准B节点golden，PS/PL映射待profile | 528平方、4宽除，跨帧门状态；必须测阈值附近路径及state依赖；频率/II未知。 |
| cross_mask_phat | 后续独立PL数值服务 | 3078互谱、最多474归一化；拟100MHz；sqrt/Newton/除法共享宽运算器及RAM端口，迭代上界/II未知。 |
| conjugate_ifft6 | 25位逆核候选未生成 | 6 config→last status，共轭端点守卫；拟100MHz；7406历史槽不含新组合握手；与FFT是否分核按profile确认。 |
| lag | 独立PL候选尚未建立 | 86搜索候选、最多12插值/margin除；拟100MHz；搜索/除法及共享相关RAM停顿须记录。 |
| doa_cordic_tracker | PS首选，ad30bda/268e526数值来源 | LZC/移位/24步及除法，实际CPU频率；HOLD/fresh/拒绝分支计入；软件工具耗时不换算A9 WCET。 |
| rom_control | PS DDR只读ROM候选 | 净552960B；按实际请求测cache miss→两bank更新完成；每请求8B延迟码外还有身份与协议；到达上界未定，不臆定每hop一请求。 |
| das_two_beams | 拟100MHz独立服务，未建RTL | 9216乘/8704加/2048RNE每hop条件运算量；17历史ring端口、2bank切换、pending覆盖分别测试；持续输出不能借控制队列停顿暂停采样时间。 |
| config_status_commit | ca512 worker + 待定义运输事件桥 | 第一事件→批预检→最后状态可见→commit/take；CPU频率未知；14变换及后级状态闭合，ISR批大小/屏障等待未定。 |
| arbitration_cdc_reset | 采集61.44MHz与拟数值100MHz边界 | 需同步器/FIFO/reset generation协议及报告；记录竞争主设备/最大突发/仲裁饥饿；尚无有限等待证明。 |
| output_backpressure | 输出介质尚未选择，不能提前接DAC | 分别测音频行/结果描述符到达包络、服务率及最大blackout；R<r或T未知仍BLOCKED，8槽不构成证明。 |
| audit_drain | PS worker→独立日志消费，64条已有软件容量 | 生产/ack间隔与突发错误密度；不可只算PCM队列。满时显式保留故障，不能悄然清零；频率/最坏服务未知。 |

未来测量必须先确定生产profile、用户选择工程与授权；本表不是要求现在启动工程。缓存需区分178856B主机布局、ARM sizeof/map尚未知、552960B ROM净载荷、DAS 204B紧凑/272B int32二选一以及scratch/FIFO/栈同时存活。全系统峰值与16服务上界保持null。

## 4. 仿真准备与结果分层

先选择fixed4接口边界，不生成新RTL：提供带tie/边界类别的S29→S25整数向量，Fraction独立求RNE，最大正值RNE溢出明确标拒绝而非饱和。后续TB必须逐握手比较payload和对应overflow、随机ready、尾拍、错误/停止同拍；本轮未执行这些RTL用例。Hann/activity S25及IFFT25待B明确配置再准备对应golden，不借原S24或portable结论。

复跑（仓库根；输出目录不得存在）：

```powershell
$a='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918'
python -B "$a/prepare_production_delta.py" --out "$a/evidence/e-dispatch-20260921-run02"
```

本轮实际证据 `evidence/e-dispatch-20260921-run01/`：退出0，145个待测整数向量、8个手算期待锚点、16余数类别、16服务身份核对。脚本只做来源/域/覆盖/准备检查，输出标为PREPARATION_ONLY_NOT_RTL_NOT_BOARD。原33/122/30项、FFT、耐久未重跑。

## 5. 声学交C的技术边界

只沿 `batches/positioned-single-source-01` 继续，不重录八段。现有S1 ELF本机上轮核对仍为4b7823bd…，但旧preflight因timerfixed check_entry.py依赖哈希改变失败。必须核对该检查器新旧批准范围及当前加载绑定后才准许Run，不能凭ELF同名/版本串绕过。未改变检查器、采集程序或接线。

C应在完整交付中提供：实际mic编号；尺/卷尺及最小刻度；阵列和手机固定方式；相对中心实际x/y/z、重复读数、朝向及现场照片；播放器应用及当前设置。现有手机15Pro/85%/关可见音效仅旧事实。当前WAIT_C_DELIVERY，未取得新录音，不要求拓芙代采或整理。C若不能访问当前获批设备/入口，集中回报缺项；检查器绑定问题不能通过改哈希/工程绕过。E未抢写C采集目录。

生产工程状态：WAIT_PROFILE_CONFIRMATION；在前提满足后才进入WAIT_USER_ENGINEERING_CHOICE。没有请求拓芙现在改one/Vitis或重新Build。整体REALTIME_BLOCKED、完整H3未通过。本页交工作执行协调B集中回复，未声称跨任务已送达。
