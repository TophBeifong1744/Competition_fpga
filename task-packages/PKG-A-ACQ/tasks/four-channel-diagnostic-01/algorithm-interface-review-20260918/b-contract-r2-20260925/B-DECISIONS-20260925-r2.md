# #14 / PR #30：B 合同决定稿 r2

状态：B_DECISION_DRAFT_PENDING_INDEPENDENT_REVIEW_AND_A_CONFIRMATION。原问题 B14-R1-01/02 的第1轮文稿返修，作者标 FIXED_PENDING_REVIEW；r1及其NEEDS_FIX原件保留。这是 B 主流程形成的新候选合同，不是成员 APPROVED、双方生产冻结或实现通过。production_frozen=false；REALTIME_BLOCKED。

准确 A 候选：274a408cfb3cdc12844a136be296a41fd901c3a6。B 数值来源 S4=ad30bda694abc946db045192385ebdf1b8e1a956；动态 DAS S5=268e52627d091b8909890b43586c70564563132e；桥接来源 S3=ca512a8be7978ab6ca2ade3d5e0b922e53a89c79。集成参考 main=28d58e908525d1de1c018eeb99fd607a07b6047c；不切换或修改运行中的 a14cd0766d923f00428c42ff7dc5d2eb52db0e50 产品树。

24份 Git 原始对象的路径、blob、字节数和 SHA256 见 source-index.json（3baff634ed25082ce1c57238b0aee7a5d8616e1dc924bb9b665881878a912228）。它是来源索引，不是新的生产 numeric manifest。下述简称 BROOT=task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/，AROOT=task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/。

## B14-01 / D14-01：选定数值路线及适用域

选择独立 fixed4 路线，不引入四路公共自适应指数，不替换 reference25。建议新组合 profile 标识 soundsight-fixed4-dual-domain-candidate-v1；它尚无可下发 numeric hash，不能把名字当完整对象。保留核心 GCC-PHAT/TDOA/DOA/CORDIC 在 PL 的 V1 目标；PS 负责配置/运输/状态。Tracker 放置仍待 A 依据实际服务预算确认。

