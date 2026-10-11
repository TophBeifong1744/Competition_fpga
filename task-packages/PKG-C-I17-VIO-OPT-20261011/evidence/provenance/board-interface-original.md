# I17 VIO 单窗口板级候选接口

日期 2026-10-10；主模式 RTL_IMPLEMENTATION。准确候选以 `BOARD-SNAPSHOT.json` 为准。
顶层 `i17_vio_board_top`；目标 `xc7z020clg400-1`；Vivado 2025.2。
用户已选择同一 61.44 MHz 时钟及 Vivado VIO/JTAG 控制。此候选不是连续重授权实现。

## 范围及未改变项

复用 31 源核心（其中 motor/top 为既有已冻结 61.44 MHz overlay），算法、核心接口、原握手和原证据内容均不修改。
新增同域控制器、结果保存/导出、物理 PWM 开门及实际 11 IO 板顶层。VIO/ILA 必须使用后续同版官方 IP 配方；没有 stub。
原始 inputs、两项 PWM overlay、verification 和用户 D 盘工程均未修改。
AXIS PCM 由 `m_axis_tready=1` 实际排空，但不保存 PCM 原始录音；本候选不能声称有 RAW 文件。

## VIO 固定端口

官方模块 `i17_board_vio`：4 input probes（64、64、32、128），4 output probes（32、160、96、32）。
官方模块 `i17_board_ila`：probe0 为 256 位；计划深度 1024。IP 尚未生成/完整 elaboration 尚未运行。

`probe_out0 control[31:0]`：bit0 COMMIT toggle；1 START toggle；2 STOP level，初值 **1**；3 WARM_RECOVER toggle；4 READ_WORD toggle；5 FETCH_DIAG toggle；6 DUMP toggle；7 RELEASE toggle；8 ABORT_READ toggle；其余为零。
toggle 由 0→1 或 1→0 都产生一次动作。复位后第一拍只学习基线。同拍多个 toggle 拒绝，不排队、不在 STOP 解除后重放。STOP 下可读、FETCH、DUMP、RELEASE、ABORT_READ 和 WARM；不能 START/COMMIT。

`probe_out1 context_pending[159:0]`：sid[31:0]、epoch[95:32]、boot[159:96]。
观察示例三者均为 1，即 `160'h0000000000000001000000000000000100000001`。
这只是人工声明上下文；真实 token/generation/frame_first 必须从源侧第一次 ff_busy 锁存，绝不由此示例冒充。

`probe_out2 map_pending[95:0]`：

| 位 | 内容 |
|---|---|
| 23:0 | 有符号 offset，Q8 |
| 25:24 | 有符号 direction，01=+1，11=−1 |
| 43:26 / 61:44 | 有符号源方向 min/max，Q8 |
| 70:62 / 79:71 | 水平机械 min/max，整数度 |
| 80 | 映射事实明确 present |
| 81 | 人工运动许可 |
| 82 | OBSERVE_ONLY |
| 95:83 | 必须为零 |

默认值 `96'h000400000000000000000000`（只有 bit82=1）；present=0、motion=0，不伪造未知机械范围。
观察模式要求 motion=0，无需合法机械映射；COMMIT 后真实 research profile 有效，允许数值计算，不 ARM、不提供 map_valid。
运动模式要求 present=1、motion=1、映射合法，且已填机械范围包含水平启动目标180°；范围本身由现场确定。motion=1 同时意味着现场确认垂直130°无干涉。
COMMIT/configure_motion 本身不打开物理 PWM 门。后续 START 获得一次授权、真实身份绑定且 current_qualified 成立后，才在内部低相开门；此时可能先输出水平180°、垂直130°的内部启动目标，再执行有效算法目标。
不增加人为170～190°限位。机械范围不等于电气0～360°。源范围沿用核心 [−180°,180°)，最大允许值为179+255/256°，不接受+180°。

`probe_out3 read_select[31:0]`：type[3:0]、diag bank[6:4]、bit7=0、word[15:8]、其余0。选择字段随对应动作锁存。

## 运行顺序

