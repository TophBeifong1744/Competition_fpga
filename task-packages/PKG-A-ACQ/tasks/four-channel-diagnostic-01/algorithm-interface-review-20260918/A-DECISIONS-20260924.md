# #14 A侧合同决策增量：身份、数值、状态与时间

版本：`a-production-contract-candidate-0.2`；作者A，非作者复核B。状态：`PROPOSED_BY_A / WAIT_B_CONFIRMATION`，`production_frozen=false`，`REALTIME_BLOCKED`。

本稿把候选设计选择具体化，供B按D14编号集中确认；不把设计决定当作实现或测试通过。PR #30 对 `c4a2a173eb48383a30d3bfc3138e0ee14a25b4d4` 的批准仅覆盖原准备稿，本增量不继承该批准。默认reference25、旧profile/golden、采集固件、实际one/Vitis及历史证据均不改。

## 1. 准确来源与适用顺序

| 引用 | 准确提交 | 受控入口（仓库相对路径） |
| --- | --- | --- |
| S0 当前V1范围 | `28d58e908525d1de1c018eeb99fd607a07b6047c` | `document/project-plan.md`、`document/project-identity.md` |
| S1 本次原提案 | `c4a2a173eb48383a30d3bfc3138e0ee14a25b4d4` | 本目录 `JOINT-CONFIRMATION-20260924.md`、`E-CONTINUE-20260921.md`、`E-PREPARATION-SHA256.json` |
| S2 旧A合同与预算 | `f08556d01821d6c3c8204fdac2c38f53b2107c05` | 本目录 `PRODUCTION-CONTRACT-20260921.md`、`service-budget-20260921.json` |
| S3 C桥软件语义 | `ca512a8be7978ab6ca2ade3d5e0b922e53a89c79` | 本目录 `ps-semantic-bridge-candidate-01/CONTRACT.md`、`src/ps_bridge.h`、`src/ps_bridge.c` |
| S4 B工程语义 | `ad30bda694abc946db045192385ebdf1b8e1a956` | `task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/engineering-closeout-20260921/CONTRACT.md`、`FLOW.md`、`repair-r1-r2/cordic-profile.json` |
| S5 动态DAS | `268e52627d091b8909890b43586c70564563132e` | `task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/dynamic-das-20260921/README.md`、`dynamic_das.py` |
| S6 B原候选意见 | `3c04a8c221a3808846e749c8814ad22a85e8e13d` | `task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/delay-consistency-01/DISPATCH-20260921-B.md` 的合同表 |

以上SHA用于读取原件；同名工作树文件或历史摘要不替代来源。S6旧单段采录安排已被当前八段安排覆盖，本稿不重派录音。S4修复后合同优先于旧NUMERIC中的S22/9前视措辞；S2旧“ca512待审/d3d待修”不作为重新打开已关闭问题的依据。

## 2. D14-01：V1计算边界与最小数值路线

**A选择：四路固定RNE右移4作为本次独立生产候选路线；不引入四路公共自适应指数。** 理由是复用已明确的尺度与准备向量，避免同时新增指数屏障及阈值换算。它不是对弱信号性能的批准；若对应gate域或弱信号证据不满足，由B给反例后再改变候选版本，不能在实现中暗换路线。

S0要求PL实时GCC-PHAT/TDOA/二维DOA。S1中“doa_cordic_tracker：PS首选”仍是旧测量建议，本次不采纳为V1生产映射。候选中DOA/CORDIC数值核归PL；PS负责运输适配、配置、状态和日志。Tracker控制状态放置尚需结合真实服务预算确认，不能以主机模型已经运行来承诺A9或PL实时。实际资源不满足时由M提出有证据的架构调整，不私自改变V1判据。