| 节点 | B 选择 | 来源及限制 |
|---|---|---|
| 输入/分帧 | 四路合法 S24 原码，H1 8×LE32；N=1024、H=512；同一连续 interval，不补缺号、不跨段。物理采样率配置为48000 Hz | S3 CONTRACT；采样率是配置适用条件，不是实测频率证明 |
| 双窗 | DOA 原码加一次 Hann；activity 先逐路 S34 精确求和、RNE(sum/1024) 得 S24 均值，S25 去均值，再加一次 Hann。两个窗结果不可共用 | S4 integer_gate.py、FG window_pcm；窗乘保守 S43，RNE >>17，DOA S24 / activity S25。禁止先把 S25 夹回 S24 |
| Hann | 1024×U18F17，同一冻结4096B little-endian U32 ROM | S4 BROOT/fixed-nodes-20260921/b1b3/run02/hann-u18f17.u32le，SHA256 51a05f855181f1774c3373c83085fd5a2792f5db932d66b1f3dc768e8ec6a2f2；不运行时重算 cos |
| FFT/fixed4 | 两域各4个 FFT29；窗码精确 <<4，十级各 RNE /2；半谱固定 RNE >>4 至 S25F23 | 两域独立编号；S25窗最宽输入仍须合法S29。新增gate域不继承旧196帧的全域结论；逐级overflow不得作为有效数据 |
| PHAT | 配对01/02/03/12/13/23；S51F46互谱、保守U102F92平方和；bins7..85（含端点）；square>0 且 2500×square>=max_band_square；至少12bin；epsilon=67108864/1000000000000000，单位为互谱幅度码；mag_frac=24、倒数F30，输出S25F23 | S4 phat_model.py。epsilon规范有理数须约分为2048/30517578125；不是零、平方码或PCM码。此band不决定activity band |
| IFFT | 独立25位逆核、十级各/2、不额外/1024；DC/Nyquist虚部必须0，内部半谱虚部最小负码不得直接共轭取负 | S4 guards.checked_conjugate；portable Q30 与 AMD24 twiddle 的身份/逐码期待分开 |
| lag/DOA | lag S18F12，插值delta限±2048、分母翻正后RNE、0分母delta=0、扫描平局先负lag；最终按固定几何物理界拒绝。至少3个合法pair且秩满，拒绝前xy S23F20 | S4 FG及工程合同；几何须为固定40mm方形、通道顺序(0,0),(1,0),(1,1),(0,1)、声速343m/s才可复用现推界。其他几何不得套旧码/ROM/界 |
| DOA数值资格 | 保留既有残差平方和 <= K×2048²，模平方介于104858²和1363149²（含边界）；margin仅诊断，不新增准入阈值 | S4 FG doa_q20；这是候选内部数值资格，不是实测方向正确或目标身份。K为有效pair数 |
| CORDIC | 使用独立 cordic-s23-normalized24-canonical-q8-v1；S23非零输入，共同精确左移至max幅值bit_length=24；24步、xy S28、角累加S26，RNE输出S18F8，规范到[-180,180) | S4 cordic_candidate.py / repair-r1-r2/cordic-profile.json。1215向量仅有限误差证据；旧FG atan2输出不得直接冒充该新profile |
| 动态DAS | S5 8前视/17历史、最多2beam+最新pending、480点淡变；稳定请求最多等480再淡变480；被覆盖pending不保证执行；平滑回mono最多960点 | S5 dynamic_das.py；与旧立即重定向语义不同。合法凸组合输出S24，溢出检测不能靠静默饱和消除 |
| ROM | 固定几何时使用S5已验证延迟表；优先PS DDR只读驻留，再下发已绑定延迟码 | .npy整文件553088B，SHA256 acb899401cf0f1b7d7c9685d52c04bcbf28b6f1454b386bde57310f23776fe86；净载荷552960B，两者不可混作同一字节身份。角[-46080,46080)，mic0隐含0，92160×3个LE S16F12；若转换裸ROM，另绑定转换及输出字节 |

上述是候选选择，不说明目前存在一条实现了全部选择的完整链。FG内旧CORDIC、饱和出口、DAS旧块模式需由新组合显式替换/守卫，不能只给旧文件重命名profile。

## B14-02：首个 fixed4 独立实现包的算法接口合同

这是不依赖活动阈值、TTL数值、真实录音标签的独立范围。A取得本稿复核与确认后，可按工程Skill确定RTL/TB路径、时钟/端口及延迟合同后派发；本稿不授权one/Vitis操作。

