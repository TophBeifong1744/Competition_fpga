# #14 A工程接口补充：fixed4首包候选 r2

结论：B的准确r2可作为限定设计输入；本稿把首包收窄为单时钟、单在途事务的fixed4叶模块。r2真实A成员确认及本新增接口的非作者复核仍待完成，不能据此宣布生产冻结或直接修改A机工程。

## 1. 身份、范围和证据等级

- Issue #14 / 原PR #30；本轮父提交 `f1962ea2c5d4e93e7af88eaef3d6c5a3b61f9fe7`，初始增量父提交 `274a408cfb3cdc12844a136be296a41fd901c3a6`，共享main基线 `28d58e908525d1de1c018eeb99fd607a07b6047c`。
- 本A稿r2为R首次NEEDS_FIX后的第1轮返修；I14-F4-01/02均为FIXED_PENDING_REVIEW，作者不自行关闭。B原稿也称r2，两者按文件/哈希区分。
- B原稿：[准确r2](b-contract-r2-20260925/B-DECISIONS-20260925-r2.md)，SHA256 `30a9a550d4303d464dc2e56d8b2ce38774b49c1d8e313bc70efbc0c4b06c5924`。源索引SHA256 `3baff634ed25082ce1c57238b0aee7a5d8616e1dc924bb9b665881878a912228`。
- B r2独立技术复核为PASS_WITH_SCOPE；B14-R1-01/02仅为VERIFIED_CLOSED_MANUSCRIPT_ONLY。r1被r2取代，不把r1结论或PR旧APPROVED扩到本候选。
- 工程身份：四麦二维V1，ATK-DF7010P_7020P V3.9 / xc7z020clg400-2 / Vivado 2025.2；实际project_entry仍未验证。本批模式ANALYZE，claim_stage=PREFLIGHT，证据仅合同/来源核对。
- M编写工程选择；A成员拥有运输/PL集成；B拥有算法合同；R后续只读技术核查，真实非作者成员批准另按原PR办理。实际主会话模型/强度UNKNOWN，不从推荐推定。

## 2. r2的准确接收范围

| r2条目 | 本轮接收的设计输入 | 不随之获得的结论 |
| --- | --- | --- |
| B14-01/02 | gate与DOA双域、各4路FFT；每事务bin 0..512共513复数，S29独立RNE右移4得到S25/F23；溢出/无效占位和取消语义 | 不接收整份旧golden为新全链golden，不改变reference25 |
| B14-03 | 三份身份与上游来源的无环引用方向；准确24源对象绑定 | 外部算法schema、生产encoder、实际twiddle/AMD对象和新组合golden尚未齐备 |
| B14-04 | activity/calibration、Tracker与两类TTL明确暂缓；保留域/单位/因果约束 | 不采用旧4/2、3/3、512或开发配置作为生产默认 |
| B14-05 / R1-02 | 冻结完整expected；正常分支按r2；ABORT保存原最终集合F，其余Q=expected−F显式取消，含未启动实例 | 不证明现OR-mask已实现逐实例屏障，不把取消当SKIPPED成功 |
| B14-06 / R1-01 | 同边沿取消优先；当前未知错误及新无error/未知归属政策按r2分开；物理传输历史不回滚 | I14-TOKEN-01源码缺陷仍OPEN，未修C；物理排空与旧回调退役未测 |

本稿是M的技术接收与A侧候选补充，不代签真实A对r2的成员批准。生产参数缺件不阻塞本叶模块合同审查，但阻塞对应生产准入。

## 3. 首包结构及端口候选

一个fixed4实例一次只处理一个域、一个通道的513复数。八个逻辑事务可串行复用，仍保留八套身份/结果；本稿不声称串行满足48 kHz或hop预算。只含一项输出弹性寄存器及计数/取消状态，不含FFT IP、帧聚合器、DMA、CSR、DAS或PS桥修复。

以下是模块内部接口候选，不是现有AXI、CSR或C ABI。所有输入在同一`clk`上升沿满足建立/保持；无CDC。`cold_reset`只用于冷启动或已完整退役后的数据通路初始化，合法条件及管理检查见第5节；活动事务的受控reset必须先取消、保存、退役，不能直接拉此reset。

