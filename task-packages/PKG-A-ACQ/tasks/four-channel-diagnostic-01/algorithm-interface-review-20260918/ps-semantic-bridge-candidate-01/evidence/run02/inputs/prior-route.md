# 推荐实施路线与待裁决项

实际整理于2026-09-20。本文是工程侧推荐与可执行模型合同，不是已实现生产ABI，不代签B。只写本独立子包。

## 1. 推荐路线：先有PS语义桥，再接独立PL算术服务

当前实物链是四路同源PDM/CIC→持续分包→simple S2MM→两个RX槽→Cortex-A9 #0 standalone检查。实际 `four_mic_endurance/src/continuous` 五个源码只读快照及SHA见run03 bindings；源码在场不证明当前板上加载了该版本。当前短留存S1 store不是在线算法队列。已批准耐久/采集不重新运行。

推荐：**PS处理accepted-row、分帧与会话/错误；PL后续承接封闭帧的数值计算**。原因是现有DMA路径已到DDR，PS能保留全64位ID和诊断原因，先不在61.44MHz不可暂停采集链中串入可背压BRAM分帧器。单缓冲BRAM候选仍是独立可复用实现/对照依据；该路线暂不重复实例化它，也不把其资源相加到PS帧缓冲。选择将分帧搬到PL是后续替代路线，不是本轮隐含工程改动。

1. PS接收检查长度、guard、DMA/source状态；接收完成后失效对应cache。按原始8×LE32解包，mic0..3不换列。
2. `FREE→DMA→CPU`，CPU检查后把整个8000B包复制进**独立有界8包环**，复制/发布成功才允许RX槽FREE；失败保留CPU所有权、寄存器与原因，停止源并按现有协议排空，禁止回收掩盖错误。
3. PS语义桥按每个accepted row推进历史ID（错误行也推进），clip/drop断开clean interval；连续错误不新建空interval；duplicate/reverse/wrap、非法flags/reserved/range、upstream/queue error停止会话。保留全原因集合，不以展示首错替代原因。与现有`check_packet`“所有ID异常直接返回”有差异：后续生产接入必须显式拆开transport检查和语义检查，不能宣称现有C已支持恢复。
4. clean row进入两个1024×32B帧工作区，N1024/H512。前一帧封闭后先复制其后512组到空闲FILLING区，再发布READY；复制未完成不得转IN_USE，消费者完成前不得复用。READY/IN_USE占满则不覆盖，暂存在8包环；环满视为可观测致命故障。无效尾帧不补零，不跨interval/session拼帧。
5. 算术服务取得不可变帧、完整身份与版本快照。数据缓存flush后才交DMA/硬件读；硬件写回完毕后invalidate；描述符发布/获取还需内存屏障。PS纯CPU复制不能用“flush即可”代替所有权。生产内存属性/屏障代码尚未实现。
6. 第一接入模块推荐**PS语义/帧缓冲桥的独立C候选**，测试对照f879软件模型；接着才是PL Hann/FFT服务。现有simple S2MM并不提供PS→算法的发送路径；后续需择定新增MM2S/专用DDR读取器与结果回传控制接口，获准后由拓芙操作。现在不假称已有双向链、不生成BD。

建议最终PL域负责window、两个独立FFT29/IFFT25核、互谱/PHAT、lag和DAS算术；PS负责控制、队列、DOA/跟踪与提交。DOA/跟踪若PS WCET不能满足再考虑PL CORDIC；预算模型将这一服务表示为等价100MHz操作槽，**没有把模型周期当ARM真实耗时**。当前PS核频率/WCET与总线等待没有新测量。

## 2. 身份、时钟与提交

- 外部session保持唯一字符串/UUID；内部32位session_key必须按一次装载生命周期单调分配、查表绑定完整字符串，尚有在途引用不得复用。frame/interval为u32，原sample_id为u64；到最大值前fail-stop，禁止取模“恢复”。断开重连后需要新boot身份，不能仅清零session_key。
- 配置、geometry、numeric profile、activity profile、background calibration、固件/bit绑定分别保存SHA-256；运行中变更需新session，不用一个短版本字符串替代这些身份。逻辑描述符建议含session/interval/frame、first/last原ID、reset_before、错误原因、上述版本。传输寄存器布局/字节序仍待B联合冻结；原H1不动。
- 优先级：STOP/RESET/session-fatal > frame error > commit。控制命令先撤销所有未提交及HOLD可用性，然后继续运输层排空。排空产生的数据可作诊断但不能重新发布方向。恢复性错误清帧、overlap、gate、tracker和TTL，新clean row才分配新interval。
- 每帧只提交一次；必须等待相应frame的status完整闭合。晚到错误若帧已提交，记录撤销事件、禁止以后使用该结果并fail-stop；已经物理输出的样本不能被“回滚”，要标明受影响区间。新session的frame=0不能接收旧session的晚到结果。
- `valid_through=last_id+ttl_samples`，相等有效，大于过期；HOLD不续期，溢出拒绝。不能把“最后收到ID”当现在采样时间，因为它可能积压。模型提供`sample_upper_bound(anchor_id, elapsed_us, uncertainty_samples)`：同一epoch的采样ID/PS时间锚点+向上取整48kHz经过样数+不确定性上界。实际跨域锁存/时钟漂移上界未给出，故生产available时刻未知时拒绝新提交，而非填0。停止/reset使该锚点失效。
- 暂定activity只发布`band_activity`，`speech_present`和`target_identity`仍unknown；这不是声学存在判断已通过。

