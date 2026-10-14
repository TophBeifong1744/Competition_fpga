# C 连续控制接合增量（#17 / #19）

任务来源：2026-10-13 用户指定的 `M｜主流程` 对话和任务1。此包供 A 接入既有 `F:/AMD/p/i17_live_loop/i17_live_loop.xpr`；C 的对应工程为 `D:/vavido_project/i17_live_loop/project/par/i17_live_loop/i17_live_loop.xpr`。目标 `xc7z020clg400-1`，Vivado 2025.2。新增同域连续控制入口，无 VIO 启动依赖。原 Python 自动断续不作为本次 RTL 证明。

## 接入内容与边界

`candidate-files.json` 列出本批唯一 7 个产品源。新增 `i17_continuous_control`、`i17_diag_consumer`、`i17_continuous_top`；其余 4 个文件按 `preimages.json` 和 `patches/` 对准确实际工程源应用增量。不得让同名模块的旧/新源同时加入工程，也不得覆盖 A 已更新的 bank、B PHAT/backend 或 C 共享读出改动；前像不匹配时用差异接合。

`i17_continuous_top` 是采样时钟域核心入口。A 在原板顶和原 PS/BD 中实例化，保留原 50→96→61.44 MHz 时钟、复位、麦克风映射、PWM 引脚和约束；不能直接设为物理板顶再为命令总线随意分配管脚。`reference/` 为本次仿真的准确依赖与正式生成 IP 原件，只用于复现和比对，不是第三套总工程，也不是指示覆盖 A 的当前组合。

命令、上下文、配置、停止及结果消费均属于同一个 61.44 MHz `clk` 域。上游保持多位 payload 稳定，通过 valid/ready 握手整体锁存。PS/PYNQ 跨域桥必须在原工程按一致性和复位合同接合，不能逐位双触发器同步多位配置。PYNQ 镜像、Overlay、CSR 地址及板上运行均尚未验证，属于后续 PS 接合；本批不伪造地址/镜像或宣称 PYNQ 已接通。

## 同域命令合同

`cmd_valid && cmd_ready` 每拍接受一条命令；`cmd_done` 和 `cmd_error` 在接受沿后输出。发送方撤下 valid 或提供下一条合法命令，不能把常高 valid 当作单次脉冲。

| op | 名称 | 行为 |
|---|---|---|
| 1 | CONFIG | IDLE/READY 中且全链空闲时原子锁存 context、map、deadline；先向来源声明 context，再允许首窗口 |
| 2 | RUN | READY 且真实来源已排空时等待前端就绪，先打开持续采集，下一沿启动窗口 manager |
| 3 | STOP | 幂等，立即撤新采集/运动授权，保持真实 FFT/status/报告/诊断导出可排空 |
| 4 | RECOVER | 显式 warm 请求；必须观察 manager 6～9，再回 0、config-ready 与真实全链排空后回 IDLE；重新 CONFIG/RUN |

`stop_request` 是独立同域最高优先级停止电平，保持高期间不允许运行。接受 RECOVER 的同沿也撤运动，不能让同沿结果继续驱动。重复 RECOVER 在恢复期间返回 `02`，不刷新恢复期限。

`context_pending[159:0]={boot64,epoch64,sid32}`。CONFIG 后先构造原 DECLARED context165；不等待 ff_busy，也不在 FFT 前等待其自身资格。

| map_pending 位 | 格式 / 含义 |
|---|---|
| 23:0 | offset，S24Q8 |
| 25:24 | direction，原 signed-angle-map S2 约定 |
| 43:26 / 61:44 | domain min/max，S18Q8 |
| 70:62 / 79:71 | mechanical min/max，U9 |
| 80 / 81 / 82 | map-valid / motion-enable / observe-only |
| 95:83 | 保留，必须 0 |

