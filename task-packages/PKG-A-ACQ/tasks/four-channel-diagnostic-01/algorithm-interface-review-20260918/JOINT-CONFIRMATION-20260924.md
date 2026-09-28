# #14 联合确认提案与 #18 实际链接口准备

版本：`a-b-production-confirmation-draft-0.1`。作者 A；复核 B。
状态：`WAIT_B_CONFIRMATION`，`production_frozen=false`，`REALTIME_BLOCKED`。
本文件把已发布准备和 B 意见放在同一确认入口，不修改旧合同、参数、向量或批准记录。

## 准确来源和本次核验

- A 准备：`7274df873d6a36da8e16ca54f05688d3c7f09689`，本目录 `E-HANDOFF-20260921.md`、`E-CONTINUE-20260921.md`、`E-PREPARATION-SHA256.json`。
- 已批准候选依据：`f08556d01821d6c3c8204fdac2c38f53b2107c05` 的 `PRODUCTION-CONTRACT-20260921.md`（`a-production-decision-draft-0.1`）和 `service-budget-20260921.json`。A7274 中这两个文件与该版本逐字节相同。
- B 对照：`696d21000adfb1b39332bb35c1ae7b45d2b75227` 的 `task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/engineering-closeout-20260921/E-PREP-HANDOFF-20260921.md`。
- B 原意见：`3c04a8c221a3808846e749c8814ad22a85e8e13d` 的 `task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/delay-consistency-01/DISPATCH-20260921-B.md`。此文件不在 696d210 树内，不能用错误版本链接。
- 本次读取准确 Git 对象：12 个清单条目全部匹配，加清单自身共13份原件；145向量、16余数类、10个tie和8个overflow项可读。原结果记录8个手算锚点。只做完整性/内容核对，未重跑生成器，`PREPARATION_ONLY_NOT_RTL_NOT_BOARD`。
- 本次直接远端核实 A7274、B696d、main `7f26cf115b1b57ddede67439921b562274667fd6`。历史“未取得原件”只描述当时观察，本次原件可访问不等于 B 已接收或批准。

## 一次联合确认表

各行均为候选方向，B 应在 #14/本 PR 绑定受审准确 SHA，逐项回复“同意及来源”或具体调整；任何新参数均需明确版本。没有回复的行保持待确认。A 负责运输/集成部分，不能代签 B 的算法判断。

| 项目 | 候选方向 | 尚须确认及实现绑定 |
| --- | --- | --- |
| numeric profile | 四路、N1024/H512；reference25 保留；config/geometry/numeric 各32B不可变身份 | 新 profile_id/version/hash、规范化字段/单位/排序/schema、几何通道与activity/calibration依赖全集。A起草身份绑定，B确认算法字段 |
| fixed4 / S25 | FFT29到S25固定RNE右移4、越界拒绝；DOA S24窗和去均值activity S25窗分域 | 是否最终选择fixed4；输入缩放/弱信号界、Hann ROM和均值中间位宽、新S25 gate域golden。145向量是待测输入；旧FFT196帧不能无条件覆盖新增S25 gate域，核对覆盖差集后只补差异向量 |
| PHAT / IFFT | epsilon按互谱幅度码；portable Q30与AMD24 golden分列；25位逆核、十级各/2为候选 | B确认是否保留ad30bda候选band7..85、square>0且2500*square>=max_band_square、至少12bin、epsilon=2^26/10^15（互谱幅度码）、mag_frac24/倒数F30；绑定XCI/wrapper/twiddle/ROM及golden hash。后级AMD逐码未测，不能把epsilon写0或复用portable逐码期待 |
| S23 / S28 | 拒绝前xy S23F20；共同精确左移的归一化CORDIC S28候选 | 是否采用ad30bda的engineering-closeout-20260921/repair-r1-r2/cordic-profile.json中cordic-s23-normalized24-canonical-q8-v1及24步、S28 xy/S26 angle、S18F8输出、[-180,180)、RNE；绑定源码/profile/golden，补除法/进位中间宽度。有限向量不证明全域误差 |
| DAS8 / 17 | 268e526动态DAS：8前视/17历史、2beam+最新pending、480淡变；旧9前视另列 | 两bank/ring/cache生存期、输出RNE/overflow、pending覆盖和有界背压；被覆盖请求不保证执行，实际持续输出未证 |
| source / emit / TTL | source=emit-8；仅真EOF补尾，gap/reset不补零；停顿不暂停TTL；HOLD不续期 | ready/expiry/available/commit每个字段时基、显式+8转换、采样时钟锚、TTL值/单位/溢出拒绝；夹具TTL=512不成为生产默认 |
| required_status | all_required_status_visible_at <= available <= commit_now；commit/take双查身份和TTL | A提议transport、frame-domain、window、FFT config/data/status、fixed4、gate、PHAT、IFFT、lag/DOA、tracker、binding；B确认算法全集及合法SKIPPED原因，A补运输错误合并，映射16服务。暂不冻结bitmask，夹具status=3不复用为生产全集 |
| 所有权 / 缓存 | RX完成及cache/状态核对→成功复制入算法自有环→释放RX；借用帧不得覆盖；结果/审计各自释放 | B确定最后一次算法读取及全部结果状态闭合事件；A绑定DMA/CPU转换、cache属性/屏障、ISR队列/单worker、token回调退役和session/generation映射 |
| STOP / 恢复 | smooth_stop最长960样点回mono；fatal/session_abort撤销未消费结果并排空运输 | cancel/abort/timeout/drain完成条件、晚错追溯及reset世代隔离。平滑STOP不能代替硬停，已输出音频不能回滚 |