1. 输入逻辑事务身份至少区分session/interval/frame、gate或doa域、channel(0..3)及generation，配置身份固定。每事务只适配半谱bin0..512，513个复数，各分量为S29；全FFT的1024输出/index/TLAST/最终status仍须上游验证并排空，截取半谱不能提前宣称FFT完成。8事务共4104复数/8208分量是工作量，不是周期数。
2. 每分量数学结果 q=RNE(x/16)，正负tie均向偶数；合法域[-2^24,2^24-1]。x在[2^28-8,2^28-1]溢出；x=-2^28合法输出-2^24。举例8→0、24→2、-8→0、-24→-2。输入非法S29是输入合同错误，不截断。
3. 一个复数任一分量溢出，该复数numeric_valid=false、对应分量overflow位锁存，输出占位payload固定(0,0)；两者均合法才给实际q。它是新适配合同，旧软件返回饱和值加计数仅复用其舍入/overflow判据，不能比较或消费旧饱和payload为合法数据。A145向量中的output_s25=null意为无有效数值，不是线缆null。
4. ready/valid的物理传输有效与numeric_valid分开：未取消事务的每个语义接受输入产生且仅产生一个带相同身份/index的完成beat（包括数值失效占位），不能因overflow丢拍造成等待死锁；仅valid&&ready计物理传输。无取消时，输出背压期间整个payload/身份/index/overflow保持。取消是逐输入完成beat与保持规则的唯一此处例外，按下面B14-R1-01以事务终结代替未传输输出，不等待ready排空。事务累计overflow在最终状态保留，不能因后续合法分量清除。
5. fixed4最终完成须覆盖全部513个输出被接受和该事务汇总状态；端点/重复/丢bin/错身份/晚错不能被计数相等掩盖。后级可流水，但在同帧两域全部必需状态闭合前不能发布fresh结果。底层固定延迟/II/有限stall由A给具体实现合同，本稿不猜周期。
6. fatal/session_abort/受控reset优先于逻辑提交，按B14-R1-01/02产生事务终结并撤销旧generation在途结果。物理传输历史不回滚；下游在同一提交裁决点先应用取消身份，不能使用同边沿传输绕过撤销。平滑audio_stop不是数值块硬复位，停顿不冻结物理TTL。异步reset/跨域取消由A另绑定可靠观测、优先级及排空合同，不能仅靠本单时钟逻辑规则宣称通过。
7. 验证重用145准备输入，但期望须独立复核；增加复数两分量组合、两域/四路身份、513拍边界、随机ready、末拍背压、overflow和晚status、取消后旧generation回报。准确源码/ROM/TB哈希与首错日志绑定。无需重跑未变FFT196历史样本；新域FFT准入另批。

## B14-03 / D14-02：身份对象的边界

接受274a408的容器/规范编码/引用方向作为候选。numeric不得反向引用包含其自身hash的golden；下游validation-binding同时引用numeric/config、输入、期待输出、比较语义、backend和执行证据。旧golden原字节不改。

ss-numeric-algorithm-v1必须逐节点明确：节点/版本、输入输出shape和有符号位宽/F位/单位、缩放与RNE、饱和或拒绝、合法域、窗/ROM引用、变换长度/方向/级缩放/backend、PHAT整数比较与epsilon单位、pair顺序/几何适用域、lag平局和边界、LS资格、CORDIC独立profile、DAS插值/混合/启动/EOF/状态策略。不能只写一个“S25”或引用整份开发config。

ss-numeric-source-manifest-v1必须把每个数值节点映射到固定commit/path/blob/SHA256；ROM同时记录存储编码/形状/索引和字节摘要。源/ROM叶节点禁止反向引用numeric或config。source-index.json提供可核验来源，尚不声称依赖闭包齐备：portable Q30 FFT在FG中运行时生成twiddle，生产仍需冻结其实际table字节/顺序及生成环境；CORDIC atan表同理。AMD XCI/wrapper/实际twiddle/全部适用域golden由A给，缺件明确阻断，不能用portable向量替代AMD逐码。

FG run05 golden-stages.npz仅适用于原profile/原输入；不能整体绑定为本新双域+新CORDIC+动态DAS链的golden。新节点合成golden可以准备，完整组合golden另需固定全链配置。schema字段类型遵守现容器整数字符串/约分规则，算法外部schema具体机器定义仍待实施与复核，本稿不伪称已发布。

## B14-04：activity/calibration、Tracker 与 TTL 的决定

**当前不冻结生产activity/calibration或TTL数值。** 原因是两环境仍只有partial输入来源和开发观察，且实际时钟锚/服务等待未绑定。此处是明确暂缓的合同字段，不阻挡B14-02独立实现；也不能声称完整#14已完成。

