# 实际C内存与预算边界

来源：最终GCC16.1.0 x86_64 Win32 SEH，O0/O2的实际sizeof/_Alignof一致，见run04/memory-O0.json和memory-O2.json。候选本体无malloc/free，无递归，不使用VLA；调用者提供整个对象，本轮测试用静态全局对象，避免把大对象放线程栈。实际ARM布局尚未编译，不能照搬。

| 对象 | 个数×单体 / 合计字节 | 生命周期 |
|---|---:|---|
| H1解码group | 32B | 固定id/pcm4/flags/reserved，无float |
| descriptor | 152B | 帧封闭后不变；结果复制；这是C内存布局不是传输ABI |
| input | 8×9040=72320 | 包数据8000、侧带1000及所有权/token；FREE→READY→HELD→FREE，失败留HELD |
| output frame | 2×32960=65920 | READY→HELD→FREE；revoked不允许新消费，不强制覆写借用 |
| sliding window | 32768 | 独立1024组，帧发布复制后memmove保留512组；错误计数隔离旧内容，无需全存储清零 |
| result | 4×208=832 | PENDING→COMMITTED→USED→FREE，或INVALID→FREE；晚错撤销；frame可独立拥有 |
| audit | 64条=6656 | 明确ack前不覆盖，满则故障；另有last_event及累计reason |
| 整个bridge | **178856B，8B对齐** | 包括config/hooks/计数/填充；其余控制开销已在sizeof内 |

组件之和≤sizeof及sizeof<1MiB由C断言实际检查，但**不是把对象放进现有RX区域的授权或地址验证**。本体还没有DMA槽、cacheline guard、Xilinx驱动、算法内部缓存；不能直接代替0ab的202816B方案或与它相加。未使用真实DDR地址，未改链接脚本。测试输出明确LE序列化，不直接写C结构体padding给比较器。

正常路径每输入组复制32B并解码，原包自有复制保证调用者释放不会悬挂；每发布一帧复制32768B、移动16384B重叠区。两个输出槽含消费者正在处理的槽，不是“2个等待+1个处理”。无消费时第3帧发布显式失败；结果不释放时第5个事务显式失败。

输入环8×250=2000组仅在空环前提下对应约41.667ms原始输入容量；不能据此承诺任意停顿可接受。输出帧满时pump立即报错，不无限阻塞；调用者若暂停pump，后续enqueue会填满输入环并报错。长期平均服务慢于输入无有限队列能修复。审计积压也有独立64条容量，不忽略这条服务路径。

每次主机进程耗时已记录commands.json，只用于本机观察，包含进程启动/文件输出；没有将其换算为Cortex-A9 WCET或DMA吞吐。缺PS真实执行、cache维护、DDR/AXI仲裁、时钟锚与中断/轮询服务界，故**REALTIME_BLOCKED**。

后续生产仍需：明确ARM结构体与对齐；将输入环/帧/结果映射到不重叠区域并绑定ELF/map；验证DMA所有权/cache屏障和异常排空；实现同session采样时钟锚；单线程worker与ISR事件队列/原子发布；给全部服务和最坏积压上界。本轮没有提前做这些工程变更。