| 节点 | 本次选定的候选合同 | 保留的实现/证据缺项 |
| --- | --- | --- |
| 输入/窗 | H1原8×LE32不变，S24原码；N1024/H512；DOA原窗后S24与去均值activity窗后S25分域，加窗各一次 | Hann ROM逐字节绑定、均值/乘积/RNE宽度；S25 gate域不能借旧S24全域批准 |
| FFT与fixed4 | 两域各4次FFT29；窗码精确左移4，十级各右移1；输出固定RNE右移4到S25，越界产生INVALID，不输出截断/饱和值作为有效数据 | 145项仅准备输入；实际握手、payload/overflow和新增输入域逐码尚未验证 |
| PHAT | 六对顺序01/02/03/12/13/23；S51F46互谱、U102F92平方和；band 7..85；square>0且2500×square≥max_band_square，至少12bin；epsilon精确为2^26/10^15互谱幅度码；mag_frac24、倒数F30 | 开方/两轮Newton/除法的实现、临时位宽及golden绑定；epsilon不能置0或混成平方码/PCM码 |
| IFFT | 独立25位逆核候选，十级各/2，不再除1024；DC/Nyquist及最小负码共轭保护 | 实际XCI/wrapper及AMD逐码/status；禁止运行时把29位核切成25位 |
| lag/DOA | lag S18F12；拒绝前xy S23F20；采用S4独立CORDIC profile `cordic-s23-normalized24-canonical-q8-v1`，24步、xy S28、角累计S26、S18F8输出[-180,180) | 归一化取绝对值/左移、除法余数翻倍/进位需实现宽度；有限向量误差不升级全域定理 |
| DAS | S5的8前视/17历史、2beam+最新pending、480点淡变；稳定请求最多等待480再淡变480，被覆盖pending不保证执行 | 连续PCM吞吐、bank/ring寿命和有限背压尚未实现；合法凸组合输出的S24范围不授权静默饱和 |
| ROM | 固定S5几何/声速/采样率时优先PS DDR只读驻留，552960B仅净载荷；每会话绑定ROM字节身份 | 几何不同时禁止复用原ROM；ARM地址、cache、带宽和系统峰值未知；不默认把完整ROM塞PL |

**两个配置域分开命名：** PHAT的band 7..85不覆盖activity的band。S4树中的 `checkpoint-20260923/config.json` 是开发候选，activity band为7..72，且包括开发集/显示增益等字段；不能整份复制为生产配置。Activity阈值、标定参考、Tracker策略和TTL必须有B确认的独立对象。9/22新背景参考不自动成为生产默认。

## 3. D14-02：三份身份的候选生成规则

本节是新规范建议，尚无生成器或生产hash；不得填造hash。保留现C桥config/geometry/numeric各32B且非零的边界，不改现ABI布局。

1. 规范对象使用固定schema/version、ASCII字段名；拒绝重复键、未知字段和浮点数。身份/计数/定点码用规范十进制字符串（无前导+、无多余0，零仅`0`）；有理数用约分的`numerator/denominator`对象，分母为正。枚举和哈希用规定的小写字符串，逻辑标志才用bool。数组次序按合同，不能自动排序通道或pair。
2. 对象键递归按ASCII字典序；UTF-8、无BOM、无空白、无末尾换行的JSON字节为canonical payload；字符串值限定ASCII以避免Unicode归一化分歧。SHA-256输入为`SoundSight/<kind>/v1\n`的UTF-8字节与payload直接拼接，kind只能是config/geometry/numeric。输出32B；JSON展示为64位小写十六进制。域前缀中的`\n`是单个LF字节。
3. `geometry`包含channel→mic映射、坐标及单位、参考mic、坐标轴/角度方向、声速和几何适用范围；实际不确定性以独立现场证据引用，不把40mm模型写成精密实测。
4. `numeric`包含D14-01各节点格式/缩放/舍入/非法域、pair顺序、ROM和算法参考字节身份、**twiddle_backend**及对应golden身份。portable-q30与amd24是不同numeric对象；当前AMD绑定缺项时不生成“生产已完成”的numeric对象。共同profile名称不代表逐码相同。
5. `config`引用geometry/numeric摘要，并包含采集来源/采样配置、activity与calibration对象摘要、Tracker/TTL策略、完整required-units及skip规则、时基/身份映射合同版本。calibration数据的内容身份需纳入其对象，不能只写易变路径。三对象引用保持无环：geometry不引用config，numeric可引用geometry，config引用二者。
6. 实际XCI/wrapper/ELF、工具及构建字节身份另列实现绑定清单；该清单引用三份摘要和实际产物哈希。源码语义一致不证明构建或实际位精确结果一致。源码证据以固定Git提交/blob或其明确导出字节为准；可加载工件使用实物字节SHA-256，禁止静默把CRLF转换当同一工件。
7. 缺少必需字段的草案可保留null，但不得通过生产profile验证或下发。运行中配置不可变；任何有效字段变化必须新身份，并在停止/退役旧在途对象后的新session生效。

B需要一次确认的是算法字段全集与引用关系；E后续实现canonical生成/校验及缺项拒绝，不在本轮生成假默认。

## 4. D14-03：时基适配与TTL，不把8样点前视当处理延迟

保留三类不同坐标，字段必须显式携带域/单位和身份，禁止仅凭字段名为整数就混比：

