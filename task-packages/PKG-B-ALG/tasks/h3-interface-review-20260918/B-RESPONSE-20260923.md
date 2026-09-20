# B 对 A 接口裁决意见的集中回复

实际整理日期：2026-09-20；20260923 是检查点名称。状态：B 单方技术回复，供 A 确认及工作执行汇总；不是双方冻结、实现 PASS 或 H3 批准。本轮仅文档与静态证据整理。

## 输入身份与阅读入口

- main：`1f369dc688cc1e49d5b2b51735bce7dc9d1cfb78`。
- B 接口：`28d5c775f15f29cbe1039e8ce60cc4498bb257b7`，本包 INTERFACE.md、NUMERIC.md、SCHEDULE.md 与 references.json。
- A BRAM：`e4f9eae3fe7e4104ff8a6827937e326954f90a82`，`task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/frame-adapter-bram-candidate-01/` 内 RTL/model。
- A 两份原文见本包 `inputs/a-working-20260923/`，由用户提供文件本体，逐字节复制；来源路径、SHA-256 及固定对象绑定见 `evidence/response-20260923-bindings.json`。它们是未提交工作材料，**没有新待审 SHA**。
- 本文引用 A-DECISIONS 的“集中意见”各行和 CONTINUE 的“一次集中裁决清单／数制与逐级比较／完整预算交付”。旧文档不改；以下新增建议须由 A 回答后才形成共同合同。

## 1. 输入、异常、丢弃及恢复

| A 原文意见 | B 裁决 | 理由及明确规则 |
|---|---|---|
| “维持8×LE32、uint64原ID、S24扩展int32” | 同意 | 冻结 H1 原件不动；48kHz、四路同一 ID，JSON 新增样点 ID 用十进制字符串，不能经过 float。 |
| clip：“保留raw_flags，同时使clip行产生上游错误” | 同意（独立适配方案）；现候选需调整 | clip 行本身丢弃、清重叠和未满窗口，下一无错误且连续的行才起 clean interval。H1 仍用 stream_error=1/unknown；新增逻辑原因 CLIP 及 clip_mask 保留，不能把 unknown 改写为历史文件中的新码。低四位原样保存。未适配 BRAM 的 clip 反例必须留下。 |
| 缺号：“丢弃当前行、清have_prev，下一个合法行可重新起段” | 需调整 | 首个跳号的已接收行本身为 DROP，丢弃；不能补造缺失行。B 读取器仍将错误行的 ID 作为后续连续性基准。A 清 have_prev 后会漏掉下一次跳号，不能只用“下一合法行”笼统对齐。适配器需独立保留上一已接收 ID，窗口状态与 ID 检查状态分开。 |
| “重复/倒序是否整会话拒绝，而不是恢复” | 同意拒绝；实时实现待定 | 现 B 离线读取器拒绝整份输入，包括重复、倒序、uint64 回绕。建议运行时立即 fail-stop 当前 session，禁止丢一行后继续；所有未提交结果失效，清 HOLD/TTL，只能显式新 session 恢复。此前已提交结果无法物理撤回，应另报 session fault，不能宣称运行时与离线整文件拒绝完全等价。 |
| “连续错误……须逐样本比较” | 同意；interval 映射需调整 | 每个错误行都保存原始事件并丢弃，且参与 ID 连续性检查。连续错误不生成空 clean interval。A 当前每错误行递增 interval_index，B clean interval 是非空段；保留 A raw_interval_index，外围映射为逻辑 interval_id，不伪造计数相同。 |
| “多故障优先级/原因集合” | 需调整；数字 ABI 待定 | A 现码 STOP=1、UPSTREAM=2、ID=3、FLAGS=4、RANGE=5 原样保留。单一码不能替代完整原因集合；新增逻辑 reason 集合见下，不复用未商定的位号。 |

建议逻辑原因字符串：CLIP、DROP、ID_DUPLICATE、ID_REVERSE、ID_WRAP、UPSTREAM_ERROR、INVALID_FLAGS、INVALID_RESERVED、PCM_RANGE、QUEUE_OVERFLOW、STOP、RESET、LATE_STATUS_ERROR、RESULT_EXPIRED。此表是草案字典，不是硬件枚举冻结。

恢复裁决先看**完整原因集合**：ID 重复/倒序/回绕、非法格式/范围、上游完整性错误、队列溢出视为 session 致命；单独 clip/drop 可切段恢复。诊断主原因建议顺序：UPSTREAM_ERROR/QUEUE_OVERFLOW → ID 类 → FLAGS/RESERVED → PCM_RANGE → CLIP；同类细分保持确定顺序并列出全部原因。即使主原因是 CLIP 或上游错误，也不能遮蔽伴随的致命 ID 错误。STOP/RESET 是控制事件，不覆盖原始故障原因。新增分类及优先级须 A 确认；当前 RTL 尚不具有这套完整行为。

