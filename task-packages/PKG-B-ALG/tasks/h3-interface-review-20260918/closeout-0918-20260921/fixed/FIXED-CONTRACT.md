# 9.18 完整定点合同统一表（整理完成，生产格式未冻结）

固定来源：`fe67547635ff254f9f91c7f917e8dedb6daf3363`。本页是独立工作材料，供原对话汇入既有任务包后交 A；不是完整 H3 签字。只引用该提交内文件，不以文件名日期推断实际执行日期。

## 读表约定与准确来源

S/U 表示有符号/无符号总位宽，F 表示小数位；PCM 码单位时输入为 S24F0，满量程归一化时同一码为 S24F23。二者是单位解释差异，不是额外移位。NPZ 的 int64/uint64 是容器，不能当作部署总线或内部寄存器宽度。Python 宽整数节点尚无硬件宽度证明的填 `null`；表中“保守容纳”也不是资源批准。

以下路径均相对于只读源根 `F:/NUEC/review-worktrees/algorithm-closeout-20260923/`，完整字节身份及函数起止行见 [source-identities.json](checks-02/source-identities.json)、[code-anchors.json](checks-02/code-anchors.json)。

| 代号 | 准确出处 |
|---|---|
| CP | `task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923/` |
| FG | `task-packages/PKG-B-ALG/tasks/h3-complete-20260918/source/fixed_golden.py` |
| PH | `task-packages/PKG-B-ALG/tasks/phat-fixed-03/phat_model.py` |
| T-old | `task-packages/PKG-B-ALG/tasks/h3-complete-20260918/tests/test_h3_candidate.py` |
| T-new | `CP/source/test_candidates.py`；`CP/source/test_repair.py` 是复现工具测试，不能替代数值覆盖 |
| G-old | `task-packages/PKG-B-ALG/tasks/h3-complete-20260918/evidence/run05/golden/` 的 `golden-stages.npz`、`golden-summary.json`，同级上层 `golden-check.json` |
| G-new | `CP/evidence/golden02/` 的八个 NPZ、`summary.json`、`SHA256.json`；每段一帧15数组，合计120数组 |
| N/I/S | `task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/NUMERIC.md`、`INTERFACE.md`、`SCHEDULE.md` |

本轮检查冻结数组与其清单的 dtype/shape/码字节哈希，未重新生成这些数组。以下“已有测试”均为来源阅读/证据复用，未在本轮重跑。最小增量验证编号见 [VALIDATION-PLAN.md](VALIDATION-PLAN.md)。

## 统一逐级表

