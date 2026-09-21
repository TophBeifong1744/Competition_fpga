# A侧生产合同决定表（未联合冻结）

版本：`a-production-decision-draft-0.1`。适用四路H1开发链，不适用六麦入口。DECIDED_A只表示A建议/实现选择，REUSE表示既有合同引用，PENDING_B/UNVERIFIED不是通过。默认reference25和采集固件均不改。

## 控制与数据

| 字段 | A决定或沿用 | 状态 / 缺口与责任 |
|---|---|---|
| 原始行 | 8×LE32、uint64 ID、mic0..3、signed24扩展int32、原flags/reserved；48kHz是配置值 | REUSE H1 0.3；不改列、不伪造测频 |
| 几何 | mic0原点，+X向mic1、+Y向mic3；坐标/config分别按实际版本绑定 | REUSE已有操作记录；未标定不升级为独立声学映射，A不猜测换线 |
| 分帧 | 1024/512，跨250组包边界，不补尾，不跨错误/session；错误行也更新上一接受ID | REUSE软件语义；不能把包TLAST当FFT TLAST |
| 生产路线 | PS复制、校验/accepted-row、分帧/所有权/提交；后续独立PL数值服务 | DECIDED_A建议；不是已接入，现有S2MM没有自动具备算法MM2S路径 |
| 输入所有权 | DMA完成、invalidate/状态核对、复制入独立环成功后释放RX；复制失败不得释放掩盖错误 | DECIDED_A；缓存属性/屏障/实际故障排空A未实现 |
| 帧内存 | 采用C候选独立滑动窗＋2输出槽；借用释放前不覆写 | DECIDED_A；替代旧0ab两工作区容量模型，不改旧证据；ARM布局/地址未定 |
| 有限身份 | C内部session uint64且递增，generation uint64跨session保留；frame/interval有限且不回绕 | C候选；旧0ab的32位session_key只是历史方案。外部boot/UUID到内部session映射由A补，不截断字符串/计数 |
| 不可变配置 | config/geometry/numeric三份32字节身份随帧复制；activity/calibration/固件依赖须纳入规范化配置哈希来源 | C显式配置，不把夹具TTL=512/status=3当生产默认；规范化序列化与哈希生成尚未实现 |
| 错误 | clip/drop断段；duplicate/reverse/wrap及非法行/致命上游错误停止session；原因全集保留 | REUSE语义；运输检查与可恢复语义检查分层仍由A适配 |
| 同批完成 | 先全批错误/控制与binding、status、payload一致性预检/聚合，再commit；冲突批无新可消费结果 | C返修ca512a8待B复核；检查实际commit/take，不仅返回码 |
| 当前未知error | 包括越界slot/未知代次/已释放对象均fail-stop；旧session独立STALE | 同上；历史提交事实与当前可用性分离，晚错不能物理回滚 |
| 最大代次 | UINT64_MAX可被acquire，下一次分配耗尽失败且不发布READY | 同上；不把MAX当空选择哨兵 |
| TTL | last_id+ttl溢出拒绝；等于边界有效；commit/take都查；HOLD不续期；unknown时间拒绝 | REUSE软件语义；可信采样时钟锚、漂移/延迟上界仍待A实现 |
| STOP/RESET | fatal/session_abort硬停撤销逻辑结果及未消费输出，再按运输协议停止/排空；audio_smooth_stop独立表示平滑回退请求 | DECIDED_A候选；前者不允许被20ms淡变掩盖，后者接受最长960样点回mono；实际设备中止仍未实现 |
| 状态屏障 | 每次数值服务须绑定session/frame/config及overflow/error/完成；全部要求状态闭合才能提交；all_required_status_visible_at≤available≤commit_now | DECIDED_A；B d3d2a3d检查器该项仍待修，不能引用其误放行为证据；完整状态位集合待联合确认 |
| 执行上下文 | 单worker拥有bridge；ISR仅通过另行定义的事件队列交接，hook不重入 | DECIDED_A；事件队列/内存屏障/并发实际尚未实现，不靠当前C测试证明 |

## 数制：来源、单位和冻结界线