activity：数值核候选沿S4，band7..72（含端点）与PHAT7..85分离，归一化功率RNE(2×sum(|X|²)×1024×2^34 / sum(Hann²))，U64输出。只把其公式作为候选；4/2功率比、3/3帧、最少3路和floor为旧研究配置，均不升级生产默认。新schema必须有band/功率单位和算法引用、四路参考摘要、floor、on/off、attack/release、最少路数、初态、invalid/interval reset与更新规则。生产选值需独立校准输入及适用条件；bg_pre只服务各自开发诊断，不做在线自动学习的默认材料。

calibration：必须绑定通道映射、几何/单位、采样率和声速适用值、增益/延迟校正政策（包括明确“未应用”）、参考数据身份及估计方法/不确定性。未校准不能用零修正值宣称校准完毕。噪声功率参考与几何/通道校准分别具名，不能共用不明“calibration”摘要。

Tracker：选定状态语义SEARCH→ACQUIRE→LOCKED/HOLD；同一因果时基严格递增，gap/reset清获取历史；拒绝不能增加获取计数，HOLD只能显示旧方向且不更新last_fresh/expiry，不发fresh控制。数值参数必须显式给定：应用角域、获取帧数/角散布、跟踪跳变容差、HOLD时长、gap界及时间域。S4的±30°、5帧、8°、20°、9600/1440样点只作旧配置来源，不在本轮自动生产采用；尤其不能拿±45录音的拒绝结果反向调整应用角域。平均与圆周跨界政策必须随角域决定，原有限扇区算术平均不能泛化到全圆。

TTL：分为结果运输有效期T_result（S3 frame.last_id为起点、原sample_id域）和Tracker方向保持T_hold（最后fresh的指定时基）。二者不是同一参数；9600 HOLD不能拷为C桥TTL，512夹具也不成为默认。两者各自带数值/单位/起点/域/来源，等号有效、溢出拒绝、HOLD不续期。A先给可信原ID↔session采样时间锚和处理等待界/测量入口；B再结合允许的方向年龄/目标动态条件定数值。即便未来T_result大于一个hop，也不得仅因延迟而改成无期限有效。

时域采用D14-03：max(required_status_visible_at)≤available≤commit_now≤expiry仅同域比较；+8仅用于source→DAS emit坐标。C桥take检查与DAS控制有效期分别执行；unknown clock保留不提交/take WAIT，生产等待上界与超时策略仍须A绑定。缺锚/非单调/溢出不发布fresh。

## B14-05 / D14-04：实例与合法分支

pair→IFFT固定：01→0、02→1、03→2、12→3、13→4、23→5。

外部expected集合包含：transport、frame-domain、binding；mean_0..3、gate_window_0..3、doa_window_0..3；gate_fft_0..3、doa_fft_0..3；fixed4_gate_0..3、fixed4_doa_0..3；gate_state；每pair的phat、对应ifft及lag；doa（含资格判断/CORDIC子状态）、tracker、result_binding。名称在本稿为符号实例，A现mean/gate-window复合项需显式映射到这两类，不分配CSR或OR-mask位号。

未取消事务的每unit必须恰好一个最终事件，绑定原事务/三份身份及可见时刻。取消事务则按B14-R1-02的事务ABORT终结等待：此前最终事件不改，其余实例由ABORT快照明确标为CANCELLED，不要求已取消硬件实例再回报完成。区分“执行成功且结果可用”“执行成功但算法拒绝”“依赖不满足未执行”“数值/协议错误”和“事务取消”；这些是逻辑类别，不能直接假装S3已有对应ABI。missing/duplicate/wrong identity绝不能补成完成。

本候选分支表（须独立复核/A确认后实施）：