| 阶段 | 输入 → 输出位宽与F | 缩放、RNE、溢出/无效行为 | 准确代码与 golden | 已有测试/证据 | 实际缺项及下一动作 |
|---|---|---|---|---|---|
| Hann（DOA） | S24F0 × U18F17；全宽乘积保守 S42F17 → S24F0（归一化输出 F23） | N=1024，对称 N−1；`round` 生成系数，乘积 RNE >>17，S24 饱和计数。只加一次窗；输入范围/形状检查 | FG:48–89 `rne_div/rne_shift/saturate/hann_u18f17/window_pcm`；G-old `hann/windowed`；G-new `hann/doa_windowed` | T-old `test_signed24_endpoints_window`、正负半偶舍入/饱和；G-new 八探针 | ROM 逐码绑定及乘积 RTL 尚未对照；不能把浮点 cos 运行时再生成视为冻结硬件 ROM。B1 固定 ROM 哈希/量化节点；A1 绑定实际 ROM、流水线 |
| gate 均值与窗 | 1024×S24F0 → S34F0和 → RNE /1024 得 S24F0均值；差 S25F0；×U18F17 → S43F17 → S25F0 | 去均值后不能夹回 S24；此路窗 RNE >>17，无 S24 饱和。Python int 求和/乘法，weighted 用 int64 容器 | `CP/source/integer_gate.py:7–16 stage`；G-new `pcm/mean/centered/hann/windowed` | T-new `test_integer_dc_zero_and_width`（常量0及±端点）；八探针 | 非恒定满幅、均值半码、居中差超过S24的边界未覆盖；B1 做纯整数边界，不新增声学模拟 |
| gate 去均值 FFT | S25F0精确<<4 → S29F4（同码满量程F27）复数 → S29F4，数值为DFT/1024 | portable Q30 twiddle；先复乘分量 RNE >>30，再每级蝶形 RNE >>1，共10级；每级饱和计数。不是一次最终 /1024 的等价逐码实现 | `integer_gate.py:17–21`；FG:101–136 `fixed_fft`；G-new `fft29`和十级 `stage_sha256` | 八探针及常量DC消除；未借 AMD FFT29 归档为此路通过 | 居中输入域、十级内部全幅范围、Q30 ROM对应尚缺；B1/B2；A1/A2 做所选IP映射。不能自动共用DOA变换 |
| DOA FFT（保留默认/候选） | 默认 reference25 S25F23；候选 S24F0窗码<<4 → S29F4（归一化F27） → S29F4 | 同 FG portable 逐级移1；DOA 未去均值。默认 reference25 不改；仅窗后带保护位的29位候选明确，不代表默认已替换 | FG:101–136及`full_chain`；`CP/source/golden.py:27–31`；G-new `doa_fft29`；G-old `fft29`；默认AMD模型入口 `phat-fixed-03/integration/chain.py:24–53` | G-old限定软件、历史AMD前向FFT29归档；证据身份见下表 | Q30与AMD24位twiddle不能互借逐码通过；生产profile待A选择；B2/A1。FFT29归档覆盖不证明新gate全域 |
| 29→25 | S29F4 → S25F0（归一化 F27→F23）；取513半谱 | 固定 RNE >>4；饱和到S25并计数；饱和/上游IP溢出使帧无效。这里没有四路共同指数搜索 | FG:139–146 `adapt_fft29_to_s25`；`integer_gate.stage`；G-new `fft25/doa_fft25`；G-old `fft25_half` | 原逐级golden及八探针，不等于转换边界覆盖 | 固定4只是候选；共同指数路线未实现/冻结，不把六麦研究搜索搬成四路默认。B2 半偶/端点/溢出传播；A1裁决profile；若指数改变，PHAT epsilon标度重做 |
| gate 频带功率/状态 | S25F0半谱，bins7..72（66）；平方/和宽无符号；分子 U104F0，分母 U45F34码值；输出 U64F0 原PCM码²；阈值比较 U66 | `P=RNE(2*sum(re²+im²)*1024*2^34 / sum(hann_code²))`；分子/输出显式范围断言。noise取浮点标定ceil，floor≥512²；on≥4n/off保持≥2n；至少3路，attack/release饱和3，invalid立即reset | `integer_gate.py:22–31,33–54`；G-new `band_power`及summary中的分子/分母/overflow；噪声码[984271,1040622,965554,946106] | T-new整数开启边界与invalid；八探针，重复同帧3次是状态探针。浮点与整数功率约0.389%最大差异不等于等价 | U64极限阈值乘4、2/3路、关闭边界、reset优先级与非DC全幅尚缺；B1/B3；A2常数除法替换须保持RNE。speech_present、target_identity仍unknown |
| 互谱/PHAT保护 | 两个S25F23 → 互谱S51F46；模平方保守U102F92；输出S25F23；mag_frac=24，reciprocal F30；开方及Newton内部部署字宽 null | `Xi*conj(Xj)`；513点全算互谱。带内7..85共79，`square>0 && 2500*square>=max_band_square`；≥12点才有效。非零整数互谱幅值≥1；epsilon是`2^26/10^15`互谱码单位，不可直接设0泛化。sqrt nearest整数（精确比较），256项倒数LUT+2轮Newton，输出RNE；越S25抛异常，IP overflow整对无效 | PH:10–71 `rne_ratio/sqrt_rne/reciprocal/cross/normalize/mask_for/phat_pair`；G-new `phat/mask`，G-old `phat/phat_mask`；epsilon常量在PH:5 | 旧PHAT研究/AMD integration证据与run05逐级golden；八探针，仅覆盖实际保留bin | `square<<48`、2500乘法、倒数迭代全部不能收窄为64位；由U102保守推导开方输入U150，乘2500容纳U114，尚非最小实现。B4补零/11–12bin/相等mask/负半偶/异常传播；A2给有限延迟/内部字宽 |
| IFFT/共轭补全 | 513×S25F23复数 →1024×S25F23 → S25F23相关 | `k=1..511`镜像共轭，DC/Nyquist保留；逆向十级各移1，已是标准IFFT，不能再/1024。portable每级饱和标志；CP golden汇总任一IFFT overflow后把全部pair置无效 | FG:157–165 `conjugate_complete`、101–136 `fixed_fft`；`CP/source/golden.py:42–49`；G-new `ifft`（只存实部）和ifft_flags；G-old `ifft_real` | reference25历史AMD 16 IFFT数学对照；portable G-old/G-new是不同证据线 | 一般S25最负虚部取负可能超S25，当前PHAT有效幅度受限，但补谱函数本身没检查；DC/Nyquist虚部与虚残差、overflow/晚status传播待B4/A2。旧FG.full_chain不集中拒绝IFFT flags，不能作为生产错误闭环；当前CP增加集中无效化，也不是RTL证明 |
| lag/亚采样插值 | 1024×S25F23相关 → S18F12 tau；delta限±2048（±0.5采样）；margin F15，部署总宽 null | 边长40mm，a=1920/343采样；边/对角严格整数物理界。搜索±ceil界：13/17点，先序负lag胜平局。抛物线 `(L−R)*2^11/(L−2C+R)` 分母翻正后RNE；0分母delta=0；最后按精确Q12物理界拒绝。margin与max(abs(peak),1)相除，仅诊断，不用于valid | FG:37–45、168–193；G-new summary `pairs`；G-old summary/boundary冻结值 | T-old正负lag、range reject、边/对角两符号物理边界及插值 | 中间差/乘/除宽度、全平/等峰/0分母/负峰margin语义无统一硬件合同；B5补纯相关码向量，A2除法与valid。不得私加margin阈值 |
| DOA/置信度/角度 | S18F12有效tau ≥3对 → xy S22F20候选，平方 norm F40/residual F24，角 S18F8度；中间寄存器宽度 null | 固定六对01/02/03/12/13/23及方形几何，整数LS RNE；det=0或<3对拒绝；残差平方≤n*(0.5*2^12)²，模平方在round(0.1*2^20)²..round(1.3*2^20)²。24步CORDIC常量角F16，内部`>>i`是有符号算术移位（非每步RNE），最终RNE→F8。方向为阵列指向声源，+X→+Y正 | FG:196起 `doa_q20`、`_CORDIC_ATAN_Q16/atan2_q8`；G-new summary `doa`；G-old DOA；T-new三角度符号测试实际是浮点diag，不是全整数符号证明 | T-old `test_rank_deficient/test_invalid_pairs/test_positive_x_geometry`；旧跟踪五帧/扇区/HOLD限定证据 | xy格式是草案，Python未显式限宽，拒绝前中间范围未证明。B5确定界/阈值等号/全部可达有效对集与CORDIC象限；A2绑定ROM/流水线；残差/模一致不证明目标存在，不能将valid直接接正式direction_accepted |
| DAS/饱和及淡变 | S24F0 × U13F12插值权重；四路和保守 S39F12；RNE /(4*2^12) →饱和S24F0；淡变权重U13F12 | 位置`n*4096-delay_q12`，floor取left，0..4095 frac；越块取零；平均后饱和计数。角F8→delay F12目前使用浮点sin/cos和round，不是整数硬件函数。旧control淡变480样点、固定共同8样点是软件假设；当前新音频是浮点DAS/混合 | FG:326–352、394–495 `delay_q12_from_angle/das_block/_weights_at/causal_audio`；G-new `manual_das`裁两端8点、仅手动；G-old `single/manual/automatic/auto_weights_q12/auto_target_bank` | T-old zero/constant/因果/断流/淡变；run05独立批准只针对软件断流闭环；CP浮点音频18测试中的相关项不证明整数新gate自动链 | 新gate→整数tracker→实时DAS没有统一全流golden；延迟ROM/CORDIC、跨块历史、同时方向数及快速反复切向缓存待定。B6算术/跨块接口增量；A2/A3时序/流接口。声学回退诊断仍由原对话负责 |