| 域 | 现有语义 | 本次组合约束 |
| --- | --- | --- |
| 原始sample_id | H1的uint64原ID；C桥expiry=frame.last_id+ttl | 加法溢出拒绝；等于expiry仍有效，严格大于过期；C桥可信clock必须返回同域上界 |
| session物理采样计数 | B的status-visible/available/commit-now，实际时间不随ready等待停止 | A提供原ID与该计数的锚及有效区间；未知时不能换算或把available倒填帧尾，不用CPU打印时间替代 |
| DAS局部emit/source | S5每个连续interval的source=emit−8；启动source −8..−1有明示语义 | 原ID↔session时间↔interval局部索引分别记录映射；gap后重建局部映射、清历史，不能跨interval拼接；仅真EOF补尾 |

候选锚至少记录boot/session/interval、原ID原点、session计数原点、局部source原点、来源频率/观测点及有效性。区间内转换必须用检查溢出的整数差与加法；缺锚、回绕、非单调或不适用域均不得发布新有效结果。实际计数来源/延迟界仍未知，本稿不虚构数值。

**+8仅用于把S5接受的source域Tracker ready/valid_through映射到局部emit坐标。** 已在物理采样时基的status/available/commit-now及C桥原ID域expiry不得再加8。C桥结果领取须先按其真实时间上界通过TTL；领取后DAS控制另按其域验证有效性，不能用+8给已过期结果续命。两种有效期的组合与锚必须由同一适配合同明确，不直接拷贝一个`valid_through`字段。

C桥unknown clock时不提交，take返回WAIT；这是保留行为，不写成“unknown必fatal”。生产适配不得无期限等未知时钟且宣称实时：超时/停止策略必须在硬件时基及服务界已定后绑定，当前仍阻断。

`max(required_status_visible_at) ≤ available ≤ commit_now ≤ expiry`须在同一域成立；commit/take各按其调用时刻核验身份与TTL。结果available不是帧末ID；S4离线音频的`available=emit`不能直接套到有额外流水线/排队延迟的实物。实际present/consume时间另记录，ready停顿不冻结时钟。HOLD不更新方向或expiry。

## 5. D14-04：逐实例完成集合与有条件跳过

候选以**符号unit集合**定义，不分配生产bitmask或CSR地址。外部profile固定本帧expected-units，DUT不能在submit时自行缩减。每unit恰有一个最终结论，所有结论绑定boot/session/interval/frame、generation及三份身份；重复、漏项、错误身份不得算完成。

| 层 | 候选实例集合/闭合条件 |
| --- | --- |
| 输入 | transport、frame-domain、binding：运输无错、完整N/H及连续区间、身份一致；不能把DMA TLAST当FFT TLAST |
| 前端 | mean/gate-window0..3、doa-window0..3；gate_fft0..3、doa_fft0..3；fixed4_gate0..3、fixed4_doa0..3；gate-state |
| 六对后级 | phat_01/02/03/12/13/23、ifft0..5、lag_01/02/03/12/13/23；pair↔ifft映射固定 |
| 结果 | doa、tracker、result-binding；缺DOA资格时仍须给明示的拒绝/HOLD/unknown语义，不制造fresh |

每次FFT/IFFT的最终unit成功必须覆盖config接受、规定输出数量/顺序/index/TLAST以及最终status无错；不能仅把看到TLAST当作完整成功。内部可以流水重叠，逻辑依赖保持，以上表格不是要求全部串行。

基线分支先要求上述实例有最终结论；正常路径为OK。`SKIPPED`只能来自B确认的profile分支和原因映射，例如gate关闭或有效pair不足，其依赖必须已闭合，不能将运输/overflow/状态丢失改写成SKIPPED成功。未确认任何skip映射时不启用该优化；测试应拒绝缺unit、重复unit和自减expected集合。SKIPPED是否对结果形成合法HOLD/INVALID由明确策略决定，不等同该节点OK。

本集合是待B确认的新组合合同。S3当前uint32 OR-mask和不透明payload不能证明这些实例都已闭合，也不能检测每实例重复完成；夹具status=3不升级为生产集合。E需在适配层保留实例状态/时刻，再映射到已批准桥接原语，不能只扩几个bit就声称实现完毕。

## 6. D14-05：所有权、提交和STOP的组合边界