本提案不产生新寄存器地址、bitmask、默认数值profile或最终生产ABI；未决项不是实现者可自行猜填的空白。

## #18 实际链和16服务测量入口

下一工程阶段目标：把已批准模块和联合确认后的合同接到准确生产版本，取得实际ARM/PL服务、状态、内存、争用与背压证据。范围及操作由拓芙选择原工程或副本后执行；本次不修改/构建/下载实际one或Vitis。

可独立推进的是合同/事件映射、受影响域的TB与仿真准备；实际工程编辑、构建、下载和16服务实测须等接口冻结、模块准入及拓芙的工程选择，不据此阻止准备成果先交审。

预期事件链：DMA完成→ISR事件队列→单worker核对cache/状态→复制并释放RX→借用帧→数值服务→必需状态闭合→commit/take双查。此顺序不是完整MMIO/IRQ/DMA合同；实际地址、对齐、缓存行、边界、状态清除/并发和abort语义须随选定工程绑定。现有S2MM不能推定为算法MM2S路径。

16服务仍以本目录 `service-budget-20260921.json` 为唯一预算源；测点、条件和停止要求复用 `E-CONTINUE-20260921.md` 第3节。以下是实施/采证缺项，不是已测耗时：

| 服务ID | 要补的实际依据 |
| --- | --- |
| capture_dma_cache_copy | 完成→invalidate/guard→复制结束；CPU/DDR/cache争用与环满fail-stop |
| accepted_row_frame | ARM ELF/map、跨包/滑窗/双槽HELD时间及消费者持有等待 |
| mean_two_windows | 均值/S24/S25实现、ROM/乘法器端口、启动与II |
| fft8 | 8次config握手到末status，真实ready停顿 |
| fixed4 | RTL payload/overflow与背压；8208运算量不能代上界 |
| gate_power_state | 部署位置、宽除法、阈值附近及跨帧状态路径 |
| cross_mask_phat | sqrt/Newton/除法、迭代上限、共享资源等待 |
| conjugate_ifft6 | IFFT25 XCI、6事务status、共轭守卫及FFT资源共享 |
| lag | 搜索、插值/margin除法和RAM争用 |
| doa_cordic_tracker | A9/PL映射、归一化/24步/除法及HOLD/fresh/拒绝分支 |
| rom_control | 到达上界、cache miss到两bank更新；552960B仅净载荷 |
| das_two_beams | 17行ring端口、两bank切换、pending覆盖及连续输出 |
| config_status_commit | ISR批大小、屏障、14变换及后级状态闭合到commit/take |
| arbitration_cdc_reset | 61.44MHz/拟100MHz边界、FIFO/reset generation、仲裁有限等待 |
| output_backpressure | 实际介质、到达包络、最低服务率和最大blackout |
| audit_drain | 64条审计队列的生产突发、消费/ack上界和满队保留故障 |

每项证据须绑定源码/配置SHA、ELF/map或XCI/DCP、工具和实际频率，保存请求、首次接收、末payload、末必需status时刻；分开启动、II、服务时间和等待。观测最大值不是WCET。16项 cycles_per_hop、ARM布局、系统峰值、queue burst/blackout/minimum-service 保持null。旧103364周期槽不能替代实际上界；不同旧内存模型不能相加。

工程执行按一整阶段交接：先完成生产profile/状态与输入身份确认，选定已批准模块范围；再由拓芙在选定工程接线/配置/构建并保存配套产物；最后按上述测点采证和运行受影响测试，由B复核准确组合。缺项保持REALTIME_BLOCKED，不把本测量方案当实测。

## 本轮范围、验证与交接

- 复用 f08556d、ca512a8、ad30bda、268e526 的限定证据，未重跑旧33/122/30项、FFT或耐久。
- 当前没有RTL/AMD新域逐码、ARM构建/cache/DMA、CDC/STA、生产板测或系统实时通过。
- 后续只补受影响域：fixed4逐握手/overflow、S25窗、AMD25 IFFT、晚状态/TTL边界、旧世代回调、reset/取消/背压及所有权。
- C负责正确素材的新八段全流程；A仅入口支持和接收，B独立诊断，不要求拓芙代采。
- 本准备可先交B审；批准准备范围不等于最终profile冻结或#18完成，不使用自动关闭Issue的合并关键字。
