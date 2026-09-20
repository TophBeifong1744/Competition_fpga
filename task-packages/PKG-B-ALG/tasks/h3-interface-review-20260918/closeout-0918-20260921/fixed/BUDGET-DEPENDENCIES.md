# 每帧依赖、操作量与缓存生命周期

适用固定提交 `fe67547635ff254f9f91c7f917e8dedb6daf3363`，N1024/H512/48kHz/4通道/6对。来源：父 `SCHEDULE.md`、checkpoint `H3-ALGORITHM-CONTRACT.md`、FG、integer_gate、PH、`h3-complete-20260918/source/budget.py`，代号见 [统一表](FIXED-CONTRACT.md)。下列操作计数是算法计数，不是时钟周期；100MHz是配置值，不是实板完整链时钟验收。

## 依赖与不能共用的原因

同一帧完整PCM → 两路计算：

1. gate：四路均值 → 去均值 → Hann → 4 FFT29 → 固定4适配 → bins7..72功率 → 四路gate状态。
2. DOA：原PCM → Hann → 4 FFT29 → 固定4适配 → 等四通道频谱/错误状态 → 六对互谱/PHAT → 每对补谱/IFFT25 → 六对lag → DOA/跟踪。
3. gate与方向结果必须绑定同一session/frame/config，汇总全部算术、TLAST、最终status后才可原子提交。DAS按方向实际可用时间和TTL使用控制，不回填到已输出PCM。

在实数理想式中 `FFT((x−mean)*w)=FFT(x*w)−mean*FFT(w)`，Hann频谱并非只有DC，不能只丢DC便认为共享成立；这里均值、窗乘、逐级FFT均有量化，公式也不保证逐码等价。新gate还使用不同频带7..72；原DOA是7..85。因此按现有候选最坏 **8 FFT+6 IFFT**。PHAT无效可跳过相应IFFT，但上界仍6；研究方向计算不因gate关闭跳过，不能将关闭概率用于WCET。若未来复用FFT工作空间，它是串行资源共享，与复用变换数值结果是两件事。

## 操作账本

| 阶段 | 每帧/每hop操作量 | 说明及尚缺 |
|---|---:|---|
| 均值/去均值 | 4×1023=4092加，4次RNE /1024，4096减 | 加法数按首元素初始化；软件sum从0起的实现可能多4次。读取/地址成本另计 |
| 两路Hann | gate4096+DOA4096=8192实乘、8192次RNE >>17 | 固定ROM读8192次；DOA饱和计数，不得把gate居中窗夹成S24 |
| 8前向+6逆向 | 每1024点radix2有512×10=5120蝶形，最多71680蝶形 | 朴素每蝶形4实乘、6加减→286720实乘、430080加减；另复乘2分量RNE+输出4分量RNE/蝶形。仅描述FG通用循环，不是AMD内部运算/DSP数，特殊twiddle优化不先扣 |
| 29→25半谱适配 | 8×513×2=8208分量RNE/限幅 | 输入8条前向；每帧统计所有状态 |
| gate功率 | 4×66=264复bin，528平方乘，264 re²+im²加，4×65=260归约加，4次归一化RNE整除 | 分母ROM平方和可预先冻结；实际stage每帧重算，不把软件优化假设当硬件。乘2×1024×2^34可精确左移45；除法/倒数方案需证明RNE |
| gate判决 | 4路×2门=8比较，两组三路计数、饱和到3的状态转移 | threshold乘4保留U66，配置/背景校准载入成本未给上界 |
| 当前互谱 | 6×513=3078复bin；12312实乘、6156加减 | 当前软件全部半谱先算；带内仅6×79=474是稀疏硬件候选，不能直接替代现行计数 |
| 当前mask | 3078×2=6156平方乘、3078求和；6×79最大值候选及带内相对mask | 最多474次2500×square比较；Python短路具体次数依数据变，硬件上界按带内总数 |
| PHAT归一化 | 最多474保留bin；每bin1宽整数sqrt、1 LUT查表、2轮Newton（4实乘）、2输出实乘及RNE | normalize再次算re²+im²（最多948平方乘+474加）；bit_length/指数移位也须算。所有硬件延迟 null |
| 补共轭 | 每有效pair拷513复bin，镜像511复bin并虚部取负 | 最多6对；若流式做，不宣称完全无搬运 |
| lag | 4边×13+2对角×17=86搜索点；6次插值除法（分母非零时）+6次margin除法 | 另需隔开相邻峰的second搜索；并非只有6次除法。比较实现的准确比较次数取决于搜索/初始化策略 |
| DOA/角度 | ≤6有效pair的LS/残差；2次xy除法、≤6次predicted除法，24步CORDIC，1次角度RNE | determinant为0、pair不足是早退；真实部署算术内部宽度/周期待定，不把Pythonfloat初始化常量计成硬件 |
| 单方向DAS/hop | 4×512=2048路插值；直接双权重形式4096实乘，四路和及512次RNE /16384、饱和 | 两方向同时计算至少4096路插值/8192实乘；淡变、单麦混合另加。迅速再转向可能残留多bank权重，不能默认“永远最多两beam” |
| 传输/控制 | 原始32B组=1536000B/s；PCM int32=768000B/s；单声道int32=192000B/s | 输入含ID/flags不能只算PCM；DMA复制、cache维护、描述符、仲裁、CDC、输出背压另列 |

