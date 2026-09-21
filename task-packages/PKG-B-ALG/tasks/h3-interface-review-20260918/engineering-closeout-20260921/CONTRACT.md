# H3 工程合同收口表（2026-09-21，待 A 复核）

2026-09-21 A复核覆盖：整包NEEDS_FIX仅针对轨迹R1/R2，作者返修见 [repair-r1-r2](repair-r1-r2/README.md)，尚待A批准。A已确认CORDIC须独立profile，新候选以该子目录 `cordic-profile.json` 绑定原源码与原run05 golden，未重新计算或替换FG。A接受8前视/17历史及最坏20ms平滑回mono作为下一步离线候选取舍；统一session采样时基、硬停与平滑STOP分离。ROM优先评估PS DDR只是部署建议；生产/AMD/RTL/资源/实时未冻结。下表原“待裁决”依此分为已接受的研究取舍与仍未批准的生产选择。

“已决定”仅指已获相应限定批准的事实或保留约束；“候选”不是双方生产冻结；“阻断”指部署所缺材料。本文覆盖父目录历史表中的 S22/9 样点待定措辞，不改原件。默认 reference25 保留，声学阈值与方向准入不变。

## 源码、证据简称

- FG：[fixed_golden.py](../../h3-complete-20260918/source/fixed_golden.py)，函数 `fixed_fft/adapt_fft29_to_s25/lag_q12/doa_q20/atan2_q8/das_block`。
- PH：[phat_model.py](../../phat-fixed-03/phat_model.py)，`mask_for/normalize/reciprocal`。
- CP：[integer_gate.py](../checkpoint-20260923/source/integer_gate.py)；八帧 golden 位于同级 `evidence/golden02`。
- N：[B1–B6](../fixed-nodes-20260921/README.md)，准确 349501c；D：[动态 DAS](../dynamic-das-20260921/README.md)，准确 268e526。
- 数制旧统一表与逐函数身份：[FIXED-CONTRACT](../closeout-0918-20260921/fixed/FIXED-CONTRACT.md)；该表历史缺口由后续批准覆盖，不能再整批派 B1–B6。
- 批准路径均为仓库根下 `docs/reviews/`：`b-checkpoint-fe67547/REVIEW.md`、`b-consolidation-b5913e5/REVIEW.md`、`b-fixed-nodes-349501c/REVIEW.md`、`b-dynamic-268e526/REVIEW.md`、`a-h3-two-20260921/B-REVIEW.md`、`h3-repair-a7f70c5/B-REVIEW.md`。

## 一张准确合同表