| 原因 | 允许未执行的unit | 最终语义 |
|---|---|---|
| gate关闭，且前端/8FFT/fixed4状态已完整且无错 | 六phat/ifft/lag和doa，均以GATE_CLOSED显式闭合 | tracker仍处理一次无候选更新；结果是拒绝或既有HOLD，非fresh |
| 某pair合法输入但PHAT有效bin不足12或零能量 | 只跳该pair的ifft/lag，PAIR_UNUSABLE | phat记录正常算法拒绝，其他pair继续；不伪造相关序列 |
| 合法lag少于3或几何秩不足 | doa完成资格拒绝，内部CORDIC不执行；不是缺doa最终事件 | tracker接受无候选；无fresh |
| DOA残差/模长不合格 | doa完成资格拒绝，CORDIC可不执行 | 无fresh；不把数值角度称正确方向 |
| 上游数值overflow/非法共轭 | 依赖后级不执行，NUMERIC_INVALID并保留原错 | 整帧无fresh，不归为正常gate关闭；gate/Tracker的invalid处理需配置明确，不通过伪造正常输入推进状态 |
| transport/status身份/重复/遗漏/致命错误或session取消 | B14-R1-02的事务ABORT覆盖所有仍待定unit为CANCELLED；不使用正常SKIPPED成功路径 | 立即终结该事务逻辑等待、保留原错和已完成历史；无新commit/take，资源退役另等实际abort/drain |

基线不以gate关闭跳过前端或任何前向FFT，也不跳过tracker/result_binding最终说明。需要这种省算优化须新合同/状态测试。14次变换是全有效路径，合法拒绝路径中未启动的IFFT必须记“未运行及原因”，不能报8FFT/6IFFT全成功。无论何种分支，expected集合不由DUT缩减，SKIPPED不是OK；本表不能作为现有OR-mask已实现逐实例屏障的证据。

## B14-06 / D14-05：所有权与 I14-TOKEN-01

同意RX完成/cache核对→复制入算法自有环→释放RX；帧最后读取需包含mean及双窗最后原PCM读取，若实现DAS仍借原PCM，还须包含该读取。不能只数FFT输入结束；实现应显式给出每个消费者的read_done集合，A确认实际别名/拷贝边界。result_begin不释放帧；结果、PCM、审计寿命分别管理。commit不等待DAS消费或audit ack，避免环形等待。

选择以下新的候选错误归属规则，旧S3实现不自动继承：
- 可靠归属当前session的未知错误（包括slot越界）按既有合同fail-stop。I14-TOKEN-01这部分仍是待A修复的旧缺陷。
- 当前session中格式畸形/不可能slot/generation的无error完成也按新组合协议错误fail-stop；已知合法token的正常重复通知单独审计/拒绝，不自动将所有重复API请求都升级新故障。重复unit完成不得形成第二次提交；其是否属于可容忍运输重复必须有显式来源合同，否则当协议错误。
- 只有能凭boot/session映射证实为旧回调才STALE审计，不杀新session。future session、未知boot或无法归属事件不得按session!=current一概旧回调处理；活动session暂按协议完整性故障fail-stop并隔离事件，停止新提交，待显式恢复。无活动session时拒绝/审计，不启动新会话。A必须提供可验证归属方法，不能仅比较无来源的整数大小。
- 以上新增无error/未知归属政策需A确认并另列测试；不改原批准含义。正常旧session与当前合法完成混批两种顺序不能误杀；当前畸形/错误与合法完成混批两种顺序均不得新commit。测failed/撤销/take/审计，不能仅看返回码。

平滑STOP/SEARCH/TTL最多960样点回mono与fatal硬停分开；当前session晚错停止后续发布、撤销未消费结果，已输出PCM不可回滚。A负责真实abort/drain、旧回调退役、cache/IRQ与恢复；B本稿不替它提供硬件证据。


### B14-R1-01：背压与取消同边沿的唯一裁决

这是新独立fixed4包的单时钟逻辑取消规则，非AXI现有外设自动支持的事实。E表示该块/聚合器可靠观测到fatal、session_abort或受控reset的有效时钟边沿；跨域传播和取消可见点须由A绑定，未观测不能倒称已经取消。使用逻辑取消侧带与事务终结记录；不采用“等ready送完全部cancel beat”的方案。