14变换若全部以复数32位槽内存物化，每变换1024×8B×读写2=16384B，共229376B/帧，93.75帧/s即21504000B/s。它仅为一种外部物化方式的搬运算术，既不是全部DDR带宽上界，也不能假定每种IP都这么访问。均值两遍扫描和两路窗均需另审读端口/缓存命中；带宽准入要求最坏服务延迟与端口冲突证据。

## 时间预算：已知算术不等于WCET

| 项 | 值/证据等级 |
|---|---|
| 每hop整数周期限（100MHz配置） | floor(100000000×512/48000)=1066666 |
| 历史前向槽、逆向槽 | 7366、7406周期；来自不同历史核/测试调度，不是新调度器验证 |
| 8×7366+6×7406 | 103364周期，算术1.03364ms |
| 与hop的算术差 | 963302周期；不是“剩余可用算力”或安全余量证明 |
| Tgate（均值/窗/功率/状态） | null |
| TDOA-window / TPHAT / Tlag / TDOA / TDAS | null / null / null / null / null |
| Tcopy / Tconfig-status / Tstall / TCDC / Toutput | null / null / null / null / null |
| 完整 Ttotal / 端到端延迟 / 实际资源 | null / null / null |

可审公式：`Ttotal = 8*Tfft + 6*Tifft + Tmean + Tcenter + Twindow_gate + Twindow_doa + Tadapter + Tpower + Tgate_state + Tphat + Tlag + Tdoa + Ttracker + Tdas_mix + Tcopy + Tconfig_status + Tstall + TCDC + Toutput`。每项须说明是否已经含在IP槽中以防重复计算，但在证明前不能删项。并行化要换成实际资源约束下的关键路径和服务上界，不能直接将串行和减去“可重叠”时段。

gate连续3帧最早收集2048样点=42.6667ms；原tracker连续5帧收集3072样点=64ms；若gate开后才开始累计tracker还会更晚，必须核对状态机。固定8样点、480淡变、9600 HOLD不是处理WCET。这些时延不能互换或当完整链限值。

## 缓存与释放屏障

| 缓冲（32位分量槽预算） | B | 获得→释放、不能覆盖的时刻 |
|---|---:|---|
| 四路双帧PCM | 32768 | FILLING→两路gate/DOA全部读完；保留512重叠；不得尚有一消费者就释放 |
| Hann只读ROM | 4096 | 整个profile生命周期；变更须新配置身份 |
| DOA四路半谱 | 16416 | 各路完成且最终status已关联→六对全部完成其频谱读取；不能只等首对完成 |
| gate四路半谱增量 | 16416 | 各路FFT/status→该路功率及帧错误汇总完成；可流式缩减只是未来候选，当前不扣 |
| 单对PHAT半谱 | 4104 | normalize/mask完成→完整补谱消费者接受；同一对错误状态一起保存 |
| 单对IFFT复数缓存 | 8192 | 补谱开始→逆变换消费和最终状态齐；若和工作区共址须读写顺序证明 |
| 单对实相关 | 4096 | 逆变换输出→lag和margin全部提取且status归属明确 |
| 四路10点音频历史 | 160 | 跨hop维持；断流/重启重置；只是候选小历史，不能涵盖任意重定向bank |
| 单声道hop双缓冲 | 4096 | PRODUCING→外部消费者实际消费完；无界ready不能靠两槽吸收 |
| DMA两槽含guard | 16128 | CPU_OWNED复制到算法自有缓存后才能FREE；不得FREE后仍留源指针 |
| 指数/描述符预留 | 1024 | 帧创建→提交/取消及消费者释放；只粗预留，非ABI大小 |
| **列举合计** | **107496** | 父91080+16416；未复用、未映射，不是实际BRAM/DDR占用 |

尚未列全：FFT/IFFT IP内部RAM、twiddle、PHAT LUT/流水线、队列/CDC、PS heap/stack、cache对齐、DAS多bank、输出设备/驱动缓冲。107496B因此不是保守的全系统内存上界，仅是列举项未复用和；实际所需内存仍 `null`。

A须交付内存地址/端口/所有权表及最高同时存活量；只有证明“gate功率和所有相关状态结束”在“DOA覆盖相同工作区”之前，才允许扣gate临时空间。串行FFT共享同一核仍需解决29位前向与25位逆向的静态IP宽度；双核/统一宽度重新验证由A决定。

## 一次性交A的依赖闭环

1. 选择profile及确切XCI/wrapper/ROM，方向位、SCALE_SCH、TDATA/TUSER/TLAST/status含义、传输字宽。默认reference25保持至正式决定。
2. 确定PS/PL划分、宽除法/sqrt/CORDIC流水线和仲裁，提供逐阶段有限周期上界与真正调度表。
3. 帧/状态队列深度、满队列策略、最坏DDR/cache/ready服务、CDC/复位协议和所有权证据。
4. `activity_profile_id/background_calibration_hash/band_activity/speech_present/target_identity` 的ABI及错误原子提交；后两者仍unknown。
5. 按确切版本提供IP/RTL/集成仿真、资源/时序/实板证据。A工程操作遵循AGENTS，本文不创建或修改one，不自动执行综合/实现。

机器可读的算术结果见 [budget.json](checks-02/budget.json)，所有未知上界保留JSON `null`。
