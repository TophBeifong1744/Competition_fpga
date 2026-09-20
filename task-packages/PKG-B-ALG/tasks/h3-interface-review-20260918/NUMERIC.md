# 四路数制与 FFT/IFFT：证据身份分开

**生产最终格式仍未冻结。** 以下给出可执行软件候选的完整选择，不把“候选选择明确”写成“AMD全链已准入”。默认reference25未改。

| 环节 | 本包所引用软件候选 | 实现/批准边界 |
| --- | --- | --- |
| 输入 | signed24符号扩展int32；解释S24F23；四路共用除2^23，仅浮点适配时使用 | 原始整数保持，不能逐通道归一化；48kHz为配置值 |
| 分帧 | N1024/H512，四路同组ID，无窗/无补尾 | 分帧器不加窗，后级只加一次 |
| Hann | 对称N-1定义，U18F17；PCM×系数后RNE右移17、饱和S24并计数 | 系数来自上游冻结模型；应将ROM逐码绑定，非任意新窗 |
| 默认前向reference25 | S25F23，十级各移1，总DFT/1024 | 不由本包替换 |
| 软件前向研究候选 | 窗码精确左移4→S29F27；1024点radix-2，逐级移1、RNE；Q30软件旋转因子 | 7a17edd portable golden，不等同AMD24位旋转因子 |
| 候选回PHAT适配 | 四路全部固定RNE右移4→S25F23；饱和计数并使相关数值无效 | 不是六路研究的最小共同r搜索；四路自适应指数屏障仍未实现/冻结 |
| 互谱/PHAT | 6对(01,02,03,12,13,23)，S51F46；平方和U102；引用phat-fixed-03归一化，PHAT S25F23 | bins7..85；相对mask1/50、最少12；整数开方/除法硬件延迟未闭合 |
| IFFT | 补共轭至1024，S25F23，逆向十级各移1，不额外再除1024 | portable Q30模型与AMD IFFT25归档分开；没有IFFT29准入 |
| lag/DOA | 当前候选lag S18F12；xy S22F20；角度S18F8度 | 优先当前config，不能照抄旧S17Q12；边/对角物理边界整数判定 |
| 跟踪/DAS | 淡变权重U13F12，累加S39F12，输出S24F0；RNE/饱和计数 | 整数软件候选；固定延迟8和480样点淡变不是整机延迟 |

## AMD IP历史配置（复用，不新仿真）

FFT29归档：xfft9.1 rev15，1024，radix_2_burst_io，29位实虚输入/输出、24位twiddle，scaled、convergent_rounding、natural_order、nonrealtime；配置100MHz，forward配置字0x0AAAAB，十级各移1。64位TDATA real[28:0]、imag[60:32]；TUSER[9:0]输出索引，bin1023 TLAST，状态overflow bit0。196/196历史向量覆盖只证明此前前向核输入/配置的归档逐码结论；本次不重跑，也不借作全链证据。

IFFT25配置按归档reference25合同：25位分量、24位twiddle、同一1024/radix-2/scaled/convergent/natural/nonrealtime布局；逆向十级各移1（方向位0，固定1024配置对应0x0AAAAA）。具体硬件配置端口宽度、填充和握手须以实际绑定XCI/wrapper再核对；本包没有把29位IP动态变为25位IP。

阻断：portable Q30与AMD24位twiddle/逐级舍入可能不逐码相同；四路29→25共同指数路线与本候选固定4路线未最终选择；PHAT epsilon随指数的合同、最终硬件开方/除法、整条IFFT/lag/DOA/DAS逐级对照未齐。A不得据此直接冻结生产数制或换默认算法。