| 端口组 | 方向/宽度 | 定义 |
| --- | --- | --- |
| `clk`, `cold_reset` | 入各1 | clk上升沿；cold_reset高有效、同步采样，无异步复位敏感边沿；第5节定义合法条件及复位值 |
| `ctx_active`, `active_ctx`, `terminal_saved` | 出1/64/1 | ctx_active从begin接受后保持到合法retire；包括正常数据完成及取消后的占用。active_ctx在占用时有效；terminal_saved表示此前已接受初始终结保存确认，不等于资源已退役 |
| `begin_valid/ready`, `begin_ctx` | 入/出1，入64 | 非零上下文句柄；ready仅空闲且终结记录容量已预留。接受begin的同边沿不收数据 |
| `s_valid/ready`, `s_ctx`, `s_bin`, `s_re/im` | 入/出1，入64、10、各29 signed | 输入bin必须从0连续到512，同句柄；只在握手边沿检验此输入 |
| `m_valid/ready`, `m_ctx`, `m_bin`, `m_re/im` | 出/入1，出64、10、各25 signed | 一入一出；普通背压下所有有效负载与侧带稳定 |
| `m_numeric_valid`, `m_ov_re/im` | 出各1 | 任一分量溢出，则本复数numeric_valid=0，re/im均0；溢出标志逐分量保留 |
| `cancel`, `cancel_causes[31:0]` | 入1/32 | 由管理层归属到当前ctx的同步取消；持续电平幂等。原因是候选内部bit集合，不分配系统ABI码 |
| `protocol_fault_now`, `protocol_fault_bits_now` | 出1/2 | 实际输入握手错误的组合告警；bits[0]=ctx不符，bits[1]=bin不符，可同时置位，now为两位OR；第4节定义持久编码 |
| `data_done`, `sticky_numeric_overflow` | 出各1 | data_done仅表示513个语义输入及513个输出已传输；不是FFT最终status或帧成功 |
| `terminal_cancelled`, `terminal_ctx`, `terminal_causes` | 出1/64/35 | 每次被取消的ctx锁存一次终结；原因[0]=外部cancel曾有效，[1]=本地ctx错，[2]=本地bin错，[34:3]=外部32位原因并集；保持到合法retire |
| `terminal_n/p/t`, `terminal_cancelled_untransferred` | 出10/10/1/10 | r2的N、P、T及N−P−T，均是首次取消快照 |
| `terminal_s_transfer`, `terminal_t_bin` | 出1/10 | 首次E的新输入物理握手标志（不加入N）；旧输出bin仅terminal_t=1时有效，否则确定为0；两字段保持到合法retire |
| `terminal_saved_ack`, `ack_ctx` | 入1/64 | 管理层已持久接收该终结；只确认记录保存，不释放任何物理引用 |
| `local_quiescent` | 出1 | 本叶不再持有有效待输出beat且不会再自行产生旧ctx输出；不代表FFT/DMA停止 |
| `retire_valid`, `retire_ctx`, `retire_safe` | 入1/64/1 | 管理层确认当前ctx记录已保存、读者/回调已物理退役；本地条件同时满足后才返回空闲 |

64位ctx不是截断三份身份或把字符串转整数。管理层须在begin前建立不可改、无歧义映射：boot/session/interval/frame/generation、domain、channel、三份完整32B身份。句柄在一个boot内严格递增且不复用，耗尽拒绝；映射至少保留到物理退役。新boot启用前必须隔离旧来源并证明旧引用退役。此映射/分配器不在叶模块首包；集成前需实现与验证，不能靠外部口头保证生成生产身份。

## 4. 数据、取消和完成的逐边沿规则

正常ACTIVE时，`s_ready=(N<513) && (!q_valid || m_ready)`；`m_valid=q_valid`。cancel不组合掩掉已呈现的valid/ready；这样才能保留r2规定的同边沿物理握手。begin/retire握手不与数据事务重叠。取消后的状态禁止新的语义输入。