沿用原 map 合法性检查，机械区间必须包含既有复位位 180 度。观察模式要求 motion-enable=0；运动模式要求为1。水平沿用 max360/reset180，垂直固定原 max220/reset130，不改变数值算法或伺服标定。

`timeout_pending` 是 24 位周期数，合法范围 1～8,388,608，不放宽原 23 位上界。控制器分别对配置、前端等待、报告无进展、排空、恢复限时。RUN 仅真实完成报告刷新期限；部分数据不刷新。到期沿故障优先，不能用被取消逻辑屏蔽的 report-valid 组合反抑制超时。首因 `31`=到期，`32`=真实源故障/ABORT，跨 warm 保存到冷复位。

原 manager 新增 `CONTINUOUS_WATCHDOG`，默认0保持旧入口语义；本入口显式1。RUN 中仅实际完整源帧的 m-fire && m-last 刷新原23位期限，持续会话不再因总长度超过136.533 ms必停；后端另受报告期限约束。这是设计上界，不能充当后端服务时间实测。

状态：0 IDLE、1 CONFIG、2 READY、3 WAIT_FRONTEND、4 START_SOURCE、5 RUN、6 DRAIN、7 HELD、8 RECOVER。故障不伪清 busy/物理义务。HELD 代表安全停止状态，不自动表示已排空；读取真实义务和来源 status 后决定恢复。STOP 后 PWM 保持既有最后位置，冷复位关闭门，不能理解为断电。

## 自动消费与记录

真实 B 报告/ABORT 由核心每拍接受。`result_valid/result_abort` 为同域事件，提供完整725位 identity、原 S18Q8 角度、映射 U9 角度及 qualified 标记；PS 持久读取需要后续桥缓存，不能轮询单拍信号。`reports_consumed/aborts_consumed` 是64位饱和统计。运动仅在当前租约、来源资格、映射与运行控制全部满足时走原 servo 门。

五诊断 bank 按轮询 select、逐字导出、ACK 低相重装。仅 `diag_valid && diag_ready` 才 ACK 当前 seq/word；背压保持原记录，不伪消费。导出字段包括 bank、sequence、word、words、last。五类原记录长度37/41/38/27/32 words，保留原协议。停机期间接收方也须继续接受导出；持续背压最终由原 bank 满/期限安全停止，不能吞记录求通过。

## 复现入口及预期输出

仓库根运行：

```powershell
python simulation/run_i17_continuous.py control export watchdog canary_export
python simulation/run_i17_continuous.py full_probe
python simulation/run_i17_continuous.py full_stop
python simulation/run_i17_continuous.py full_stall
python simulation/run_i17_continuous.py full_first
python simulation/run_i17_continuous.py full_noise
```

默认工具 `C:/AMDDesignTools/2025.2/Vivado`，可通过本进程 `I17_VIVADO_ROOT` 指向同版正式安装。每次独立输出到 `codex_out/i17-continuous-control-20261013/runs/<case>-<attempt>/`，含冻结源、run.json、xvhdl/xvlog/xelab/xsim 原生日志、全链 events.csv。runner 查 Fatal 和完成标记，exit0不能掩盖失败；canary 必须实际拒绝错误 payload。`full_probe` 只定位时钟/首窗口进度，不代表连续链通过。展开使用至多32个作业、至少半机目标；XSim 运行阶段实际串行，不能靠无效任务填满全机。

默认4096样本 warmup 未在完整链短测中验证；完整链 TB 用0隔离该等待，控制器有单独等待测试。合成 PDM 只提供自然链路刺激，无声学方向真值；不能据此验收角度精度、现场跟随或响应最大值。

静态预算：既有 PDM/CIC 在停止采集时仍逐20拍取bit、64bit出PCM，warmup不受RUN门控。4096样本名义等待为5,242,880系统周期（85.333 ms），计入启动相位仍小于最大8,388,608周期期限；这是RTL设计预算，未替代默认warmup的整链实测/仿真。较小合法deadline仍可能因配置/等待/处理时间不足而安全超时。