## 两条数值证据线不能合并署名

| 证据线 | 准确来源和可复用结论 | 不覆盖 |
|---|---|---|
| portable Q30 | FG及G-old；`docs/reviews/h3-run05-7a17edd/B-REVIEW.md` 准确 `7a17edd2b5408e10608d954f3e7fa11cb62fe34b`：软件断流闭环 LIMITED PASS。G-new为本checkpoint八帧整数探针 | AMD位精确、生产profile、完整新gate整数流、声学性能 |
| AMD 25位 | `fft-bitexact-01/README.md` 与 `compare_cmodel.py`；25位输入输出、24位twiddle；历史6 FFT+16 IFFT，22528复数点/45056分量对照记录；C API code/2^24，应用F23不变 | portable Q30等价；新gate；所有输入域；混合位宽调度 |
| AMD 29位前向 | N所述196/196历史覆盖；剩余136帧批准原件 `phat-fixed-03/closeout-01/a29-coverage-review-01/B-REVIEW.md`，准确 `b8c5e87f6cb1054c2684719310f02f36c83ac731`；xfft9.1 rev15、24位twiddle、scaled/convergent/natural/nonrealtime | 29位IFFT；新gate居中域；全链资源/实时；允许运行时切换25/29位 |

`reference25` 继续保留。固定右移4、共同指数、gate/DOA共享、统一IP宽度均只能经方案选择及受影响增量证据关闭；不能用这里的格式表代替 A 决定。

## 与复现返修的边界

`CP/REPAIR-R1-R2.md` 的基线bb964cb，A原报告5e343f2，返修被测实现0bea3461；其12+18测试、48 WAV、120整数数组、19 JSON记录是旧作者结果。R1浮点字段容差只吸收尾差，整数/类型/状态/NPZ逐码仍严格；R2采用指定提交原blob。此次没有运行这套复现，没有把本地工作树与blob的文本差异归一化放行，也没有把作者返修自测当A复核回执。