在边沿k接受一个合法复数，k之后q给出其转换结果，最早在k+1传出。连续有效且下游持续ready时II=1；同时出旧beat、入新beat时，q更新为新beat。最后bin传出后data_done保持，但ctx仍活动，等待管理层终结/退役。numeric overflow是数值无效，占位仍输出，累计sticky标志，不伪装饱和成功，也不自行省掉后续bin。

采用精确数学RNE(x/16)，先在足够宽的中间结果中检测是否超出S25，再窄化。正溢出输入区间`[2^28−8,2^28−1]`；`−2^28`合法输出`−2^24`。8→0、24→2、−8→0、−24→−2。实现不得先截断再检查。

有效取消条件`kill = cancel || protocol_fault_now`。协议错同边沿输入记物理接收但不加入合法N；当前旧输出若传输仍按T记账。protocol_fault_now必须在E前同域组合可见给管理层/消费者，消费者同E禁止成功提交；不可先寄存一拍后再倒称E已取消。组合告警只依赖本地预状态及输入/ready，管理层不得把它回灌到本地ready造成组合环。接口连到不认识取消的普通消费者不构成本合同实现。

**I14-F4-01持久原因定义：** 正常ACTIVE的`s_valid && s_ready`为1时，分别比较`s_ctx != active_ctx`和`s_bin != N`得到protocol_fault_bits_now[0]、[1]；没有此实际握手则两位均0。N在比较时为E前已语义接受数。`cause_now[34:0] = {cancel ? cancel_causes[31:0] : 32'b0, protocol_fault_bits_now[1:0], cancel}`。首次kill在E把cause_now锁存到terminal_causes；因此仅本地bin错得到0x4，仅ctx错得到0x2，两者同时得到0x6。外部cancel即使cancel_causes=0也有bit0=1；cancel=0时外部原因线的闲置值不进入记录。外部与本地错误同E并存时取全部并集，不以外部输入覆盖本地位。

首次取消之后，同一ctx的terminal_causes只做`旧值 OR cause_now`，不清位；terminal_saved_ack不清原因。其他首次快照字段（身份、N/P/T、terminal_s_transfer、terminal_t_bin）不重采样；持续cancel不生成第二终结。管理层在E用公开的组合fault位和自身cancel输入保存原因/禁止commit，不能等寄存输出下一拍才阻止提交；取消后的新增原因另写late-error审计，不倒改此前已保存的初始快照。terminal_saved仅确认初始快照，不免除管理层对后到原因的保存责任。

E是可靠同步观察kill的边沿。优先级：kill > 正常输入计数/数据完成 > 正常退役。记录E前N、P及E的旧输出物理传输T；E的新输入物理握手另记为DISCARDED_ON_ABORT。E后q_valid=0、data_done=0、terminal_cancelled=1、local_quiescent=1，不等ready或audit ack。N−P−T必须非负；不变量破坏时保存原值并报协议错误，不能修数掩盖。

| E前状态与E事件 | E后要求 |
| --- | --- |
| N=1/P=0，输出stall；cancel=1且ready=0 | T=0，未传输取消数1，撤销输出；ready永久0不阻塞本地取消 |
| 同上，cancel=1且ready=1 | 物理T=1，TRANSFER_ON_ABORT，未传输取消数0；不能用于fresh/commit/take |
| 末拍N=513/P=512，最后FFT status与cancel同时 | 可保存物理末拍/状态观察；取消终结，正常成功为0 |
| cancel持续或重复；迟到旧输出请求 | 一个终结，不复活旧ctx；额外错误来源由管理审计保留 |
| R的反例：N=P=0、q空，输入ctx正确但bin=1，cancel=0、cancel_causes=0 | fault_bits=2'b10；E后terminal_causes=0x4、terminal_s_transfer=1、N=P=T=0，无零原因终结 |
| 同上但ctx也错误，且cancel=1、cancel_causes=0x8 | cause_now=(0x8<<3) OR 0x7=0x47；三类原因保留，不能把本地错冲掉 |

