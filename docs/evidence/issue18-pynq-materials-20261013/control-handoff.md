# 任务1控制候选给 PYNQ 接合的合同摘要

准确候选 `b529fed84bde1d5d5d6326e0d8870416c738657a`（PR63）。权威源为该提交 `project/rtl/c_board/i17_continuous_top.sv`、`i17_continuous_control.sv`、`i17_diag_consumer.sv` 及其接入 README；本摘要不定义 MMIO 地址、CPU 结构体布局、中断或 DMA 协议。

## 端口、原子命令和独占

| 同域端口 | 宽度 / 含义 | PS 桥需要落实的事实 |
|---|---|---|
| clk/rst_n | 61.44MHz / 低有效复位 | 与实际 PS/AXI 域的跨域和复位顺序；多位数据整体稳定握手，不能逐位双FF |
| cmd_valid/cmd_ready/cmd_op | 1/1/3；op1 CONFIG、2 RUN、3 STOP、4 RECOVER | 一次 valid&&ready 接受一条命令；持续 valid 会逐拍接受，不是一次启动。单一控制 owner及CPU交易身份/响应留存待桥实现 |
| context_pending/map_pending/timeout_pending | 160/96/24，CONFIG 整体锁存 | 影子多字写入、安全提交和 ACK；逐字 MMIO 写不应直接改变运行配置 |
| cmd_done/cmd_error | 1/8，接受沿后响应 | done 是命令响应，不是排空/恢复/运行完成；桥持久化后CPU读取，不能轮询单拍 done |
| stop_request | 独立同域最高优先级停止电平 | 保持高时禁止 RUN；不是已存在的 CPU 寄存器/异步外部引脚 |

配置 context=`{boot64,epoch64,sid32}`，有效声明由 core 生成165位版本/存在位；由控制 owner 管理会话身份，不能假定 core 已替 CPU 持久化分配唯一 boot/epoch/SID。

map96：offset `[23:0]` S24Q8，direction `[25:24]` 沿原 S2 约定；domain min/max `[43:26]`/`[61:44]` S18Q8；mechanical min/max `[70:62]`/`[79:71]` U9；map-valid/motion-enable/observe-only `[80]/[81]/[82]`；`[95:83]=0`。机械区间须包含180，观察模式 motion-enable=0、运动模式=1；详细合法性沿原 signed_angle_map。水平 max360/reset180，垂直保持 max220/reset130，不重新标定伺服。

CONFIG 仅 IDLE/READY 且真实全链空闲时接受，并先声明来源 context。RUN 在 READY/configured/来源空闲时接受，等待前端，先开持续采集再启动窗口。错误01=未知 op，02=RECOVER不合法/重复恢复，04=CONFIG被拒，05=RUN被拒；0只表示该命令未被拒绝。

## STOP、恢复、期限及状态

STOP 幂等，同沿撤采集/运动授权，FFT/status/report/诊断继续排空。PWM 保持最后位置；STOP不表示执行器断电。RECOVER 接受同沿也撤运动，显式 warm 后观察 manager 6～9，再回0、config-ready与真实义务/采集排空后回 IDLE；需重新 CONFIG/RUN 和新会话身份。恢复期间重复 RECOVER 返回02、不延长期限。warm 不伪清硬件 busy/overflow sticky；必要 cold reset由现场另行决定，不能由 Python 盲清。

状态0 IDLE、1 CONFIG、2 READY、3 WAIT_FRONTEND、4 START_SOURCE、5 RUN、6 DRAIN、7 HELD、8 RECOVER。HELD 是安全停止态，**到期也可进入 HELD，不能仅凭 HELD 认已排空**。桥需要提供同一次可靠状态快照中的实际 source/manager/义务与 drain 标记，当前 top没有独立CPU quiet寄存器。

timeout24单位是61.44MHz周期，合法1～8388608。配置、等待、报告无进展、排空、恢复分别计时；RUN 真实完整报告刷新期限，部分数据不刷新。上界对应约136.533ms，是设计预算，不是Linux transfer/STOP默认秒数。到期优先；first_fault `0x31`到期、`0x32`源故障/ABORT，跨warm保留至coldreset。生产PS各期限由系统预算另定。

## 结果和逐字诊断消费

| 输出 | 已有 core 行为 | CPU 接合缺口 |
|---|---|---|
| result_valid/result_abort | 单拍同域事件；core自动接收真实B报告/ABORT | 必须锁存/有界排队完整事件并定义序号/溢出/CPU取走；不能用Notebook轮询单拍 |
| result_identity | 725位=`{token64,generation64,context165,frame_first432}` | 多字一致快照、版本/会话绑定；不是DMA或C字节布局 |
| result_angle_q8/result_angle_deg/result_eligible | 原角S18Q8、映射U9、当前资格 | qualified才有运动资格；STOP同identity迟到报告可eligible=0，仍要保留原记录；raw角与机械角分开 |
| reports_consumed/aborts_consumed | 64位饱和计数，core接收统计 | 不等于CPU保存数；多字原子快照、精确整数读取和截断水位待实现 |
| diag_valid/diag_ready/diag_data | 1/1/32，只有握手后ACK当前 bank seq/word | 接收端确实保有该字后才ready，不能永久ready=1冒充PS存档；STOP时也需消费 |
| diag_bank/sequence/word/words/last | 3/64/6/6/1；五类记录37/41/38/27/32 words | 保持原bank布局/身份；桥定义有界整记录缓存、记录退休/软件ACK与满处理；last仅为记录末字，不是已冻结的DMA TLAST |
| records_consumed | 64位饱和整记录计数 | 与CPU/archive水位分别保存，长期背压按原bank满/超时停止，不能吞字求通过 |

源 report/ABORT core侧自动接受与诊断逐字 ACK 是不同接受点，CPU取走又是第三个接受点。取消/晚错不能被“只保存成功角度”的软件过滤；STOP/首错/身份、事件顺序、丢失或水位截断必须可追溯。

## 原 PCM 与 CPU 通路的现状

任务1 top 的 `m_axis_tdata/tkeep/tvalid/tlast` 在模块内部，`m_axis_tready=1'b1`，没有外部原PCM stream端口。任务1因此没有完成旧 C1 raw→S2MM 接合，也没有实现结果→CPU缓存或诊断→DMA打包。不要将旧 C1 的8000B包、GPIO RUN地址、旧 DMA 参数直接套在此 top。

C 保存的 native XPR仍列 `i17_vio_board_top`；任务1作为准确源增量交 A，未改本机原工程。A/C需要在原总工程中给实际控制桥、结果存储及所需PCM抓取路径，集中确认资源/缓存/带宽/期限和CDC；B按该公共接口接软件，不为补件先造替代ABI。

复用任务1同域256位ILA和原验证范围；它可观测控制/首错/计数，不能代替CPU持久记录或同候选 STA/板测。当前没有 PYNQ driver、Overlay加载或物理转台通过结论。