`full_first` 保存首报告资格及完整6626位前端原件，用于定位不合格结果；它仍有资格断言，发生 Fatal 时必须记 SIM_FAIL。三角波刺激在1,706,188周期产生的真实报告为 numeric=0、eligible=0；B首错=0、前端协议/数值错误=0、映射/来源/租约资格均为1。不能跳过数值资格让转台动作，不能把该运行记连续驱动通过。

`full_noise` 只从 mic_data 输入确定宽带 PDM，检查三个自然报告、至少两个实际转台命令、自动记录消费、一般在途窗口 STOP、保持 STOP、warm 恢复及新 SID=4 首报告。各路 PDM 密度序列有5个PCM周期的目标偏移，独立累加器的初始相位使其不构成“PCM严格移位5点”的数值真值。没有内部 force 或资格旁路，全部产品源、正式 FFT/IFFT 与期限不因换测试刺激而改动。这一有限范围不能替代9M周期整链耐久、活动 FFT/IFFT 中 STOP、默认 warmup 或实板跟随验收。

本候选 `full_noise-1` 实际通过：5,481,560周期，5报告/4条实际转台命令/1个ABORT，完整标记 `CONTINUOUS_NOISE_STOP_COMPLETE`，无Fatal。SID3前三报告在1,967,053、2,601,050、3,234,636周期合格；STOP路径在3,521,092周期产生ABORT，同identity的3,521,101周期报告eligible=0，不驱动。warm后5,481,560周期的SID4新报告eligible=1。合格报告raw Q8=0、映射180度；这证明命令路径，不证明实际机械转动或声学真值。完整CSV、观察解析及原件哈希随包保存。

## A 接入、构建与现场保存点

1. 按 manifest/前像在原工程安全断点接合7源，同步指定实际组合中的 A bank、B 数学/backend、C 共享读出版本。实例化核心，接同域正式命令/接收端，核 HANN_FILE 指向原工程1024字真实ROM。不得把 diag_ready 永久1当作已有PS记录存储。
2. 复用原256位 ILA，采样同61.44MHz域。`ila_sample[255:192]` reports、[191:128] aborts、[127:64] records、[63:32] status、[31:24] first_fault、[23:16] manager、[15:8] control；[7:0] 依次 vertical-open/horizontal-open/qualified/armed/report/abort/servo-valid/stop-now。触发 first-fault、STOP、RECOVER，必要时复用旧宽记录探针查看 identity 和未归还义务。
3. 由 A 人操作首次集成综合/实现，保存准确源组合、全板及层级资源、预算差异、DRC/CDC/约束覆盖和 routed setup/hold 原件，以及匹配 bit/LTX/HWH。新控制估算约500 FF以内、consumer约80 FF以内，无新增DSP/BRAM；这是局部估算，不能从旧超容量结果相减推全板可放下。
4. 必要时序与实物安全条件满足后，由 C 现场执行非VIO启动、持续跟随、在途 STOP、保持 STOP、显式恢复并新SID重启及超时故障。保存原控制输入/状态、ILA、转台观察、方向与音频原件，数据直接交B。下载/复位/接线/供电/执行器动作未由本批自动执行。

准确验证摘要见 `validation-summary.md`，完整阶段见 `validation.json`，问题累计见 `repair-ledger.md`，独立判断见 `review.md`。没有完整链完成标记、匹配必要实现报告与实测时，状态必须保留 UNVERIFIED；A接入/验收记录另行绑定实际候选。

C本机冻结交接包：`python simulation/package_i17_continuous.py`；它核对本机原工程前像、原件及白名单，每个ZIP条目读回SHA256核验，输出到 `deliverables/i17-continuous-control-20261013-<七源ID前12位>-<包内容ID前8位>.zip` 与 `.sha256`。此生成命令依赖C本机实际前像，仅用于C交接；A按随包前像patch在原工程接合。