这些是设计期待，NOT_RUN。普通stall保持规则的唯一撤回例外是双方已约定的取消。

## 5. 终结容量、记录与物理退役

本叶为一个活动ctx预留一个不可覆盖取消槽，未退役时拒绝新begin。terminal_saved_ack必须在terminal_cancelled已经可见之后到达并匹配ctx；确认后叶模块仍保留原终结及sticky原因到retire，不能因ack清除占用。后到新原因由管理层另外审计；审计接收不动原N/P/T快照。

**I14-F4-02复位定稿：** 首次上电尚无已初始化状态时，管理层先保证所有请求（begin_valid、s_valid、cancel、terminal_saved_ack、retire_valid）为0、无外部旧引用/回调，再至少一个clk上升沿采样cold_reset=1；在此之前不声称输出/状态有效。已初始化后的再次cold_reset，前一状态必须满足`!ctx_active && !terminal_cancelled && !terminal_saved && local_quiescent`，同时上述五项请求均0，且管理层的旧引用/回调退役证明已成立。叶侧TB断言检查前述公开状态和请求，管理模型另断言其持有的退役证明；硬件中证明来自真实读者，不能由叶虚构。非法cold_reset是环境合同违例，必须被断言/管理监控报告；本首包不承诺非法复位仍无损审计或故障容错，不将它用于运行中取消。

合法cold_reset保持期间begin_ready、s_ready、m_valid为0；采样边沿清q、N/P及所有sticky/终结字段，ctx_active=0、active_ctx=0、data_done=0、terminal_saved=0、local_quiescent=1。所有payload/terminal观察字段复位为0，组合protocol_fault输出为0；释放cold_reset后恢复空闲begin资格。begin接受时装载active_ctx、ctx_active=1，清本事务计数/终结字段、local_quiescent=0；直到513输出全部传完或取消才再次local_quiescent=1。合法retire清占用及本地终结/确认字段，回相同空闲状态，不重置外部句柄分配器。运行中受控reset的合法次序是cancel→初始终结已保存→真实引用退役→retire→可选cold_reset，外部持久审计/boot/generation不随它清零。

取消后本地静止不依赖任何消费；正常路径只有513输出传完才本地静止。retire_safe必须由管理层在实际读者read_done/取消确认且无未来访问后给出，不能固定绑1。合法cold_reset之外，ack/retire按以下E前公开状态判定，管理层与叶采用同一判据：

- `ack_ok = terminal_saved_ack && ctx_active && terminal_cancelled && (ack_ctx == active_ctx) && !terminal_saved`。满足则E后terminal_saved=1；否则该请求不改变任何终结或资源状态。首次取消同E的ack因E前尚未terminal_cancelled而拒绝；持续cancel期间可保存已存在快照，ack不清原因且不改kill优先级。
- `retire_ok = retire_valid && ctx_active && (retire_ctx == active_ctx) && local_quiescent && retire_safe && !kill && (terminal_cancelled ? terminal_saved : data_done)`。不满足则不释放。首次有效ack与retire同E时，retire使用旧terminal_saved=0，必须另一个边沿才能成功；kill与retire同E同样不释放。
- **审计责任固定归管理层**：本叶不增加reject事件端口。管理层在每个E用上述公开信号计算`terminal_saved_ack && !ack_ok`、`retire_valid && !retire_ok`并各记一条拒绝事件（同E两者均错则两条），保存请求ctx、活动ctx、终结/确认/静止/安全/kill预状态及失败谓词，包括重复ack、错误ctx或未退役。无请求时不审计闲置payload。叶忽略被拒绝控制，不因它清错/复用；管理审计满按既有fail-stop/隔离规则处理，不能假称叶已保存该拒绝事件。该审计与真实排空仍是外围责任，但本地接受/拒绝判据不再由实现者选择。

帧管理层另须在开帧前预留至少一个完整活动帧的ABORT存储：固定身份、expected集合身份、E前最终集合F及状态、Q=expected−F、原因/坐标及既有提交历史。首个集成候选只允许一帧在途，容量按这一个完整集合设计；位图宽度/实体布局仍待管理器合同，不是本叶取消槽的别名。无容量拒绝开帧；运行中审计满保留故障和未退役身份并fail-stop，不能覆盖后继续。