STOP=0 → 填配置 → COMMIT toggle → configured=1/READY → START toggle。
控制器等待真实 frontend_ready（4096 样本预热约85 ms），产生 start 上升沿，再发 diag_start。
源忙后锁存完整725位 identity，核上下文一致。运动模式先保持 ARM LOW，再 HIGH，等 current_qualified 才放 FFT 输出/status permit；观察模式直接放 permit。
一次 START 只授权一个真实窗口。默认内部 manager watchdog 保留，不让操作者在启动后追着手动 ARM。
report/ABORT 先保存，STOP/结束只撤销新命令资格，FFT/status/report/ABORT 继续排空。原 PWM 保持最后目标；STOP 不是机械急停或断电。
前端 manager NORMAL_HOLD(5) 只表示前端完成；后端 IFFT/DOA 尚未产生结果时，本窗口授权继续保持，不能据此提前停止。真实 report/ABORT 已保存、manager ERROR_HOLD(10) 或明确 STOP 才结束此授权。
数据导出并显式释放所有本地槽和核心诊断银行后，WARM_RECOVER 回到真实 manager IDLE；重新 COMMIT 和 START。没有自动连续重启。
WARM 是原生 diag_reset 请求，不冷复位、不清历史证据。拒绝/错误不会偷偷清空队列。
暖恢复先在请求脉冲被核心采样后观察原 manager 的恢复状态6～9，再等待其返回 IDLE 且 config_ready、完整 quiet/无义务/AXIS排空；请求前的旧 IDLE 不构成恢复完成。

## 输出 probe 位图

`probe_in0 status[63:0]`：

| 位 | 内容 |
|---|---|
| 0 / 1 / 2 / 3 | configured / observe / stop / evidence_empty |
| 4 / 5 / 6 / 7 | report_full / abort_full / diag_full / diag_partial |
| 8 / 9 / 10 / 11 | io_busy / config_ready / frontend_ready / ff_quiet |
| 12 / 13 / 14 / 15 | ff_busy / ff_ip_obligation / doa_busy / doa_ip_obligation |
| 16 / 17 / 18 / 19 | diag_armed / current_qualified / horizontal_open / vertical_open |
| 23:20 | 零 |
| 31:24 / 39:32 | controller state / manager state |
| 47:40 / 55:48 | controller error / evidence error |
| 63:56 | 0x17 标识 |

controller state：0 IDLE、1 CONFIG、2 READY、3 WAIT_FRONTEND、4 START_SOURCE、5 START_DIAG、6 BIND、7 ARM_LOW、8 ARM_HIGH、9 WAIT_QUALIFIED、10 RUN、11 DRAIN、12 HELD、13 RECOVER。

`probe_in1 result` = report_header[191:128]，report_full=0 时零：raw Q8[17:0]、command[26:18]、accepted/held servo angle[35:27]、command_valid[36]、frontend_abort_seen[37]、first_error[45:38]、存在标志[46]、map_valid[47]、numerical_valid[48]、delivery_eligible[49]、qualified_delivery[50]、current_qualified[51]、accept[52]、reject[53]、reject_reason[57:54]、其余零。
raw 是算法结果；command 是目标；servo angle/accept 不是实际机械到位反馈。

`probe_in2` = 最近 READ_WORD 的32位数据。
`probe_in3 read_meta`：seq[63:0]、type[67:64]、word[75:68]、words[83:76]、valid84、last85、partial86、diag_bank[89:87]、error[97:90]、其余零。

## 完整记录导出

所有多字字段 **低32位先出**，末字高位补零。READ_WORD 单字只读；DUMP 连续逐拍输出完整所选类型到 ILA，不自动删除。

| type | 内容 | words |
|---|---|---:|
| 0 | report 时配置 `{map96,context160}` | 8 |
| 1 | report_header | 16 |
| 2 | report identity725 | 23 |
| 3 | 原生 frontend terminal6626 | 208 |
| 4 | 原生 frontend ABORT payload180 | 6 |
| 5 | FETCH 到本地的完整/部分诊断记录 | 1～63；部分只输出确实捕获的字 |
| 6 | 原生 frontend ABORT identity725 | 23 |
| 7 | 后端 ABORT 时 active identity725 | 23 |
| 8 | 后端 ABORT 头192 | 6 |
| 9 | LIVE 状态128，DUMP 时冻结 | 4 |

后端公开接口没有另一个独立 payload 端口；type8 如实保存公开 first_error/local_error/状态，不能当作未公开原生后端 payload。
type9 word0 bits0～3=report/abort/diag/partial，word1=实时 bank_counts，word2=local_error，word3按低字节顺序为controller_state、manager_state、controller_error、evidence_error。
bank_counts：bank0[6:0]，bank1[10:7]，bank2[14:11]，bank3[18:15]，bank4[22:19]。