逐样本预期例（ID:状态，初始均为新 session）：

- `100:clean,101:clip,102:clean`：丢 101；102 起新段，100 的尾部不足帧则仅记摘要。
- `100:clean,103:clean,104:clean`：103 标 DROP 并丢弃；104 起新段。
- `100:clean,103:clip,105:clean,106:clean`：103 同时 DROP/CLIP，105 仍为 DROP；106 起新段。A 清前序 ID 的现候选会出现差异。
- `100:clean,101:clip,102:clip,103:clean`：两条错误事件，只有 103 才开启下一非空段。
- `100:clean,100:clean` 或 `100:clip,99:clean`：离线拒绝；运行时建议 session fault，不恢复成正常帧。
- 最后一条跳号行仍丢弃；没有下一 clean 行就不创建新段。没有外部预期终点时，不能从 EOF 推断尚未收到的“末尾缺号”。stop/restart 即使 ID 相邻也不跨 session 拼帧。

以上是对照用期望，**本轮未运行差异测试**，不能作为测试结果。

## 2. 身份、提交、停止与 TTL

| A 意见 | B 裁决 | 明确边界 |
|---|---|---|
| N1024/H512、跨250组包界、不加窗/补尾 | 同意 | 分帧器不加窗；Hann 属后续算法。FFT TLAST 在第1024个 accepted 样点，不用 DMA 包尾。 |
| 描述符外围携带缺失字段 | 同意方案；实际 ABI 待定 | session_id 为外部唯一字符串；A 32位 session 仅本次运行的映射键。逻辑 frame_id 在 session 内递增；interval_id 为非空 clean 段编号，另留 raw_interval_index。frame/interval 与样点 ID 是不同量。 |
| row_start/stop、config/geometry/profile | 同意新增逻辑字段 | row_start 为 session 输入记录序号（从0计，包含已接收错误行、不包含未收到的虚构行），row_stop 为右开端点；正常帧差值1024。first/last_sample_id 是包含端点的原 ID。config_id、geometry_id、numeric_profile_id 各绑定版本和内容哈希，并带 channel_order/N/H/Fs；声源标签另存，不冒充采集配置或几何真值。 |
| “计数溢出策略” | 同意不得回绕；实现待定 | 任一有限位宽身份将溢出前停止接收并报错，显式开启新唯一 session；映射表不得在旧事务仍在途时复用。原 uint64 样点回绕仍拒绝。 |
| “先做离线文件/已验证DDR记录的可背压重放” | 同意 | 生产桥、CDC、音频设备均未选择；不能把 S1 有限归档当环形队列，不新增跨域线。 |
| RX复制完才FREE、独立帧生命周期 | 同意；容量待定 | 不持有 FREE 槽指针、不覆写消费者；队列容量、最长服务时间、溢出检测和显式重启由 A 交付内存合同。未确定前不分配 DDR 地址。 |
| “WAIT_STATUS后原子提交” | 同意逻辑提案；实现待定 | 数据/数量/TLAST/overflow/status 全齐且身份仍有效才 COMMITTED，一帧至多一次；VALID 计算结果不自动成为正式 direction_accepted。 |
| “同拍故障/停止/提交优先级” | 同意需明确；采用本段建议待 A 确认 | RESET/STOP/session致命故障优先于帧错误，帧错误优先于提交；同拍禁止提交。全部原因保留。先执行失效，再允许下一事务，不能以先输出后补错等价替代。 |

stop 可以保留原尾数据用于诊断，但停止识别后未提交结果均 INVALID，清跟踪/重叠/TTL；“排空”不授权继续发布 fresh。clip/drop 切段时清旧状态，并保守作废当时未提交事务；旧已提交结果保留审计记录但不再供 HOLD 使用。

晚到错误必须带事务身份；提交前到达则 INVALID。提交后才到达说明完成判定合同破坏：记录追溯故障、撤销后续消费资格并 fail-stop，不能改旧日志伪装从未发布。没有 status 完成上界就不能声称 WAIT_STATUS 能给出有限延迟。

TTL 使用同 session 原样点轴：建议 `valid_through_sample = last_sample_id + ttl_samples`，ttl_samples 来自 config，不在本文冻结数值；到达/消费样点超过此值即 RESULT_EXPIRED，等于仍有效。迟到结果不得从 available_sample 重新续期；HOLD 不延长原有效期，另受 HOLD 上限。session/interval 结束清 TTL；加法溢出拒绝。available_sample 无可信映射时填 null，不能据此宣称实时有效。fresh、HOLD、INVALID、target_presence=unknown 分开；当前研究方向不自动解锁正式 accepted。

