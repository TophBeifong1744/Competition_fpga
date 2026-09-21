# 新增逐级数制对照

准确被测源码来自Git `f5a4cea7a7cf7dcccf09720cfff92131e6157752` 的 `h3-complete-20260918/source/fixed_golden.py` 与 `phat-fixed-03/phat_model.py`；运行快照和SHA在evidence/run03/inputs及bindings.json。不是读取脏工作区同名文件。新gate类来自 `bb964cbd5b4bee005702bebe6b9cee16d9b885d9`，仅AST提取原样IntegerActivity类跑新边界；不跑其前向FFT/stage或八段。

## 数制与独立预期

S/U表示总位宽含/不含符号，F表示相应单位的小数位。原始PCM整数码与归一化满量程单位必须分开：同一S29数可描述为原PCM单位F4，或归一化F27；不得据此说位模式改变。

| 阶段 | 输入→输出、舍入与错误 | 本轮独立对照 |
|---|---|---|
| 原DOA Hann | S24 PCM×U18F17，S42乘积，RNE右移17→S24；越界拒绝，饱和有计数 | 65位Decimal Taylor cos产生1024系数；4096乘积用Fraction精确RNE；端点、满量程/负数/随机输入及非法系数 |
| 新gate前处理 | 1024个S24用S34求和，RNE/1024；去均值S25；S43乘积RNE>>17→S25 | 新合同已绑定；整段均值/窗/前向FFT本轮NOT_RUN，不借原S24窗测试证明新S25窗全范围 |
| FFT29及固定4 | 窗整数精确<<4；Q30 radix2十级各/2；RNE>>4→S25，overflow整帧无效 | 引用f879的262401独立适配案例及旧FFT覆盖，不重新运行前向FFT；新gate/DOA不能未经证明共用FFT |
| 互谱 | 两个S25F23半谱相乘带共轭，宽S51F46，平方和保守U102F92 | 4097向量以独立乘法矩阵验证整数实虚部，S25越界拒绝 |
| mask/epsilon | band7..85，sq>0且2500sq≥band最大；≥12bin；epsilon=2^26/10^15互谱幅度码，非平方码/PCM码 | 已有阈值边界引用f879；本轮复核11/12bin与IP overflow拒绝、epsilon精确单位 |
| PHAT | round(sqrt(sq<<48))，幅度带24小数；归一化mantissa/reciprocal Q30 LUT+两轮Newton，再RNE至S25F23 | 2054向量与80位Decimal理想归一化独立比较；开方整数逐码一致，归一化对理想值最大1码误差。这是近似误差测量，不是“全级逐码等价” |
| IFFT补共轭 | 513半谱→1024，DC/Nyquist必须实数；其余镜像imag取负；S25最小负数取反溢出拒绝 | 镜像511bin；复现B函数对非法非实端点未拒绝，新候选入口守卫拒绝3种非法输入。当前正常band不含端点，此反例不是实录损坏证明 |
| IFFT25 | inverse、Q30 twiddle、每级/2，总/1024，输出S25F23；overflow不得使用饱和值掩盖 | 新执行3个解析逆变换基向量，6144实虚码精确；另1个独立DFT证明超范围的overflow反例；没有重跑历史前向FFT |
| lag | 对正相关峰搜索，边6/对角8整数点，抛物线RNE至Q12并夹±0.5；S18F12；超物理边界无效 | 102组合，用Fraction抛物线及平方整数不等式独立判断；不是几何标定 |
| DOA | 6对lag的法方程→S22F20方向，残差与模长拒绝；24步CORDIC→S18F8度 | 5方向用Fraction高斯消元独立得到精确量化xy，角度对atan2允许0.02°；不足配对/零向量拒绝。非声学角度精度证据 |
| DAS | S24 PCM、Q12延迟；线性插值S37、四路和S39F12，RNE/(4×4096)→S24；饱和记错 | 257样点×4通道、正负分数延迟，Fraction独立分段线性对照；边缘按零延拓，仅离线边界规则，不把缺失实样本补零当连续有效数据 |
| fade/跟踪 | U13F12权重、整数RNE/状态规则 | 引用B run05，不新跑；本次DAS不是重新验证完整自动波束/跟踪 |
| gate功率/状态 | bins7..72，U104分子/U45分母→RNE U64 PCM码²；阈值比较扩U66；3路、连续3帧 | 功率整除本轮仅合同/操作预算；新测原类3开/3关、invalid清状态、U64顶值不能乘4回绕；speech/identity保持unknown |

## 验证层次

| 项 | 数学/整数/模型 | 本轮AMD IP仿真 | 实际系统 |
|---|---|---|---|
| Hann、互谱、PHAT、lag、DOA、DAS | 上表新增案例PASS，范围有限 | NOT_RUN | NOT_RUN |
| IFFT | portable Q30解析向量与异常状态PASS | NOT_RUN | NOT_RUN |
| fixed4 / accepted-row | 引用f879受审自检，不当B批准 | NOT_RUN | NOT_RUN |
| 新gate | 状态类边界PASS；全流整数gate未跑 | NOT_RUN | NOT_RUN |
| 生命周期/TTL/预算 | 本包软件模型通过 | NOT_RUN | NOT_RUN |

portable Q30函数与AMD 24位twiddle分开绑定；本包不含新XCI、不改IP配置。FFT29历史196帧仅引用对应包，不能推广本轮后级。IFFT的3个解析基向量没有覆盖一般旋转因子误差；需要准确IP组合后另做新增后级XSim。默认reference25未改，B原函数未改。

### 新发现与最小处置

`conjugate_complete`接受DC imaginary=1，记录在endpoint-counterexample.json。新增 `engineering_model.validate_ifft_half` 仅作为独立边界守卫，检查shape/S25/实端点/负最小共轭，不静默截断或将错误清零。生产接入前须由B确认错误归属。原golden与原日志保留。

负延迟DAS会请求未来样点；8样点共同延迟只能覆盖几何插值邻域，不能自动覆盖新gate至少2048样点、方向/跟踪/排队延迟。在线输出必须明确“使用当前已提交的旧结果”还是延迟保留音频；本轮不以8样点宣称端到端因果闭环。
