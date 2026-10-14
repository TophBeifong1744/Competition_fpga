# 本批问题与证据累计

源对象为实际 C 工程中的四麦连续诊断链；原问题 ID 和验收条件保留，不以换包名重置。

| ID / 原因 | 处置与有效进展 | 当前状态 |
|---|---|---|
| 首窗口启动互等 | 新 CONFIG 先声明上下文，不等 ff_busy；FFT/status permit 不再等由其自身建立的 qualification | 控制定向通过，完整链待完成 |
| 连续会话23位总时长必超时 | CONTINUOUS_WATCHDOG 仅实际完整源帧刷新，保留原期限；独立报告期限保护后端 | manager缩放测试1000周期/32周期期限通过，不是实测136ms耐久 |
| C-CONT-RECOVER-001 | 非作者发现接受 RECOVER 同沿报告可运动；加入组合撤权，真实义务仍排空 | CLOSED，控制定向证据 |
| C-CONT-FAULT-002 | 非作者发现 DRAIN 晚错首因未记录；覆盖 START_SOURCE/RUN/DRAIN，首事件锁存，不因持续错误重置计时 | CLOSED，control-7 |
| 重复 RECOVER 延长期限 | 在途重复命令返回02，不重复 warm 或重新计时 | CLOSED，control-7 |
| C-CONT-TIMEOUT-LOOP-001 | 非作者发现 report→progress→timeout→cancel→B report 结构环；期限仅由寄存计数/状态判定，到期优先 | CLOSED，control-7实际反馈边界171项检查 |
| 当前故障反馈 | 新增单向 diag_current_fault，避免把外部控制引发 halt/晚错再组合反馈到控制器；历史 FF 错误只在 ff_busy 有效 | 编译/展开通过；完整链待完成，不能断言它解释所有慢运行 |
| sandbox生成C编译失败 | control-1 未通过展开；在自动审查批准的本机正式XSim进程环境复验 | ENV_FAIL，不计RTL通过；control-2及后续有效 |
| control-6测试声明顺序 | 测试 wire 在 fault_now 声明前引用；仅修测试声明顺序 | TEST_ASSET_COMPILE_FAIL，control-7修正通过，产品未因此改动 |
| full_stop-1～4 | 原首次运行被用户中断；后续针对启动/单向反馈和进度观察的不同候选主动停止；无完整完成标记 | INTERRUPTED/UNVERIFIED，不复用为整链PASS |
| full_probe-1 | 600秒墙钟限时结束；实际推进到1,215,000周期，FF/NP/B未忙、fault0，未到首完整窗口；工具约每秒2000周期 | TOOL_WALL_TIMEOUT；不能把慢仿真或缺报告认定RTL死锁。控制源期间变化，不能冒同候选 |
| full_stop-5 / full_stall-1 | 同候选真实首报告在1,706,188周期；full_stop第二报告在2,346,197周期，均eligible=0。停止长测，集中首结果资格诊断；保留各自 external-stop.json 和原生日志 | INTERRUPTED_FOR_FIRST_RESULT_DIAGNOSIS，不是PASS，也不是已证实死锁 |
| C-CONT-ELIG-001 / full_first-1 | 同七源首报告实际 b_error=0、numeric=0、map/gate/lease/report_current=1、ff_error/protocol/numeric=0。非作者解码实际6626位：unit状态均OK，FFT各1024，fixed4各513，started/retired=FFFF，source_received8192，无取消/协议/数值错误。资格断言实际Fatal，XSim退出0被runner拒绝 | SIM_FAIL；当前无已证实的前端终结/资格接合错误。具体后端数值拒绝分支UNKNOWN，缺同报告direction_reason/pair等字段，不改变产品阈值 |
| full_noise-1 | 七产品源与全部冻结源匹配；5,481,560周期、5报告/4实际命令/1 ABORT，真实完成且无Fatal；SID3三报告合格、STOP同identity ABORT/不合格报告不驱动、warm后SID4首报告合格。刺激仅mic_data，无force或资格/期限改动 | FUNCTIONAL_SIM_PASS，有限三自然报告＋一般在途STOP＋保持STOP＋真实排空＋warm＋SID4合格重启；9M/活动IP STOP/默认warmup未测 |

复核共三次有实际源码进展的增量判断：恢复同沿撤权→DRAIN首因/重复恢复→独立期限判定及反馈边界。最后一次只读非作者限定同意局部控制；完整连续链没有被自签或批准。后续同一故障若无进展，遵守连续两轮无进展/最多三轮规则，不继续无依据自动返修。

当前完整链验证使用七源准确冻结；仅按实测工具速度增加墙钟等待，未扩大 RTL 周期期限，未改 PDM 分频、时钟、算法、ROM或 FFT/IFFT。原件与最终状态绑定于 validation.json；运行缓存、生成C及工具波形不进入精确增量包。

C-CONT-ELIG-001 的接合判断已得到正向自然刺激证据：同一七源在宽带PDM下资格和运动路径通过，未针对三角波失败修改产品。原full_first数值拒绝的具体B分支仍UNKNOWN；它保留为测试刺激的失败事实，不新增无依据算法返修，也不改记PASS。