## 3. 固定右移4候选与 PHAT 单位

对 A“固定RNE右移4→S25，作为独立软件候选”裁决：**同意**。四路使用同一固定 shift=4；不引入四路自适应公共指数，不替换 reference25，不冻结生产数制。

- 输入 S24F23；Hann U18F17，乘积 RNE>>17 回 S24，任何饱和记录且禁止正常结果。portable 前向输入左移4为 S29F27，10级每级 /2，总 /1024；输出 RNE>>4 得 S25F23。S25 最大正码附近可能舍入越界，必须检查饱和/overflow，不能只截位。
- 未饱和时每个实/虚分量最大误差0.5个 S25码，即实值 2^-24；|q29|≤8 会 RNE 到0。弱信号相对误差无有限保证，零化会改变 mask、有效 bin 数和拒绝行为；不能用强信号逐码结果推导弱信号通过。
- 互谱按 S51F46 保守容器，平方模用 U102。频带 bin7..85（79个）；相对幅值阈值1/50；整数判定为 `square>0 && 2500*square>=band_max_square`，每对至少12个有效 bin。阈值是互谱相对幅值，不是 PCM RMS；rms/peak 存在门也不是 PHAT epsilon。
- 当前 `phat-fixed-03/phat_model.py`：`EPSILON_CODES = 2^26/10^15 = 6.7108864e-8`，对应 `1e-15 × 2^-20 × 2^46`，单位是上述 FFT 缩放后的**互谱幅值码**。非零整数互谱模至少1，大于该 epsilon，零量由显式拒绝保护；不能把该常量直接当平方模阈值或输入 PCM 码。平方比较须使用平方单位。
- normalize 先对 `square << 48` 开方，幅值码在原互谱码基础上再带24位小数；归一化倒数 Q30、两次 Newton 更新，输出 PHAT S25F23。变量名 magnitude_q16 不改变实际 MAG_FRAC=24 的单位。
- 改 FFT 缩放、位宽或公共指数后必须重新传播互谱二次尺度和 epsilon，重新验证零/弱能量/阈值/舍入边界，不能仅改 profile 名称。

A 独立固定4边界检查、新 AMD 仿真、实板整链均 **NOT_RUN（本轮）**；本文同意候选路线，不授予实现通过。

## 4. Golden 必须分别绑定

对 A“portable Q30与AMD24位twiddle分别列结果，禁止互借逐码PASS”：**同意**。

| 路线 | 准确来源与 golden | 可引用范围 |
|---|---|---|
| portable Q30 | 提交 `7a17edd2b5408e10608d954f3e7fa11cb62fe34b`，B `tasks/h3-complete-20260918/source/fixed_golden.py`、config.json、`evidence/run05/golden/golden-stages.npz`、golden-summary.json、`evidence/run05/golden-check.json`；完整路径/哈希见 bindings | 该 portable 软件配置与 run05 输入的整数比较；不是 AMD 核 golden。 |
| AMD 29位/24位twiddle | 原提交 `c0b5f8fb44643e81d8c4e6f0be457dddeae9758e` 的 A `tasks/fft29-bitexact-budget-01/` configuration.json、`evidence/run01/vectors/expected.npy`、selection.json；补充覆盖以固定 main `1f369dc...` 下 `coverage-extension-01/evidence/run01/` 的 vectors/expected.npy、selection.json、artifact-sha256.json、check.json 绑定 | 原60帧和扩展136帧分别引用，合计196帧六路前向历史覆盖；不表示本次四路固定4→PHAT→IFFT全链逐码通过。 |

AMD 与 portable 相同输入可作差异研究，但结果各用各的 expected 和完整配置、输入选择记录。当前没有可借用的 AMD 四路后级完整 golden PASS。25位逆向需绑定其独立配置与逆向参考；旧 FFT 候选 `ac0ff38e954dac094fd84e28b329dcb24dded7fb` 的槽延迟不等于整链逆向验证。

29位前向、25位逆向不能运行时切换同一 IP 数据位宽。双核或统一位宽的选择**待定**：双核需资源/调度证据，统一位宽需重新验证缩放、阈值、向量与预算，不沿用异宽逐码结论。

## 5. 提供 A 工程预算的算法输入

对 A“未知填null；73900仅旧FFT/IFFT槽”：**同意**。下表是现软件逻辑操作量，不是综合后资源/II；所有未证周期上界均 null。

