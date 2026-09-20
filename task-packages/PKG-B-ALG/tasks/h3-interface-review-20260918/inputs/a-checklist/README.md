# 9/18 算法接入最小清单

核对日期：2026-09-17。工程实现提交工作执行检查；仅接口核对与实施建议，未修改工程、未批准接入。**先补四路连续流到算法帧的适配，不能把 DMA 包尾直接接作 FFT 帧尾；完整 H3 尚未见准入批准。** 六秒 S1 待 B 诊断，本轮不追加录音。

## 版本与证据入口

本次只读查询远端 main、任务分支并核对本地 Git 对象；未 fetch/切换/重置共享目录。

| 对象 | 固定版本、入口与结论 |
|---|---|
| 本地 HEAD / 查询时远端 main | `02b578c730c539e7fb45e11386567f28ffe7ab71`；本地有其他任务未跟踪工作，保留不动 |
| B 四路跟踪和三路离线音频 | `f364a023830b105e6075d853da83cfd51127cf64`；`task-packages/PKG-B-ALG/tasks/four-channel-track-01/` 与当前 main 无差异。准确批准见 `docs/reviews/four-track-f364a02/REVIEW.md`，发布 `30770f6951a6cb2746a6c35acedb72e7e9e6ae50`。仅离线诊断，不是定点、实时、存在门或 H3 批准；任务原 README 的“待审”是历史时点 |
| B 定点研究与预算 | 上游 `bff45e7bbedab321fc4815e1432f1575c750edc4`，收口 `fdc2d18f2d765cad3223720a85680fd102185039`；`phat-fixed-03/closeout-01/{BUDGET,HANDOFF-TO-A}.md`。用户授权归档不等于格式冻结，见 `docs/reviews/b-fixed-user-20260912/README.md` |
| 四路预算修正及 H3 缺项 | main 上 `task-packages/PKG-B-ALG/tasks/c-board-algorithm-01/H3-GAPS.md`；当前排期以 `docs/phases/2026-09-13-to-10-01/B.md` 为准，不沿用旧包 9/22 日期 |
| FFT29 | `b8c5e87f6cb1054c2684719310f02f36c83ac731` 扩展证据可引用；仅前向核逐码覆盖，不补足公共指数适配、IFFT29 或完整链 |
| 采集 | C1 `88805ee415f137998b59b7cb197f2eeb988d17b7`、E1 `5606e1a9d9a6183ceff7cffc1bb4f8aac44bb79c` 按各自限定批准复用。实际应用现为 S1 六秒留存版本，不能把 E1 在线回收程序与 S1 混称 |
| 本批六秒输入 | `8f708e42caf32c1de6f30726298e3edf0e1970b6`，`batches/background-target-stop-20260917/`，待独立诊断。计时入口 `21c141b223936730c2ce5139624fcedb412adafb` 不因本清单而获批准 |

上述 B 交付有可用模型和局部证据；本轮查到的批准不覆盖完整 H3。B 尚未发布的新材料不推断为已交付。没有重跑原整包研究、FFT 仿真或耐久测试。

## 接口逐项对齐与最小动作

| 接口 | 当前事实 | 下一步具体动作 / 验证点 |
|---|---|---|
| 通道及几何 | DATA1～4 → mic0～3；组内四路同一 ID。mic0 原点，+X 向 mic1、+Y 向 mic3；40 mm 正方形为操作者测量/声明模型 | 保留顺序，不套六麦矩阵；算法使用同一元数据坐标，声源近场记录不是远场真值。先用四路可区分码检查不换列 |
| 原始记录 | 8 个小端 32 位字：`id_lo,id_hi,mic0,mic1,mic2,mic3,flags,reserved`；PCM 为 signed24 符号扩展到 int32；flags[3:0] 对应四路削顶，reserved=0 | 原样解包并保留 uint64 ID、错误/会话信息。不能把头、flags 当 PCM；不能通过 float 保存 ID。B 的浮点适配统一除以 2^23，不独立归一化各路 |
| 帧与包 | Fs=48 kHz；DMA 250 组/包，8000 B；B `audio_frames.py` 为 N=1024/H=512，每个连续有效区间独立分帧、不补尾 | **新增四路重叠分帧适配器**，跨 DMA 包/槽组帧。保留 512 组重叠，输出 frame_id、interval/session、首末原始 ID。DMA TLAST 不传给 FFT；FFT 第 1024 个被接受样点才产生其 TLAST |
| 时序与流控 | AXIS 32 位、TKEEP=0xF、valid&&ready 推进。PDM/CIC持续采样，FIFO 默认1024组；背压不暂停麦克风 | 算法慢不能无限拉低 ready。先复制到有界算法帧缓冲再释放 RX；队列满必须显式无效/溢出并保留原因。接口需给实际最大服务延迟，不能只引用无背压 FFT 时间 |
| DDR/缓存 | RX=[0x01000000,0x01100000)，两槽各8000+64 B，共16128 B；FREE→DMA_OWNED→CPU_READY→CPU_OWNED→FREE；收前 flush/invalidate、完成后 invalidate | 复用所有权与保护区。不保留已 FREE 槽的指针。算法帧缓存单独分配、核对程序/堆栈及所有缓冲区；本轮不改地址或分配。两个4×1024×int32帧数据共32768 B，仅规划容量，不是已获准内存合同 |
| 连续性与错误 | PL sync/overflow 为粘滞错误；PS 检查 DMA、长度、保护区、ID、范围、flags。B 按 clean interval 分帧并重置状态 | 丢号、错误行、重启处截断帧并重置跟踪，不跨段拼接。PS 当前对 clip 计数不自动失败，B 的错误行判定须显式沿用导出/读取器规则；由 B 冻结实时削顶帧接受策略，不能默认 clip=正常 |
| 时钟域 | 采集61.44 MHz；FFT历史预算100 MHz | 若后续 PL 接算法，需明确异步 FIFO/CDC、复位及帧元数据同路传递；不能直接跨域连 valid/ready。当前离线文件桥不涉及新增 CDC |
| 停止与结果提交 | RUN拉低后完整包停止并排空；不同 Run 不保证编号连续；算法方向仅在完整分析帧到齐后可用 | 停止时保留不足1024点的尾部记录，但不伪造分析帧；晚到 FFT/IFFT 状态错误必须使整帧无效，不先发布有效方向后吞掉错误。重启明确新 session/interval |
| 输出/目标存在 | B 的数值候选有效不代表目标存在；`target_presence=unknown`、`direction_accepted=false`。音频为离线 DAS/PC WAV | 复用诊断模型和 golden，不当在线模块。硬件结果包字段/有效期、实际计算延迟、定点 DAS、存在门均待定；不接 DAC，不宣称实时闭环 |