- RX：DMA完成→ISR仅排事件→单worker检查运输/cache/保护区→成功复制到算法自有环→释放RX。enqueue成功只是保存待处理数据，accepted-row语义在pump阶段；不在复制前释放或保留已FREE槽指针。
- 帧：借用到算法最后一次读取完成才释放；result_begin不等于读帧完成。结果描述符独立复制；结果、PCM和审计各有消费/释放事件。真实cache属性、屏障、地址和IRQ并发仍待工程绑定。
- 定位结果：依赖状态闭合→commit→take→DAS控制验证/采纳。**commit不等待消费该结果的DAS或审计ack**，以免成环。DAS持续输出、输出背压、审计排空独立计入系统服务预算；它们的故障仍可触发session fail-stop。
- 同批事件先预检/合并错误，再决定各结果提交；不是整个批次的数据库式全提交/全回滚。当前session已提交晚错须停止后续发布并撤销未消费结果；已发生物理输出不可回滚。旧session回调只拒绝/审计，不杀新session。
- token沿用(session,generation,slot)。session非零uint64严格递增，generation跨正常stop/reset/start保留递增，耗尽拒绝；对象重建还需boot映射与旧回调退役证明。不得截断外部字符串或清零generation假装新事务。
- 平滑audio_stop/SEARCH/TTL沿S5：不启动第三beam，最坏960样点回mono，淡出期间旧beam可仍有权重。fatal/session_abort为另一条撤销/运输停止路径，不能解释成20ms平滑等待；硬停完成必须有实际abort/drain及输出取消证据。

**I14-TOKEN-01（新组合差异，OPEN）：** S3文档泛称当前未知事务错误保守fail-stop，但其dispatch对`slot >= PSB_RESULTS`先归STALE并跳过。A本次选择的生产适配规则为：已可靠归属旧session的事件只审计；当前session的非法slot/未知generation或不可归属的畸形当前事件不得静默忽略，须拒绝并fail-stop。此规则尚未实现，B应确认影响及适用错误分类；后续E只修明确增量并补当前/旧session对照反例。不倒签S3已覆盖，不撤销其未受影响的限定批准，也不重开既有R1/R2。

## 7. D14-06：哪些待设计确认，哪些待实现/实测

| 类别 | 本轮结论 | 下一责任/交付 |
| --- | --- | --- |
| 候选选择 | fixed4、分域窗、独立twiddle/golden、S23/S28、8/17与两beam策略明确；核心DOA保留PL目标 | B按D14-01确认或给具体反例/替代版本 |
| 身份与组合合同 | D14-02～05给出规范生成、域转换、逐实例状态及所有权新建议 | B确认算法字段/状态分支/时间映射；A处理运输适配与I14-TOKEN-01 |
| 算法配置缺件 | activity/calibration/Tracker生产对象、TTL数值/单位/含义与golden绑定未齐 | B提供准确对象/来源；A不能从开发config或夹具512推定默认 |
| 实现缺件 | 新S25 gate域、AMD25逆核、各级内部宽度、状态适配、采样锚、ARM布局/cache、输出介质 | E在对应合同确认后提交实现/测试准确SHA；实际工程仍由拓芙选择并操作 |
| 实测缺件 | 16服务上界、争用/blackout/最低服务率、资源/STA与真实声学评价 | 沿#18/#17原入口补证；16项cycles_per_hop和系统峰值保持null，不以历史槽数替代 |

生产合同冻结要求必需设计字段及双方确认齐备；实物准入另要求实现与实测证据。不能要求先把全部16服务测完才写合同，也不能因合同获批就把未知周期填0。9/25评价阈值/留出身份仍由#17集中确认，PHAT内部常量不充当正式性能门槛。

## 8. B最小回执与E后续实施边界

B只需对本增量准确SHA按D14-01～06回复同意/具体调整/缺件及文件版本，另回复I14-TOKEN-01分类；引用未变批准，不重审FFT/耐久或重跑33/122/30项。一个准备稿APPROVED不自动填写这些确认。

首个E实施包建议是**固定4独立适配及验收**，前置为B确认D14-01对应域、输入/输出握手和状态绑定：复用145向量作输入，独立期望核对，覆盖正负tie、极限RNE溢出、随机ready、末拍、错误/停止同拍及状态晚到；不修改默认reference25、现有FFT IP、one/Vitis或旧golden。确定源码/TB路径、单写入方和锁定工程Skill后再派发；本稿不假定E已接单。身份/状态/时基适配是另一个完整组合包，不按每条命令拆单，也不在边界未确认时提前实现整条生产链。

本次实际工作仅来源/语义核对和合同增量；没有新的RTL、AMD、ARM、板测或声学结果。S1的145向量、S3/S4/S5既有证据按原范围引用，未重跑。A机现有未跟踪旧意见原件保留，不另建任务状态台账。
