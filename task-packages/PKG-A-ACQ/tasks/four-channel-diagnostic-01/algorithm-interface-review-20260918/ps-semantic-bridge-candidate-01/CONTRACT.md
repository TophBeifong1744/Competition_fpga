# 独立C接口与候选语义

本接口是主机软件候选API，不是生产线缆/寄存器ABI。单执行者调用；不支持并发线程/ISR直接重入。hooks为同步只读观察者，禁止回调内重入/修改bridge；时钟hook必须只返回当前session可信的采样时间上界或unknown。软件批处理优先级不证明真实CDC/异步硬件时序。

## 输入与接受点

H1每行32字节：8个小端32位字，id_lo/id_hi、mic0..3、flags、reserved。每字节移位解码，不把void*强转为uint32_t*；int32转换分两段保证可表示，不依赖无符号溢出转有符号行为。ID及行号一直为uint64，JSON诊断用十进制字符串。

`psb_enqueue(bytes,length,upstream,upstream_count,token)`仅复制1..250行进自有环，成功后调用者可立即改/释放原缓冲。长度0、非32整数倍、超过8000、SIZE_MAX和元数据长度不符拒绝。输入包允许短批次是**主机语义馈入接口**，不代替实际DMA8000B长度合同。upstream是每行独立uint32侧带错误码；非零即UPSTREAM，H1原flags/reserved不占用/改写。测试integrity_error映射侧带非零；实际来源编码尚需生产适配。

`psb_pump()`按FIFO消费一个复制包。accepted-row点是此函数逐行解码并更新rows/previous，不是enqueue时；因此STOP时尚未pump的包记录为discarded_rows，不假称已被语义层接收或连续排空。真实DMA排空仍由未来运输适配器负责，不在本候选内。

- 每个错误行仍更新previous ID；先用上一accepted ID判断跳号，再更新。不以“上一干净行”替代。
- CLIP、DROP：保留原始原因组合、flags/侧带和前后ID，丢当前行并清overlap。下一个clean行才开新interval；连续错误不创建空clean interval。
- duplicate/reverse/wrap、flags高位/reserved非零、PCM未合法S24符号扩展、upstream、队列/有限计数故障：停止session，留状态、当前输入包所有权及审计。不能调用start清错复用。
- 编号正常但仅错误码非零仍是致命错误；多个同时错误保留原因位OR全集，不以一个显示首错覆盖其他原因。

## 分帧与所有权

每个clean interval独立N1024/H512；帧发布后保留后512组作为重叠窗口。不加窗、不补尾、不改采样编号，不跨错误/session拼接。frame号在session内连续，interval号仅对非空clean段增加；描述符含session、逻辑frame/interval、原始行半开区间、first/last ID、reset_before、96B配置身份。

独立滑动window与2个不可覆写的输出帧槽分开：因此不是直接移植旧“两帧共用存储”预算，也不是BRAM实现。frame观察hook在发布时立即给出内容，仅用于日志；它不等于算法获得授权，也不等于结果可提交。随后发生错误/stop会撤销旧帧，观察日志仍保留历史已生成帧。

`frame_acquire`返回最早READY帧的只读借用及token；`frame_release`是消费者承诺不再访问借用内容的边界。释放前不得覆盖；旧token/重复释放拒绝。C无法防止调用者在释放后故意解引用旧指针，调用者必须遵守借用寿命。revoked帧不再被acquire，但允许持有方/管理方用原token释放；未释放则新session拒绝。

输入8包满、输出2帧均未释放、结果4槽未释放均显式FULL并fail-stop，不覆盖、不断言“暂停麦克风即可”。调用者可先暂停pump来等待帧消费，但输入容量有限，不可能吸收无限背压。

## 身份、提交和时间

初始化配置无生产默认：3份独立非零32B身份（config/geometry/numeric-profile）、ttl_samples、max_rows、max_frame、max_interval、required_status均由调用者指定。config哈希应由调用者包含activity/calibration等全部相关设置；本候选不生成哈希、不建立外部UUID映射、不假称完整生产版本绑定。运行中禁止直接修改配置/内部字段（测试有限计数白盒注入例外）。

session显式传入非零uint64，严格递增；generation为对象生命周期内单调uint64，跨stop/reset/start不清零。token含session/generation/slot，不凭物理槽索引匹配回调。frame和interval的可配置上限最高UINT32_MAX-1，留一哨兵值检测下一次计数，不允许回绕。达到计数边界时明确拒绝/fail-stop；TTL加法先判溢出再相加。

`result_begin(frame_token)`要求帧HELD且未撤销；每帧只能发起一次事务。结果复制描述符，独立于帧存储。帧可释放的前提仍是算法完成对原帧的读取，不能因为仅创建了结果描述符就认为异步读取已结束。结果payload是测试用不透明uint64标识，不承载DOA/DAS数值。非零status片段的payload必须一致；status=0可用作时钟重新检查，不得替换数据。

`dispatch(batch)`两遍处理：

1. 先汇集整批所有错误，记录旧session回调；未知当前事务的错误保守fail-stop。
2. fatal/STOP/RESET先于任何提交。STOP/RESET撤销所有在途及已提交可用性，记录未消费输入/未满帧，不强制复位运输硬件，不清除已锁存故障。
3. 仅同身份、配置、当前interval、完整required_status、无错误、时间有效的PENDING结果可COMMITTED。重复完成不能再提交。
4. 提交时和`result_take`消费时各查一次TTL；等于last_id+ttl有效，超过失效，now<last_id拒绝，时钟unknown不提交/不消费。take仅一次；不能利用HOLD刷新TTL。
5. 提交后晚错记录事务token/frame/interval并fail-stop，后续消费拒绝；已输出的物理效果不可回滚。释放后的当前session未知错误也保守fail-stop。旧session错误拒绝并保留STALE审计，不误杀新session；不把它改归当前帧。

同批排列的错误在前/完成在前产生相同优先结果，实际C测试两种排列。没有证明不同线程真实竞态、硬件status可靠性或外部完成屏障。

## 审计和恢复

64个审计条目保存row/error/control/commit/late/stale状态；满后保留原条目、last_event、完整累计原因并fail-stop，不能静默覆盖。`audit_clear`仅供调用者确认已归档后腾出审计空间，绝不清failed或允许失败session重启。正常restart要求输入空、帧/结果槽已释放、session递增。

失败后的销毁/新对象初始化是显式事故恢复，不是自动启停入口。外部boot/session唯一性、审计持久化和复位流程尚未实现；不应持旧token访问重新初始化的对象。本候选不生成S23F20、lookahead、算法数制或生产ABI默认值。