## 数制和预算：可引用什么、不能直接接什么

- PCM S24F23 → 对称 Hann U18F17 → S42 乘积右移17、最近偶数舍入、夹回 S24，再符号扩展 S25。这是已有整数模型合同；**分帧器本身不加窗**，避免重复加窗。
- 默认 reference25：S25F23，前向十级各移1，DFT/1024。FFT29 只是候选：整数窗码精确左移4得到 S29F27；回到 PHAT前须共同指数/舍入。现有研究的共同指数遍历是六路，四路屏障范围与元数据需要 B 明确，不自行缩改算法。
- PHAT有 S51 互谱、U102 平方和、F24归一化研究，输出 S25F23；IFFT25十级各移1，不再额外除1024；峰插值中间量 S17Q12。整数开方/除法硬件延迟、epsilon与指数关系、边界判断/DOA/DAS最终定点合同未冻结。不能拿浮点 Python 或 math.isqrt 当现成 RTL。
- 四路每 hop：4 FFT+最多6 IFFT，不沿用六路6+15。窗口21.333 ms、hop10.667 ms；100 MHz约1066666.7周期/hop。FFT29单核7366周期服务槽仅为历史特定无背压TB，4槽29464周期只作估算，不是整链吞吐。
- 四路 H3-GAPS 的69672 B是列举工作缓存的逻辑合计，不含全部算术、DMA、IP内部RAM/状态，不能当BRAM实现结果。输入纯PCM 768000 B/s；当前含ID/flags的采集记录为1536000 B/s，预算不能漏一倍。
- `4*Tfft+6*Tifft+Twindow+Tphat+Tlag+Tdoa+Tdas+Tmemory+Tswitch+Tstall` 仍缺真实模块上界。B音频候选的22路预计算缓存、零计算耗时、8样点可用延迟和10ms淡化均是离线合同，不是板端预算。

## 可执行顺序与停止条件

1. **现在提交本清单给工作执行/B**：要求完整 H3 给出准确SHA、最终四路数制/异常策略、模块握手与输出包、实际调度/缓存预算。复用上述已有材料，只补差项；不重做采集。
2. **获准后先做一个不含算法决策的四路分帧适配器候选**：从已校验32字节组形成4×1024、hop512帧，附原始ID和区间信息；不改PDM/CIC、DMA包长、默认reference25。先离线/TB逐码对齐 B 的帧索引，再决定PS还是PL实现；不是本轮已实施或获准接线。
3. 该候选最低测试：跨250组包/双槽边界；四路不同码；恰好1024/不足1024/多hop尾段；中途丢号/clip/非法flags；停止重启；输出背压稳定；缓存满不能覆盖未消费帧。预期与 B framing一致，失败保留。**这些是下一任务测试要求，本轮未执行。**
4. 再单独接整数窗→已准配置FFT的前向诊断链，逐码比原 golden 并携带帧状态；PHAT/IFFT/DOA/跟踪/DAS待其合同及准入。FFT29不能自动替换reference25。实际Vivado/Vitis修改仍先由拓芙选工程，再按整阶段操作单执行。

本轮停止于清单交付：没有新代码、工程改动、构建、仿真、时序或板测结论；引用历史限定证据不扩大批准。S1诊断、计时入口复核可并行，不作为本轮重复测试理由。

## 实际工程只读绑定及复核方式

`F:/College/verilog_digital_system/AMD/Competiton/one/one.xpr` 引用 `one.srcs/sources_1/imports/c_adapter/` 中下列文件，SHA-256：

| 文件 | SHA-256 |
|---|---|
| four_mic_top.v | `08b39fd3de26566d98d92e545121621d3f539b861b4ca80fd82b3e3024ff27e5` |
| pcm4_continuous_axis.v | `06772cd7bb97ca2a6a69099d22a294c1d3994cb2496787d44ee0d79664a85a06` |
| F:/College/verilog_digital_system/Vitis/four_mic_endurance/src/continuous/continuous_core.h | `93135b855aa83da07684d1274fa5ad9c55b560eae0f5da1bba0716d4f2fdb92e` |
| 同目录 continuous_core.c | `346697ec817ffe0318b366f0ff8735da90fb534fb773e41545e93d94d05907f6` |

实际执行：Git HEAD/远端引用查询；`git show` 固定B提交文档；`git diff --quiet f364a023830b105e6075d853da83cfd51127cf64 HEAD -- task-packages/PKG-B-ALG/tasks/four-channel-track-01` 返回0；只读检查PS所有权/缓存/校验代码、PL打包/停止状态及上述文件哈希。源代码检查不等于重新确认已加载bit/ELF；本轮无需下载。