叶模块513点data_done与FFT最终status分开：全1024 FFT输出、index/TLAST/config/status校验和高半段排空由外层FFT适配负责。管理层仅在两者齐备且无错时闭合对应fixed4/FFT成功；此前不允许fresh。取消时保存E前F，其余含未启动unit统一CANCELLED_BY_TRANSACTION，不再等各unit正常done；之后物理退役仍单独等待。已经闭合的F不因叶取消而倒写，已物理输出PCM不回滚。

## 6. 可承诺的边界与尚缺的工程绑定

| 项 | 首包设计预算 | 当前证据/缺件 |
| --- | --- | --- |
| 本地数值流水 | 无stall最早下一边沿输出，II=1；一项弹性输出 | 仅设计，无RTL/仿真/STA测值 |
| 连续513点数据 | 从第一个输入握手边沿起，第513输出最早在其后第513边沿传输 | 输入/ready必须持续；不含begin、FFT status和退役 |
| 本地取消 | E状态转移即终结/撤回；不随ready延迟 | E之前CDC传播不在本包；真实频率未知 |
| 输入缺失/输出背压/最终status等待 | 不能给有限成功完成界 | 管理器须用真实时基设置有限watchdog并触发cancel；阈值、来源和范围待绑定，不能填0或任意默认 |
| 外部abort/drain | UNKNOWN | A须给每读者、DMA/IP/回调的有限上界及观测点；超时保留隔离、fail-stop、不复用token/缓存 |
| 受控reset记录保存 | 先管理保存终结，再清叶；不共用破坏记录的reset | 实际管理存储/复位域/CDC待设计；异步reset/掉电无损恢复未证明 |

因此首包可以验证本地周期行为；在watchdog、管理存储和真实排空界未完成前，不能称完整事务系统、可上板安全恢复或实时通过。

## 7. 后续实现与核验入口

候选产品路径`project/rtl/algorithm/fixed4/`，候选验收路径`simulation/tb/algorithm/fixed4/`；现阶段不创建RTL/TB、不修改模块清单或one/Vitis。正式工程由E依据锁定run-fpga-workflow的产品写入、独立验收资产串行批次处理，真实A工程操作仍遵守用户操作约定。R本轮只读核查文稿，不另起实现或重复B已经审过的全部数值研究。

验证要求保留为可执行包的完成定义：独立整数RNE期望；145旧向量仅复用输入身份；复数一分量/双分量溢出；513个bin、标签、无重复/漏项；随机和永久ready=0；末拍/状态/取消同E；持续取消、终结ack与retire分离；late事件；容量不足；受控reset保护。协议错负例须检查同E消费者不能提交。测试管理模型只能证明逻辑合同，不能充当真实DMA排空。

公开接口矛盾、r2哈希变化、同边沿裁决无法成立、需要更改既有RTL/IP/参考模型/生产配置时返回M；不由执行方改合同绕过。I14-TOKEN-01沿原问题独立串行修复包，不能混入fixed4首包或重置返修次数。

本轮实际完成：两个B交付包逐字节收件、来源身份核对，以及本工程接口候选。复用已有数值/录音/技术复核，未重跑；RTL、EDA、板测、正式性能和生产冻结均NOT_RUN/未通过。此文稿发布不关闭#14/#16，不执行merge，不表示已向其他聊天发单成功。

本次A稿r2返修只改本文件：I14-F4-01补固定本地原因/外部并集及首次快照保持；I14-F4-02补clk/cold_reset、终结观察与控制判据。可见接口增量为terminal_causes从32到35位，新增2位组合fault明细、两个首次传输观察字段及ctx_active/active_ctx/terminal_saved；原数值公式、正常数据II/延迟及取消E优先级不变。表中新轨迹是文稿推演NOT_RUN，不能称RTL验证；两项状态仍FIXED_PENDING_REVIEW，等待R对本轮增量复核及真实成员批准。