以下0ab旧表只作为已做软件对照的准确来源，不把其中旧DOA S22和新S23建议混成同一版本；新合同候选必须经B确认后生成新的profile/hash。

| 环节 | 当前A建议/引用 | 尚需决定或验证 |
|---|---|---|
| 原DOA Hann | S24×U18F17，宽乘积、RNE>>17至S24；溢出显式无效 | ROM身份和RTL乘积/RNE对照；旧软件证据复用 |
| activity Hann | 1024项S34求和、RNE均值、去均值S25、S43乘积至S25 | 不能套原S24窗的范围证明；由B最终节点profile确认 |
| FFT29 | 窗整数精确<<4；1024点，十级各右移1、24位twiddle、convergent rounding | 原覆盖只引用。gate S25输入范围和配置是否在旧向量域必须逐项判断，未覆盖新增向量再测 |
| 29→25 | 固定RNE>>4作为独立候选；越界拒绝，不静默截断 | PENDING_B；不等于六路自适应公共指数，弱信号限制保留 |
| 互谱/PHAT | 旧来源S25F23→S51F46，平方和U102F92；epsilon为互谱幅度码，旧值2^26/10^15 | band/mask/epsilon/newgate配置须绑定同一profile；平方码、PCM码和幅度码不能互换；生产参数未签 |
| PHAT归一化 | 旧整数开方/倒数Q30两轮Newton/RNE，理想归一化误差与逐码一致分列 | 冻结实现golden，而非用理想浮点强迫每码相同；宽乘与除法中间位宽仍需实现绑定 |
| IFFT25 | 25位、逆向、十级各/2；DC/Nyquist实数及最小负数共轭溢出守卫 | AMD24与portable Q30不能混golden；前向29/逆向25推荐双IP候选，不运行时切位宽 |
| lag | S18F12，物理时延边界/插值/异常保持配置绑定 | 边/对角整数搜索候选范围不是实测几何；新增RTL逐码与拒绝行为待做 |
| DOA | S23F20拒绝前xy候选；LS分子S37、预测S46、残差U35、模U43；原CORDIC容纳S25/角累计S26 | 绑定268e526有限域包含界，旧S22表保留；舍入/除法临时位及实际核未定，容纳不等于角度正确 |
| 新归一化CORDIC | A选择继续比较d3d2a3d共同精确左移/LZC及+180→−180规范化候选；独立numeric profile，S28容纳归一化xy | 原函数保持；d3d数值子项既有复核可复用但整包NEEDS_FIX，不称全域≤1码定理；不静默混入原golden |
| 动态DAS | A接受8前视/17历史为下一步候选参数，限定±8域且零权重不读邻点；2beam+1最新pending、480淡变、960样点平滑回mono | DECIDED_A候选，基于268e526及d3d合同，不倒签旧9前视；不是生产批准，不保证每个被覆盖请求执行 |
| 音频时间 | source_sample=emit−8；启动−8..−1允许，真正EOF补尾；gap/reset不得伪装EOF补零。tracker ready/expiry映射emit时基须显式+8 | 严格整数排除bool/float；ready停顿不暂停TTL；d3d采样schema反例未闭合，不靠其轨迹PASS确认 |
| ROM | A首选PS DDR整session只读驻留净552960B，按配置请求下发延迟，禁止默认整ROM塞PL | 固定几何/48k/343m/s及[-180,180)Q8角域，ROM S16域最大32425；通用+32768需S17；实际地址/cache/吞吐未定 |
| 输出 | 当前已提交且未过期结果可供后续音频消费；未知/失效回退由最终动态策略约束 | 空间lookahead不能充当门/跟踪/排队全链延迟；采样连续性与结果更新速率分开 |

## 集中确认的完成标志

1. B针对上述未定项给准确版本与同意/调整，不用笼统“接口通过”。
2. A按确定字段绑定数值配置、状态集合、源/输出身份及所有权；新增profile不改旧golden。
3. 工程修改前另给拓芙范围和原工程/副本选择；此稿不授权自动修改。
4. 本稿未定项不阻塞文档/预算模型；但阻塞相应生产接入。旧0ab、新a7 Python语义、ca512 C返修分别保留来源。