| 项目 | 已决定/已批准事实 | 本轮候选与源码 | 阻断及负责人 |
|---|---|---|---|
| 输入/单位/profile | S24 原码保持；码域 F0 与满量程 F23 是同一码的单位解释；默认 reference25 保留 | FG/CP；N1024/H512、48kHz、四路六对，固定几何 | A+B 共同选择生产 profile、配置哈希、几何/通道映射；NPZ int64 不代表硬件位宽 |
| 前向 FFT/窗/缩放 | reference25 为 S25F23；旧 FFT29 的 196 帧批准仅归档前向核 | FG：Hann U18F17；DOA 窗后 S24，gate 去均值窗后 S25；精确 <<4 至 S29，十级各 RNE /2；固定 RNE >>4 回 S25；Q30 twiddle | A 绑定 XCI/ROM/握手；B 比较同 profile。固定移4与共同指数二选尚未生产裁决；gate FFT 与 DOA FFT 不共用数值结果 |
| portable/AMD 身份 | portable Q30 与 AMD24 twiddle 分列；原 golden 不互借逐码结论 | FG portable；AMD25 历史6 FFT+16 IFFT（22528复点）；AMD29历史196前向 | A+B：AMD全链、居中 gate 域及混合位宽调度；不能运行时把29位核切25位 |
| PHAT 保护/epsilon | N 的mask、11/12bin、零输入、倒数/开方节点已限定通过 | PH：互谱 S51F46，模平方保守 U102F92；band7..85；`square>0 && 2500*square>=max_band_square`，至少12bin；epsilon=`2^26/10^15` **互谱幅值码单位**，当前0<epsilon<1但不能泛化为0；开方mag_frac24，倒数F30，输出S25F23 | A 选择有限服务 sqrt/除法器；B 复核 RNE/内部位宽与非法域。若四路共用新适配指数，多移r使互谱码尺度变2^(-2r)，epsilon及其他阈值必须重推，不套用旧常量 |
| IFFT/补谱 | N已补一般非法 DC/Nyquist/共轭取负保护候选，未接默认链 | FG `conjugate_complete`；N b2b4 `guards.checked_conjugate`；S25F23，逆向十级各/2，不能再除1024 | A：AMD25对应 XCI/wrapper 的完整输出/最终status；B：同源 golden。没有 AMD29 IFFT 批准 |
| lag/插值 | N56例、边/对角物理边界与平局已限定通过 | FG：lag S18F12，delta限制±2048，分母翻正后RNE；0分母取0；先序负lag胜平局，最终物理界拒绝；margin仅诊断 | A：峰值及second扫描、插值/margin除法宽度和周期；不新增声学margin阈值 |
| DOA/内部容器 | N656顶点，D64项包含区间/42对集；拒绝前xy最大2531477，S23F20候选，不能先截S22再拒绝 | FG `doa_q20`；D `derive_widths.py`：分子S37/S46，残差U35、模U43，旧CORDIC xy S25/angle S26。仅固定几何、合法tau盒 | A映射实际除法器/余数翻倍/进位；B非法域/逐码。包含界不等于误差或最小硬件证明；生产未冻 |
| CORDIC小向量 | 旧D48轨迹只证明包含界，原通用小向量数值缺口确实存在；当前DOA模长门排除这一级小向量 | 新 `cordic_candidate.py`：S23整数非零输入共同精确左移使max幅值bit_length=24，复用旧24步，末尾RNE，输出规范[-180,180) Q8。新1215例最大0.50773码，原942个反例留存 | B作者候选待A审；没有替换FG或调门。新xy建议S28，不能沿用旧S25；全域误差证明及AMD/RTL未完成 |
| 延迟 ROM | D已全枚举92160角、276480码；S16最大32425，mic0=0 | D `delay_rom.py`；规范Q8角[-180,180)，载荷552960B；通用±32768延迟域要S17 | A决定PS DDR/压缩/PL方案并绑定装载哈希、地址、带宽/身份；本表不批准完整PL ROM |
| DAS输出/饱和 | 旧FG单块平均后S24饱和计数；D动态合法输入为凸组合，断言S24，非溢出修复 | D：8前视/17历史；RNE四路均值与双端点混合；S38插值累加/S36混合包含界；新极端32点与Fraction逐码一致 | A+B选择串行pending策略；任何缩窄发生的overflow应失效而非“软件饱和已通过”。饱和测试只验证FG节点，无RTL保证 |
| 动态/生产事务 | D离线动态、f879逻辑、a7f70c5状态模型各按原范围关闭；不再列全NOT_RUN | [FLOW](FLOW.md)；新trace checker检查导出轨迹，不是驱动、队列或事务实现 | A负责真实session/config/status原子提交、背压/CDC/STOP；B准备golden；生产合同未双方冻结 |

## CORDIC 新内部界与测试解释

共同左移后每分量绝对值小于2^24，没有右移量化；最大S23负码也先在更宽容器取绝对值。旧24步算术移位每步满足 M_next <= (1+2^-i)M+1。可用有理数逐步上取整计算上界（本包检查结果另存），S28为保守容器；角象限偏置与步进仍沿D的S26包含界。LZC、左移、输入取负都必须在硬件宽度合同中体现。

数值 oracle 用 `math.atan2` 计算连续角度，按圆周误差预先限定≤1个Q8码（1/256度）。这是1215个确定向量的数值比较，非全域定理、非另一个位精确C模型；输出变化必须拥有新profile，不能覆盖旧golden。规范化+180→−180只在新候选发生，恰好满足现ROM域；旧FG返回+180的事实保留。reference25与原DOA门都未改。

## 各级证据和缺项

| 级别 | 软件/旧证据（本轮引用） | 本轮新增 | AMD/RTL/工具缺口 |
|---|---|---|---|
| 窗/适配/功率/状态 | N B1/B3、B2/B4已批准 | RNE162边界、S24饱和6例仅支撑新候选 | 不重跑旧节点；实际窗ROM与溢出RTL待A |
| 前向/逆向 | portable run05及CP八探针；AMD25历史6+16、AMD29历史196 | 本轮FFT/IFFT调用0 | 旧AMD归档不等于新链通过；新AMD/RTL运行0 |
| PHAT/lag/DOA | N节点+656顶点；D64项推界/42对集/12128中间值 | 小向量候选与非法域6例 | sqrt/除法器、CORDIC硬件与非法tau入口仍待A |
| 动态DAS | D32事件分块、18端点、800更新、ROM枚举与A独立Fraction反例 | 极端32输出、源身份/可用时点轨迹；14错误注入拒绝 | 轨迹为数学夹具；真实ready、有限队列、全gate/DOA流未测 |
| 事务 | f87928项/30序列；a7f70c5 E01～03关闭 | checker正常/late-reset/取消背压及反例 | 不重新实现A模型；未绑定其异步回调、PS C、生产ABI/CDC |

旧证据仅复用，不累计为本轮新增测试；完整H3、方向效果、整机实时仍未批准。