1. 在E，取消优先于同边沿的语义输入接受、unit正常完成、commit和take；锁存该身份的取消原因和终结记录。若E边沿前输出valid=1且ready=1，物理transfer仍按电平记一次，payload/index沿旧值，标记TRANSFER_ON_ABORT；它不是可用数值/成功完成，不能用于提交。同边沿输入valid&&ready也记物理输入历史，但语义DISCARDED_ON_ABORT，不生成数值事务/输出义务。不能把真实握手日志改为“没有发生”。
2. 若E前输出valid=1、ready=0，该未传输beat由事务终结替代，不再要求输出一次；E更新后的首个状态输出valid=0，旧payload不再具有有效语义。已接受但仍在pipeline的输入同样取消。E之后旧generation不会因为ready恢复而重新输出。无取消时的背压保持规则不变；取消撤回必须为上下游共同约定，不能接到不识别取消的消费者而称契约成立。
3. 本地terminal_cancelled锁存及输出撤回在E状态转移完成，独立于输出ready、下游消费或审计ack；终结记录保持直到显式管理确认，不是可能被漏读的单周期脉冲。持续abort电平/同一原因重复请求不产生第二次终结或重新计数；后续不同错误追加故障审计，不恢复事务。E后阻止新的语义输入，只有管理层完成取消/资源退役并以新有效session/generation启动，才恢复接收。
4. 记录取消前语义输入数N、先前已输出传输数P、E同边沿旧输出传输数T（0或1）及对应index，未传输取消数=N-P-T；E同边沿被丢弃的新输入另计，不加入N。对本范围正常状态要求N>=P+T，违例另记协议错误，不以负数修正历史。已传输的P个输出不能回滚，但整个事务身份失效，未消费的下游结果撤销。
5. 若E与第513输出、最后status或本可成功的commit/take同边沿，取消胜出：可有物理传输/状态观察记录，成功commit/take必须为0，终结类别为取消。此前已完成并提交的历史不删；已提交后晚fatal走B14-06的撤销/停止路径，不将旧COMMITTED记录倒写成未提交。不得对已在外设产生的PCM效果承诺回滚。
6. 受控reset必须先由不随该数据路径一起清零的管理记录保留取消身份/待退役集合，再清数据通路；否则reset可能抹掉应审计的取消。异步复位、掉电或失效管理存储的恢复是A需另外给证据的域，不能假造E及无损审计。该缺件阻断相应硬件准入，不阻断单时钟取消规则的文稿审查。

### B14-R1-02：事务终结与未启动实例的取消

1. 建立事务时冻结完整expected集合及身份。任一transport fatal或其他会话级取消在E触发一个事务级ABORT快照：boot/session/interval/frame/generation、三份配置身份、expected集合身份、原因全集、E所在时域/坐标（未知则明确未知）、取消前已最终集合及其状态、其余待定集合。观察到的错误证据必须保留，不能以CANCELLED标签吞掉原错。
2. 快照中“其余待定集合”包括未启动、运行中和输出等待的实例；聚合器把它们的逻辑终态统一记CANCELLED_BY_TRANSACTION，并立即终结所有对该事务的逐实例完成等待。允许用一个包含完整集合的ABORT记录表示这些终态，无需逐实例伪造硬件done。此前已最终OK/算法拒绝/数值错误等记录原样保存；同E新正常status只保留为取消时观察，不抢占正常完成状态。expected集合不删除、不缩小。这里CANCELLED与成功SKIPPED、实际执行成功均不同。
3. 事务在E之后处于取消终态，不评估正常all-required成功谓词，也不继续等待max(status_visible_at)以提交；同E及之后该事务无新commit/take。审计明确正常已完成集合、未完成取消集合和成功提交是否曾在E前发生。第一次ABORT后迟到的unit状态不能再写第二终态或复活事务；按身份保留late/stale错误审计，旧session/当前错误规则仍沿B14-06。
4. **逻辑等待结束不等于硬件排空或内存可释放。** 仍在DMA/IP中的引用、HELD帧、PCM/结果槽、回调注册必须等各真实读者read_done或取消确认且不会再访问后才释放/复用；取消终态不得自动释放这些资源。A必须给物理abort/drain的有限上界和超时停机政策。超过约定界留在fail-stop/隔离状态，不能靠重用token/缓存“解锁”；没有该界不宣称资源退役或实时恢复已完成。
5. 取消快照写入是本地锁存状态，不依赖audit消费者ack来结束正常等待；A必须在接受事务前提供有界、不可覆盖的终结记录容量，或在容量不足时拒绝开新事务并fail-stop。已有审计队列满时保留故障及未退役身份，不可丢弃ABORT后继续运行。物理布局/容量/复位保存与CDC由A实现合同明确，本稿不凭空指定寄存器地址。

