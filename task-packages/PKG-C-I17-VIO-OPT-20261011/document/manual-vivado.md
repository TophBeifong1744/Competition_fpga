# A/B 手动重建本候选的操作单

这份操作单用于复现和优化前的工程接入；不要求 C 重做文件核验，也不下载板卡。使用 Vivado **2025.2**、**xc7z020clg400-1**。本包不含新导入脚本。

## 1. 新建独立 RTL 工程

1. 将仓库放到较短本地路径，打开本包。新建 Project，名称可用 `i17_vio_opt`，选择 RTL Project。
2. Project location 选本包 `project/par`，取消 **Create project subdirectory**，最终工程应为 `project/par/i17_vio_opt.xpr`，数据库同级。不要覆盖 C 正在运行的旧工程。
3. 目标 Part 选择 `xc7z020clg400-1`，Target Language=Verilog，Simulator Language=Mixed。

## 2. 添加 Design Sources（36 个 RTL）

Add Sources→Add or create design sources→Add Files，按 `project/script/src_list.txt` 加入 `project/rtl` 下准确36文件，可直接对6个分类目录多选；不要将整个包递归作为源目录。`.sv` 为 SystemVerilog，`.v` 为 Verilog，Library=`xil_defaultlib`。不添加 `simulation`、`evidence` 中的旧源/日志，不添加旧 sound_servo_burst_top。

设置 `i17_vio_board_top` 为 Top。原生综合实际读入顺序已存在 `project/project-settings.json:synthesis_source_order`，其中 `doa_math_pkg.sv` 必须先于引用该 package 的后端；GUI 自动编译顺序更新后检查。

添加 `project/data/hann-u18f17.mem` 为初始化数据。Settings→General/Source Management 的顶层 Parameters/Generics，设置 `HANN_FILE` 为这台机器上该 MEM 的**完整绝对路径**，使用正斜线并保留字符串引号。例：仓库位于D:/ss时，填写本包MEM的实际D:/ss/...路径；不能照抄旧C:/Users/hsc路径。原始RTL默认相对路径是历史布局，不能仅靠默认值运行。

本候选仅覆盖 HANN_FILE；无 Verilog defines 或 include目录，项目 XPM_LIBRARIES 为 XPM_CDC、XPM_MEMORY。保持其他 RTL 参数默认值，不设置无依据的 SERVO_CONFIGURED/SIM_FIXTURE 全局参数。

## 3. 用官方 IP Catalog 创建四个 IP

**不要直接导入 `project/ip/reference-only` 后点 Generate。** 四个原 XCI 都携带 `../../../../i17_live_loop.gen/...` 输出路径。它们只供身份和参数对照；新机器是否能通过复制自动重定向尚未验证。

在新工程 IP Catalog 中创建下列四个模块，名字必须完全相同，保存到当前工程受管理的 `.srcs/sources_1/ip/`。按下方参数和 `project/ip/config/*.json` 对照。官方GUI未暴露的参数保持相同版本默认并核新XCI；若无法匹配，记录具体差异，勿手改生成文件或升级版本。

| 模块名 | 官方 IP / revision | 主要配置 |
|---|---|---|
| ss_fft29 | Fast Fourier Transform9.1 /15 | 单通道、1024点、Radix2 Burst I/O、定点输入29位、相位因子24位 |
| ss_ifft25 | Fast Fourier Transform9.1 /15 | 与上项相同，输入25位；变换方向由现有包装的运行时配置决定 |
| i17_board_vio | VIO3.0 /27 | 输入4组64/64/32/128位，输出4组32/160/96/32位，输入activity关闭，输入同步开启 |
| i17_board_ila | ILA6.2 /19 | Native、1组256位probe、深度1024、probe类型0、match unit1、输入流水0、advanced/trigger in/out关闭 |

FFT两核还需：scaled、convergent rounding、Non-Realtime、Natural Order；ARESETn启用、ACLKEN关闭；XK_INDEX和OVFLO启用；可变变换长度/CP insertion关闭；data/phase/reorder memory=Block RAM；hybrid=false；complex multiplier=use_mults_resources，butterfly=use_luts；super sample1；目标频率100、吞吐50。这些是原 IP 配置值，主逻辑实际时钟仍61.44MHz，不能把100误作板级输入时钟约束。完整29项见各config JSON。

VIO输出初始化值必须为：

| 输出 | 位宽 | 初值 |
|---|---:|---|
| probe_out0 | 32 | 0x00000004（STOP=1） |
| probe_out1 | 160 | 0x0000000000000001000000000000000100000001 |
| probe_out2 | 96 | 0x000400000000000000000000（仅观察） |
| probe_out3 | 32 | 0x00000000 |

精确参数表：[IP参数明细](ip-parameters.md)。`config/*.json` 同时保留全部 component 参数及原 model/project/runtime 字段；输出路径和运行时标识要属于新工程，不复制旧 OUTPUTDIR。确认新 IP source/output 路径都在当前 project/par 工程范围后，分别 Generate Output Products，选择 Out of Context per IP。不要把旧机器的stub或DCP当正式替代品。

## 4. 添加 Constraints Sources（2 个 XDC）

Add Sources→Add or create constraints→加入 `project/sdc/i17_vio_pins.xdc` 和 `i17_vio_cdc_post_synth.xdc`。

- pins：Used in Synthesis、Used in Implementation 都勾选。
- cdc_post_synth：只勾选 Used in Implementation；取消 Synthesis/Simulation。
- 不导入旧工程XDC或另加全局false_path/异步clock group。物理端口共11个，唯一板级时钟sys_clk为20ns；MMCM相关时钟由Vivado推导。

## 5. 展开及有界综合

先 Open Elaborated Design，确认顶层i17_vio_board_top、11个物理端口和四个官方IP实例，无 unresolved module/IP blackbox 错误。正式 OOC 黑盒在主综合前由官方输出/检查点关联，不能用诊断stub掩盖未生成IP。

开始综合前先决定是否原样复现；本源已出现长时间 Timing Optimization 和 STOP组合环告警。建议A/B先处理有明确依据的结构后再跑。若运行则保存：新XPR、原生主/IP runme.log、实际生成的综合Tcl、综合结束utilization/timing/DRC报告。没有完成就记录中止阶段和完整日志，不能写PASS。

Number of jobs 只控制独立run并行，旧会话选8；协调者14:43读取GUI journal确认新会话launch_runs -jobs16，当前主日志仍记录maximum2processes。本包不更改线程参数。不得把jobs32当单个综合32核证明。

下一步实现/下载须针对新候选重新审查重大时序问题与真实机械条件，本次源交接不授予板卡动作。旧原生 `evidence/synthesis/*.REFERENCE_ONLY*` 和 `.tcl.txt` 仅供比较，不作为重建入口执行。

## 可选：已有 C 单元测试的复用

`simulation/tb` 仅在 Simulation Sources 中使用，逐项选testbench为top，不能一起作为产品顶层：tb_control对应i17_vio_control，tb_evidence对应i17_vio_evidence，tb_gate_map对应i17_pwm_gate/signed_angle_map，tb_pwm对应motor_drive与simulation/reference/motor_drive_frozen，tb_invalid对应motor_drive。原准确argv、plusargs、退出码和checker标记保存在evidence/tests各run.json中；此批未重跑、未重新验证便携测试入口。完整算法/官方IP仿真不由这些单元测试代替。