| 环节 | 每帧/每hop操作量与依赖 | 周期上界/依据 |
|---|---|---|
| Hann | 每帧4×1024=4096次实乘及RNE/范围检查；分帧后进行 | null |
| 前向FFT | 4次1024点；理论 radix2 各5120蝶形，不等于IP执行单元数 | 历史槽每次7366；本次完整服务上界null |
| 29→25 | 半谱4×513×2=4104个实分量RNE/范围检查；若适配全谱则8192，布局待选 | null |
| 互谱 | 6×513=3078复数乘，共12312实乘、6156加减；四路谱及status齐后开始 | null |
| mask/PHAT | 当前软件3078个平方模（6156平方及3078加法）；6个79-bin最大值扫描/阈值筛选；最多474个归一化，每个开方、倒数查表、两次Newton共4乘及实虚输出缩放乘法 | null；开方/宽乘实现、II、拒绝分支待A选型 |
| 补共轭/IFFT | 最多6次1024点IFFT；共轭/端点及索引检查，S25F23十级各/2，不再额外/1024 | 历史槽每次7406；本次服务上界null |
| lag/插值 | 物理范围搜索4×13+2×17=86个点；最多6次插值除法，lag S18F12 | null；必须等待对应相关结果与status |
| DOA/置信度/跟踪 | 最多6对时延进入几何求解、残差/有效对判断、角度及状态机；退化矩阵、拒绝路径均需计入 | null；实现迭代次数/最坏分支尚未确定 |
| DAS/饱和 | 每hop每束4×512=2048次通道插值及累加/饱和；方向切换双束交叉淡化不能仅预算一束 | null；旧/新束复用方案及音频工作集待定 |
| 复制/配置/status | 原记录校验、独立缓冲复制、事务配置和状态收集；不持有已释放RX | null |
| CDC/队列/背压 | 生产桥未选；队列容量、仲裁和最长ready低时间未知 | null；无界等待使total无有限WCET |

100MHz/48kHz/hop512：每 hop 严格整数限额1066666；4×7366+6×7406=73900周期，仅历史变换槽算术0.739ms。992766差值**不是已证明余量**。总时间还含 window、适配、PHAT、lag、DOA、DAS、copy、config/status、stall、CDC；共享乘法器、RAM端口和总线须建立依赖调度。`total=null / REALTIME_BLOCKED`。

现有延迟依据仅作分项引用：帧收集21.333ms、hop10.667ms、5帧稳定捕获最早64ms均不含处理；8样点音频可用延迟是假设，10ms淡变和200ms HOLD 是策略；BRAM 1027周期暂停仅持续ready的历史观测，不是消费者最坏服务上界。

缓存沿用 SCHEDULE 91080B逻辑清单：PCM双帧32768、Hann4096、四路半谱16416、单对PHAT4104、IFFT8192、相关4096、音频历史160、mono双hop4096、DMA两槽16128、描述符预留1024。**分配者/物理DDR或BRAM/复用/最大积压均待A内存合同**，不得与 BRAM 候选或 IP 内部 RAM 盲加。生产至消费完成才释放；四路谱保留到六对使用完，单对逆变换缓冲在 lag 复制完后复用。S1 的9600128B有限归档不作为持续环形容量。

带宽分项：原记录1536000B/s；int32 PCM768000B/s；packed24 PCM576000B/s；若每帧重读四路窗口为1536000B/s；若10次变换均以32位实虚槽落存并各读写一次为15360000B/s；mono int32为192000B/s。这些是条件化流量，不是总DDR或峰值带宽证明，缓存复用和总线争用仍待定。

## 下一步与交工作执行

1. A 依据本文对恢复/原因集合、描述符映射、TTL/同拍优先级给出一次确认；保持原 BRAM 反例，不改 B golden 消除差异。
2. A 运行新增独立分帧差异测试、固定4边界检查并整理调度/缓存预算；软件整数、AMD仿真、实板三列分别报告，未测写 NOT_RUN。
3. B 后续只针对新稳定子包独立复核。本轮不重跑八段/run05/S1/计时/FFT/耐久，不追加录音、不修改 one/生产算法。

给“拓芙工作执行”的回报：B 集中回复入口为本文件；仅新增回复、A工作材料原样快照、静态来源哈希/检查记录，并保留旧包清单后重新封存当前文件集合。原算法/阈值/接口实现、A/C源件和历史证据未改。请统一检查后发布准确待审 SHA；当前未提交、未推送、未合入，不能把 B 基线 SHA 当新回复 SHA。当前环境无跨任务发送工具，本文是待用户转交的回报，不声明已经送达。