report_header：cycle[63:0]，policy[127:64]，结果字段[191:128]，local_error[223:192]，bank_counts[255:224]，controller_state[263:256]，manager_state[271:264]，controller_error[279:272]，其余零。
报告握手前的资格、角、命令有效和完整记录同拍保存；下一拍关联保存该握手产生的注册 accept/reject/servo angle，之后 report_full 才置1。
ABORT头：cycle[63:0]、first_error[71:64]、local_error[103:72]、manager_state[111:104]、controller_state[119:112]、controller_error[127:120]，其余零。
report 与 ABORT 独立槽，允许同拍同时保存；本地序号共享递增、不覆盖未释放记录。诊断使用原核心序号。

FETCH：type5 + bank → FETCH toggle；先检查银行非空、没有未释放本地诊断副本；自动逐字校验 bank/seq/index/length/last，先保存后产生精确 ACK，ACK 间留低拍。最后 ACK 才消费核心原 head。本地副本完整后 diag_full=1；失败/中止保留 partial，不伪造 ACK。
ABORT_READ 只终止核心导出 snapshot，原 head 不被强行删除，部分副本保留。

ILA 每个有效采样：data[31:0]，上述meta[159:32]，cycle[223:160]，magic[255:224]=0x49313744；无导出拍全零。触发可选 meta.valid，即 probe0[116]=1，深度1024覆盖最大208字单记录。
先 arm ILA，再 DUMP，再实际导出 CSV。RTL只能知道字已发出，**不知道 ILA 是否武装、触发或 CSV 是否保存**。
RELEASE 是操作者确认已经保存的动作：report须先DUMP 0/1/2/3/4/6，后端ABORT须7/8，diag须5（零字错误副本可在ABORT后直接释放）。type9不需要RELEASE。DUMP可以重复。

## 错误码

controller：01冲突/保留位；02忙时WARM；03 STOP拒绝运动操作；04 COMMIT条件/配置非法；05 START条件不符；21身份绑定前过早输出；22上下文不一致；23 ARM前过早输出/manager错误。
evidence：31诊断记录协议异常；32冲突动作；33忙/选择非法；34无有效字；35 FETCH条件不符；36银行为空；37无可DUMP记录；38未输出完毕/未满足RELEASE；39序号耗尽。
错误码保留最近错误便于诊断，不冒充原生 first_error。原生首错字段另存。

## 时钟、复位、约束及未测

复用项目 `sound_servo_clock.sv` 官方7-series primitives：50→96→61.44 MHz，两级MMCM，锁失异步复位、三拍同步释放。VIO/ILA/控制/算法/舵机同域，没有新命令CDC。PWM物理开门仅在内部低相完成，冷复位立即关门。
水平电气360°/复位180°，垂直220°/复位130°；物理引脚默认低，得到一次真实运动许可后才开启。STOP不关已开启PWM门；后续观察模式保留已有位置。
引脚文件 `i17_vio_pins.xdc`。CDC文件 `i17_vio_cdc_post_synth.xdc` 仅 implementation 使用，只含四条精确输入→首级 D 例外。C-XDC-003 已移除 XDC 内不受支持的循环及条件检查；实际完整工程综合后必须另核四个唯一 meta cell、ASYNC_REG、四个唯一 D pin 和 report_exceptions 覆盖。当前实际网表对象尚未确认，不声称 XDC 自带自动守卫，不能放宽为全局 false path。当前约束快照见 XDC-REPAIR-3-SNAPSHOT.json。
只有sys_clk20ns；MMCM相关时钟自动派生，无异步组。PDM引脚到4个首级D窄例外，下游正常定时；不伪造input_delay0、不切PDM输出路径。
现有转接图支持LR=GND；实装一致性未核。IM73D122V01 tDV最大100ns，phase9链路实际在PDM下降后8个aclk=130.208ns采首级，剩约30.208ns需覆盖外部/IO/setup/jitter；**外部时序UNVERIFIED**。
本批仅语法编译；完整官方IP展开、功能仿真、资源、综合、布局布线、STA、bit/LTX匹配、实板行为均 NOT RUN。独立验证/复核及后续用户GUI入口另批完成。
没有MMIO、IRQ、DMA或软件ABI改动。没有功耗验收要求（NOT APPLICABLE）。
