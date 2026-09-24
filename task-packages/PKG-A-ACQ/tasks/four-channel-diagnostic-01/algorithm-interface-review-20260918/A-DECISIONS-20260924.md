# #14 A侧合同决策增量：身份、数值、状态与时间

版本：`a-production-contract-candidate-0.3`；作者A，非作者复核B。状态：`PROPOSED_BY_A / WAIT_B_CONFIRMATION`，`production_frozen=false`，`REALTIME_BLOCKED`。

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

按B对`ec5017d`的复核修订：旧规则没有规定字符串转义，不能唯一编码；同对象的`"A"`与`"\u0041"`不得直接各自hash。本节以[身份容器规范](IDENTITY-CONTAINER-20260924.md)及[可执行容器schema](identity-container-v1.schema.json)为唯一详细定义；本稿不再维护第二套字段表。

输入允许非canonical但合法的JSON文本，须拒绝重复键/非法字符和类型，先校验解析对象，再由唯一encoder生成canonical payload后hash。生产输出只允许canonical字节。引号和反斜线分别仅用JSON标准两字节转义，其他可打印ASCII原样输出（含斜线），控制字符与DEL固定小写`\u00xx`，不用短转义。数字码值仍为规范十进制字符串；有理数约分，分母正，零唯一为0/1且禁止负零。

三个kind的容器字段、精确类型、版本值、required/null/unknown规则及引用方向已列出。容器内部不放任意扩展字典；未齐的numeric/activity/calibration/Tracker/TTL/required-units算法对象通过具名schema与内容摘要引用，字段和准确原件仍由B确认。**容器schema通过不表示引用对象完整或生产准入**；缺外部schema/原件、图有环、参数不适用或双方未确认时不得生成可下发生产身份。草案可用null显式记缺件，但严格schema拒绝它。

numeric不再引用golden全文件哈希：golden验证绑定记录位于三个身份之外，由它引用numeric/config、输入与golden的准确字节摘要；numeric的算法源/ROM等上游引用不得反向引用自身或config。这是本轮消除hash环的明确选择，不通过忽略字段或修改旧golden解决。

保留现C桥三份32B非零摘要边界，不改变ABI布局。当前没有生产生成器、真实完整对象或可下发生产hash；机械反例/合成schema用例只验证本次规范的有限性质。

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

**I14-TOKEN-01（OPEN；原ID保留，文稿分类返修第1轮）：** 接受B更正，拆为以下三个范围，不能统称本轮新需求。

- **既有合同与实现差距，静态确认：** S2已明确当前未知error（含越界slot/未知代次/已释放对象）应fail-stop，S3 CONTRACT也要求当前未知错误保守停止；但S3 `src/ps_bridge.c:172`先把session不匹配或`slot >= PSB_RESULTS`合并归STALE并continue，跳过error处理。完整静态反例前提是active、未failed的当前session、审计有空位、单条slot=4（PSB_RESULTS=4）、error=true、batch无fatal/control。该路径记录STALE并REJECT而未置failed；审计溢出触发的旁路fault不能抵扣。**本轮未编译/运行该C反例，不称实测复现。**
- **新增组合要求，待确认：** 当前session无error的畸形事件也fail-stop，单独于既有error缺陷审查，不能混成原合同已批准范围。未来session、未知boot或无法归属的事件也不能仅因session不相等就当成已证实的旧回调；归属策略仍OPEN。
- **沿用保护：** 已可靠归属旧session的error只STALE/审计，不误杀当前session。对象重建/boot映射及旧回调退役必须给实际依据。

实际修复由A所有，在后续E实现/验收资产串行批次处理。本轮仅改分类，不改C源码。最小验证需覆盖当前/旧session、越界slot、未知generation/已释放对象error、与合法完成同批的两种顺序；核对failed、撤销、无新commit和take拒绝，不能只看返回码。无error策略独立列新增合同用例。原批准未覆盖此静态缺陷，不以旧PASS证明它；未受影响批准及既有R1/R2保留，不整体撤销或重开。

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

B已在[原PR复核评论](https://github.com/TophBeifong1744/Competition_fpga/pull/30#issuecomment-5810446729)接受D14-01、03～06的候选方向，未整体批准表中常量或生产配置。本轮只请B增量核查D14-02的编码/容器/引用定义及I14-TOKEN-01分类，并集中确认身份容器规范末表的具体算法对象/来源；已有方向意见直接沿用，不要求重审FFT/耐久或重跑33/122/30项。原准备稿APPROVED不扩大到本增量。

首个E实施包建议是**固定4独立适配及验收**，前置为B确认D14-01对应域、输入/输出握手和状态绑定：复用145向量作输入，独立期望核对，覆盖正负tie、极限RNE溢出、随机ready、末拍、错误/停止同拍及状态晚到；不修改默认reference25、现有FFT IP、one/Vitis或旧golden。确定源码/TB路径、单写入方和锁定工程Skill后再派发；本稿不假定E已接单。身份/状态/时基适配是另一个完整组合包，不按每条命令拆单，也不在边界未确认时提前实现整条生产链。

新增机械检查见 `identity-contract-checks-20260924/README.md` 与准确同版 `result.json`；只覆盖合成容器/编码有限探针，外部引用解析、完整关系与生产生成器未实现。

本次实际工作仅来源/语义核对、合同增量和机械探针；没有新的RTL、AMD、ARM、板测或声学结果。S1的145向量、S3/S4/S5既有证据按原范围引用，未重跑。A机现有未跟踪旧意见原件保留，不另建任务状态台账。