两问题的最小规范轨迹（设计期待，NOT_RUN，不冒充RTL测试）：

| 轨迹 | E前 | E同边沿 | E状态更新后及之后 |
|---|---|---|---|
| R1-a 背压后取消 | N=1,P=0,输出bin0 valid=1/ready=0 | abort=1,ready=0；T=0 | valid=0；一个事务终结；未传输取消数1；ready永远0也不阻塞逻辑取消 |
| R1-b ready与取消同拍 | N=1,P=0,输出bin0有效 | abort=1,ready=1；物理T=1 | TRANSFER_ON_ABORT，未传输取消数0；无commit/take；valid=0，不重发 |
| R1-c 正常完成 | 接受输入，未发生取消 | valid&&ready，abort=0 | 产生唯一完成beat；普通背压仍保持，完整事务仍等全部输出及最终status |
| R1-d 末拍/最后status同取消 | N=513,P=512，最后输出待传；其余成功条件已具备 | 输出ready=1、最后status与abort同时；T=1 | 正常成功提交/领取0；保留传输和status观察；终结为取消 |
| R2-a 前端后transport fatal | expected已冻结，部分前端已OK，六对后级未启动 | fatal归属本事务/session | 原OK保留，其余CANCELLED，原fatal原因保留，一个ABORT关闭等待；无新commit/take |
| R2-b 取消后迟到完成 | 已有ABORT及待物理退役引用 | 原generation到达unit完成/错误 | 仅late/stale/错误审计；不替换终态、不新commit、不提前释放引用 |

以上状态、集合及计数需A在具体RTL/TB合同映射。ABORT快照覆盖等待不是补造未运行unit的成功status；审查通过也只关闭文稿歧义。

## B14-07：下一步与阶段裁决

1. B-REVIEW对本稿新增选择/分支及fixed4合同作独立只读技术复核；不重复274a408已经接受的容器82项或旧FFT/声学实验。检查发现回Astra裁决，不自行改产品。
2. 通过后由真实A按准确稿件确认B14-01/02/05/06的新组合范围；A可据此形成独立fixed4工程包和I14-TOKEN-01修复包，产品/TB串行写批，不将本稿视作修改one/Vitis授权。
3. B仍欠生产activity/calibration/Tracker参数及TTL数值，算法外部schema和新组合golden也未完成；A仍欠实际采样锚、运输/服务绑定、AMD对象及encoder/引用图实现。上述必须进入原#14/PR #30，不另建并行算法包。
4. 本稿选择不会关闭#14，也不以16服务方案代实测；9/25可裁决“候选部分确定、生产冻结未完成”，不能把本稿或录音诊断计为完整阶段PASS。正式评价阈值另在#17处理，不将内部PHAT/DOA常量混作验收门槛。

本轮实际检查：读取固定Git源码/合同与既有独立复核，机械绑定24份原字节；未执行算法、RTL、AMD/ARM、EDA或板测。既有证据复用、未重跑。主流程实际模型/强度无法独立观测，UNKNOWN。
