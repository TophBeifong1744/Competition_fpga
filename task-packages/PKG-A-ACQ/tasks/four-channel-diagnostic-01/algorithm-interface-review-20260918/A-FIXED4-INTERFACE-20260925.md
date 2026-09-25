# #14 A工程接口补充：fixed4首包候选 r1

结论：B的准确r2可作为限定设计输入；本稿把首包收窄为单时钟、单在途事务的fixed4叶模块。r2真实A成员确认及本新增接口的非作者复核仍待完成，不能据此宣布生产冻结或直接修改A机工程。

## 1. 身份、范围和证据等级

- Issue #14 / 原PR #30；父提交 `274a408cfb3cdc12844a136be296a41fd901c3a6`，共享main基线 `28d58e908525d1de1c018eeb99fd607a07b6047c`。
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

以下是模块内部接口候选，不是现有AXI、CSR或C ABI。所有输入在同一`clk`上升沿满足建立/保持；无CDC。仅冷启动允许`cold_reset`清记录，条件是外部已证明无旧引用/回调；运行中受控reset必须走取消和持久记录，再退役，不能直接拉此reset。

| 端口组 | 方向/宽度 | 定义 |
| --- | --- | --- |
| `begin_valid/ready`, `begin_ctx` | 入/出1，入64 | 非零上下文句柄；ready仅空闲且终结记录容量已预留。接受begin的同边沿不收数据 |
| `s_valid/ready`, `s_ctx`, `s_bin`, `s_re/im` | 入/出1，入64、10、各29 signed | 输入bin必须从0连续到512，同句柄；只在握手边沿检验此输入 |
| `m_valid/ready`, `m_ctx`, `m_bin`, `m_re/im` | 出/入1，出64、10、各25 signed | 一入一出；普通背压下所有有效负载与侧带稳定 |
| `m_numeric_valid`, `m_ov_re/im` | 出各1 | 任一分量溢出，则本复数numeric_valid=0，re/im均0；溢出标志逐分量保留 |
| `cancel`, `cancel_causes[31:0]` | 入1/32 | 由管理层归属到当前ctx的同步取消；持续电平幂等。原因是候选内部bit集合，不分配系统ABI码 |
| `protocol_fault_now` | 出1 | 活动事务的实际输入握手出现ctx/bin错误时，同边沿组合告警；取消判定见第4节 |
| `data_done`, `sticky_numeric_overflow` | 出各1 | data_done仅表示513个语义输入及513个输出已传输；不是FFT最终status或帧成功 |
| `terminal_cancelled`, `terminal_ctx`, `terminal_causes` | 出1/64/32 | 每次被取消的ctx锁存一次终结，保持到管理确认；后到原因只做sticky并集，不产生第二终结 |
| `terminal_n/p/t`, `terminal_cancelled_untransferred` | 出10/10/1/10 | r2的N、P、T及N−P−T；另输出同E新输入物理握手标志和旧输出bin（仅T=1有效） |
| `terminal_saved_ack`, `ack_ctx` | 入1/64 | 管理层已持久接收该终结；只确认记录保存，不释放任何物理引用 |
| `local_quiescent` | 出1 | 本叶不再持有有效待输出beat且不会再自行产生旧ctx输出；不代表FFT/DMA停止 |
| `retire_valid`, `retire_ctx`, `retire_safe` | 入1/64/1 | 管理层确认当前ctx记录已保存、读者/回调已物理退役；本地条件同时满足后才返回空闲 |

64位ctx不是截断三份身份或把字符串转整数。管理层须在begin前建立不可改、无歧义映射：boot/session/interval/frame/generation、domain、channel、三份完整32B身份。句柄在一个boot内严格递增且不复用，耗尽拒绝；映射至少保留到物理退役。新boot启用前必须隔离旧来源并证明旧引用退役。此映射/分配器不在叶模块首包；集成前需实现与验证，不能靠外部口头保证生成生产身份。

## 4. 数据、取消和完成的逐边沿规则

正常ACTIVE时，`s_ready=(N<513) && (!q_valid || m_ready)`；`m_valid=q_valid`。cancel不组合掩掉已呈现的valid/ready；这样才能保留r2规定的同边沿物理握手。begin/retire握手不与数据事务重叠。取消后的状态禁止新的语义输入。

在边沿k接受一个合法复数，k之后q给出其转换结果，最早在k+1传出。连续有效且下游持续ready时II=1；同时出旧beat、入新beat时，q更新为新beat。最后bin传出后data_done保持，但ctx仍活动，等待管理层终结/退役。numeric overflow是数值无效，占位仍输出，累计sticky标志，不伪装饱和成功，也不自行省掉后续bin。

采用精确数学RNE(x/16)，先在足够宽的中间结果中检测是否超出S25，再窄化。正溢出输入区间`[2^28−8,2^28−1]`；`−2^28`合法输出`−2^24`。8→0、24→2、−8→0、−24→−2。实现不得先截断再检查。

有效取消条件`kill = cancel || protocol_fault_now`。协议错同边沿输入记物理接收但不加入合法N；当前旧输出若传输仍按T记账。protocol_fault_now必须在E前同域组合可见给管理层/消费者，消费者同E禁止成功提交；不可先寄存一拍后再倒称E已取消。组合告警只依赖本地预状态及输入/ready，管理层不得把它回灌到本地ready造成组合环。接口连到不认识取消的普通消费者不构成本合同实现。

E是可靠同步观察kill的边沿。优先级：kill > 正常输入计数/数据完成 > 正常退役。记录E前N、P及E的旧输出物理传输T；E的新输入物理握手另记为DISCARDED_ON_ABORT。E后q_valid=0、data_done=0、terminal_cancelled=1、local_quiescent=1，不等ready或audit ack。N−P−T必须非负；不变量破坏时保存原值并报协议错误，不能修数掩盖。

| E前状态与E事件 | E后要求 |
| --- | --- |
| N=1/P=0，输出stall；cancel=1且ready=0 | T=0，未传输取消数1，撤销输出；ready永久0不阻塞本地取消 |
| 同上，cancel=1且ready=1 | 物理T=1，TRANSFER_ON_ABORT，未传输取消数0；不能用于fresh/commit/take |
| 末拍N=513/P=512，最后FFT status与cancel同时 | 可保存物理末拍/状态观察；取消终结，正常成功为0 |
| cancel持续或重复；迟到旧输出请求 | 一个终结，不复活旧ctx；额外错误来源由管理审计保留 |

这些是设计期待，NOT_RUN。普通stall保持规则的唯一撤回例外是双方已约定的取消。

## 5. 终结容量、记录与物理退役

本叶为一个活动ctx预留一个不可覆盖取消槽，未退役时拒绝新begin。terminal_saved_ack必须在terminal_cancelled已经可见之后到达并匹配ctx；确认后叶模块仍保留原终结及sticky原因到retire，不能因ack清除占用。后到新原因由管理层另外审计；审计接收不动原N/P/T快照。

取消后本地静止不依赖任何消费；正常路径只有513输出传完才本地静止。retire需要：ctx匹配、本地静止、retire_safe=1，且取消路径先前已有匹配saved_ack；正常路径需要data_done。retire_safe必须由管理层在实际读者read_done/取消确认且无未来访问后给出，不能固定绑1。kill与retire同拍不释放。非法ack/retire不得释放，送管理层审计；不能以错误控制事件清掉原故障记录。

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
