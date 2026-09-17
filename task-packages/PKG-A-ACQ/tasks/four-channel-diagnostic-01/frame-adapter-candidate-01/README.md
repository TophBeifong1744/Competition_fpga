# 四路 1024/512 重叠分帧独立候选

2026-09-17 工程实现候选，供工作执行检查和后续 B 接口核对。**未修改实际 `one`、Vivado BD、Vitis 应用或冻结录音；未接 GCC/DOA，未上板，也未作综合/时序验证。** 本目录不代表 H3 准入或正式 M1。

## 最小合同

- 输入是一组已校验的 H1 四路记录，而不是 32 位 DMA 原始字流：`uint64 原始 ID`，按 `mic0,mic1,mic2,mic3` 排列的四个 signed24→int32 PCM，32 位 flags 和 reserved，外加上游完整性/错误码。输入方必须能遵守 `s_valid && s_ready`，例如离线或 DDR 读取器。**不能把不可暂停的 PDM/CIC 直接接进来。** 若未来接入实时采集，须另证 FIFO/CDC、最坏背压和缓存所有权。
- 采集 DMA 一包 250 组、每组 32 字节。帧长 1024 组、步长 512 组；DMA 包界与分析帧界没有整数对齐关系。分帧器不使用/产生 DMA 包 TLAST，`m_last` 仅在分析帧第 1024 个**被接受**的输出拍为 1。包长/TLAST/8 字记录解包由输入侧校验，本候选**没有**替代该校验。
- 输出每帧 1024 个四路组、原始 ID 和逐组 clip flags，同时带 `session_id,frame_index,interval_index,first_id,last_id,reset_before,sample_index`。不加窗、不缩放、不把原始 uint64 ID 转 float。FIFO 数据按 `{mic3,mic2,mic1,mic0}` 连接，是 Verilog 总线位序；`m_pcm[31:0]` 仍是 mic0。
- `s_integrity_error` **或非零 `s_error_flags`**、编号不连续、非法 flags/reserved、signed24 范围错误均发出可握手的诊断事件，并截断当前有效区间。失败组不纳入帧，不补样或重新编号；事件保留出错原始 ID、上一 ID、原 flags、上游错误码与未成帧新组数。合法 `flags[3:0]` 按组保留，**并不替 B 决定削顶帧是否可用于算法**。
- 停止请求不截断正在输出的完整帧；全部已组成帧排空后发出停止事件。尾部不足 1024 组不补零为帧，事件报告尚未成帧的**新增**组数（已输出帧保留的 512 组重叠不重复计数）。重启必须有新的 session 握手，帧序号/区间从零开始；不同 session 不拼接。

| RTL 端口 | 含义 |
|---|---|
| `start_valid/start_ready`, `start_session_id` | 新 session，上一 session 和事件排空后才接受 |
| `stop_valid/stop_ready` | 请求边界排空；握手后不再接收输入 |
| `s_valid/s_ready`, `s_id`, `s_pcm`, `s_flags`, `s_reserved` | 一拍一组、握手才推进；输入必须可背压 |
| `s_integrity_error`, `s_error_flags` | 输入链检测到的同步、DMA、溢出等错误及其来源编码 |
| `m_valid/m_ready`, `m_*` | 帧样本流，1024 拍/帧，输出背压时全部字段保持稳定 |
| `e_valid/e_ready`, `e_*` | 停止或异常事件；事件背压时保持稳定且不接收新组 |

错误事件编码：1 停止、2 上游完整性、3 编号中断、4 非法 flags/reserved、5 PCM 范围。原始 H1 flags 中只有低四位是四路 clip；异常细分的硬件来源由 `s_error_flags` 随事件带出，实际枚举需与未来输入桥约定。

## 实现与复跑

- RTL：[pcm4_overlap_framer.v](rtl/pcm4_overlap_framer.v)；独立模型：[framing_model.py](model/framing_model.py)；自检：[test_framing_model.py](tests/test_framing_model.py) 与 [tb_pcm4_overlap_framer.sv](sim/tb_pcm4_overlap_framer.sv)。这不是实际工程的替换文件。
- Windows PowerShell 在本目录执行 `./reproduce.ps1 -VivadoBin F:/AMD/2025.2/Vivado/bin -RecordName <新的记录名>`；每次必须使用新记录名，脚本拒绝覆盖旧证据。可用 `-PythonExe` 指定 Python。脚本运行 Python unittest、XSim 2025.2 的 xvlog/xelab/xsim，记录原始日志、退出码判定和源文件 SHA-256。
- 当前最新复跑：[run-20260917-03](evidence/run-20260917-03)：Python 6 个测试方法均通过（含多个边界/错误子例）；XSim 编译、展开与仿真通过，实际输出 `frames=7 events=9`。前两次 [run-20260917-01](evidence/run-20260917-01)、[run-20260917-02](evidence/run-20260917-02) 保留为修订前历史；不是本轮最新结果。运行机的 XSim 显示 `v2025.2`。源码哈希见最新目录的 `SHA256.txt`。

验证覆盖：0/1023/1024/1535/1536/2048 组与无补尾；十个 250 组块中跨包产生帧；每帧逐组四通道码值、原始 ID、512 组重叠和帧尾；大于 `2^53` 的 ID（模型）；clip 保留；上游错误（包括只有错误码而错误位未拉高）、编号缺口、非法 flags 与范围错误（模型）；输出/事件背压稳定、停止排空和重新启动（RTL TB）。RTL TB 中第一 session 为七个完整 250 组块，停后报告 214 个未成帧新增组。**TB 没有直接驱动/检查 DMA TLAST；这仍属于现有采集/解包链的责任。**

## 待核对和停止点

本候选使用约 `1024×(128+64+4)=200704` 位的样本存储，**只是 RTL 逻辑容量，不是 BRAM 用量或时序结论**。输出一帧时输入背压；对真实 48 kHz 源必须另有缓存、最坏延迟预算及溢出可观测路径。本轮没有这些实现，也没有与 B 最终 H3 模块端口、削顶策略、FFT 时钟域或资源预算绑定。B 的准确接口/准入到来后，先核对是否仍采用此组级握手与帧元数据，再由拓芙决定是否修改实际 `one`。Skill 复核独立，不受本候选代替。