## 3. 缓冲与停止

逻辑布局由memory.json生成，约0.2MiB；只证明容量相容，不分配新绝对地址，不修改链接脚本/现有1MiB RX保留范围。必须先获准把RX未占用部分划给独立环/工作区，证明程序/堆栈/既有留存区不相交，才能真正落地。当前只2×8064B是真实RX合同。

| 对象 | 所有者与释放点 |
|---|---|
| 2×8064 RX | DMA完成→CPU invalidate/检查→独立拷贝成功→FREE；guard64B保留 |
| 8×8064 ingress | CPU producer→语义/组帧consumer；完整消费包后释放，不能持有RX指针 |
| 2×(32768+128) frame | FILLING→完成overlap拷贝→READY→IN_USE→done/status闭合→FREE；64B双guard |
| gate/DOA半谱各16416B | 两套不同窗输入不共用数值；最后gate power或最后pair消费后释放 |
| PHAT/IFFT/correlation | 每次一对串行复用；6对lag已记录才能覆写对应旧pair |
| audio history/lookahead | 18×4×4B仅空间插值的前后邻样，不足以吸收算法延迟；输出hop不能因结果晚到而无界留存 |
| descriptors/result | 控制撤销立即改可用性；原记录/审计保留至无在途引用，不能立即重用key |

正常stop不复位PS/PL/DMA：请求完整包边界停止，消费有效运输尾包，闭合所有权后IDLE。致命故障先停源/保留状态；是否需要DMA复位由原因与静止确认决定，不做自动清错误重开。复位命令必须flush逻辑epoch/旧结果，不依赖BRAM/DDR内容清零。

8包环等于2000组≈41.667ms的原始容量，但可用停顿余量取决于当时占用；不是无条件允许41.667ms停顿。两个frame工作区最多一个IN_USE和一个FILLING/READY，预算的总消费者容量只能按2计算，不能额外假造两个等待帧。生产者不承受无界backpressure；队列满必须可观测停止，而非让PDM时钟停下来。

跨域至少有61.44MHz采集→现有DMA域、拟建100MHz算法→PS控制。复用原采集CDC证据不等于新增桥CDC通过。独立AXI时钟转换/异步FIFO应承载数据+身份+reset/停止确认，不能多位状态逐bit双拍同步。算法status可背压，但必须定义最大服务时间，否则全链无有限上界。

## 4. 一次集中裁决（不因它们停止本轮离线测试）

| 选择 | A推荐 | 需B/后续工程确认 |
|---|---|---|
| 生产数制 | fixed4独立候选，reference25默认不动 | 接受弱信号量化/阈值单位；共同指数另案 |
| gate/DOA FFT | 当前分别计算，不未经证明共享；8 forward+6 inverse | 若统一去均值必须重做相关方向/数制回归 |
| 分帧位置 | PS语义桥+两工作区优先，旧BRAM候选备用 | 生产CPU WCET和可用内存；不能把软件确认当RTL批准 |
| 算术IP | FFT29与IFFT25分核；Q30/AMD24分开 | 准确XCI/status/scaling组合及新增级间AMD对照；现有历史不能代替 |
| endpoint/overflow | IFFT输入DC/Nyquist imag=0、conjugate范围强检查，overflow整帧失效 | B确认新边界守卫；不更改golden去迎合 |
| ABI/提交 | 含新activity/calibration身份，unknown字段保留；PS统一提交门 | 有限ID表大小、晚错审计和真实时钟锚；寄存器布局未冻 |
| 服务/内存 | 8包环/2工作区有界，满则fail-stop | 真实地址合同、PS WCET、DDR/CDC/status/output服务上界及实测 |

推荐方案可以进入独立候选编码排期，但不授权现在修改one或Vitis。未获完整H3准入，不接生产算法链。
