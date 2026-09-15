# C1 连续采集候选合同

这是独立候选，未取代 short capture。数据仍为 `ss-four-record-0.1`：每组8个32位小端字为 id_lo、id_hi、mic0、mic1、mic2、mic3、flags、reserved。mic为signed24符号扩展到int32；flags低4位是逐路CIC饱和标志，其他位及reserved必须为0。无新DOA/DAS、音频后处理或坐标修改。

## 不变项及唯一BD接线改动

四个物理CLOCK仍由同一分频寄存器驱动。61.44MHz数据域、3.072MHz PDM、R=64 CIC、48kHz PCM、4096组预热、全局64位原始编号均不变。构建器逐字符核对前端整段代码与实际one；pdm_cic3.v和有效XDC从实际one复制且不改。

候选顶层仍叫four_mic_top以保留BD实例/端口，但`start`现在是**RUN电平**。仅候选BD把`four_mic_top_0/start`从`start_pulse_0/start`断开，直接接`axi_gpio_0/gpio_io_o`；原脉冲模块可留作无消费端的历史实例。GPIO宽度、地址、PS、DMA和外部端口不变。候选TOTAL_SAMPLES=32000参数仅为旧BD兼容保留，**连续模式不使用它作为停止计数**。不能将旧bit与新ELF混用。

## 开始、停止、故障

- RUN上升沿：仅在ready、空FIFO、非busy且无fatal时接受。未ready/排空中/错误后的上升沿不排队；需回LOW再发新的上升沿。
- RUN降为LOW：停止请求被锁存，完成当前**输入包**后不再存入新组；若恰在空包边界，立即停止，不制造空包。之后继续发送FIFO中所有组，最后一个真实包的TLAST握手后排空。请求锁存后再升HIGH不会撤销停止；必须排空后重新LOW→HIGH。
- 每250组/2000拍一包、8000字节，TLAST只在包最后一拍。背压期间TDATA/TKEEP/TLAST/TVALID保持；PDM/CIC不能暂停，因此超出FIFO容量必须报错。
- 原始ID在停止区间仍随CIC推进；单次连续段内必须严格+1，显式停止后重启允许间隔，不补样或重编号。
- overflow/sync_error/clip-ever及拒绝事件数仅由PL复位清除。fatal后禁止正常DONE和新开始；不能把剩余半包当成功排空。PS保留源状态、DMA状态、所有权、首错位置和最近16包状态，不自动重试。
- rejected是16位饱和的“忙时FIFO满拒绝事件”计数，不是所有未采集样本数；首错即停的本版通常只增1。停止期间未保存的组不计为错误。测试中的饱和值为状态注入，不能写成实际丢了65535组。

GPIO通道2的C1 ABI：

|位|意义|
|---|---|
|31:24|固定0xC1，新PS在写RX/启DMA前核对|
|23:8|sticky拒绝事件数|
|7|停止请求待排空|
|6|至少一个完整包已经进入FIFO，尚未全部发送|
|5|sticky四路valid失步|
|4|sticky任一路clip-ever，跨正常重启保留|
|3|已停止且FIFO空、无fatal（初始空闲也为1）|
|2|sticky溢出|
|1|前端预热完成|
|0|仍在接受输入组|

PS在确认上一DMA完成后**重读完整包状态**才挂下一DMA，不使用较早的包信用值。避免停止后的空DMA无数据可收。结束条件包括源排空、无活动DMA、所有CPU_READY槽已检查释放，而不仅是busy=0。

## DDR与缓存

|槽|DMA数据区（尾地址不含）|64字节guard（尾地址不含）|
|---|---|---|
|0|[0x01000000,0x01001F40)|[0x01001F40,0x01001F80)|
|1|[0x01001F80,0x01003EC0)|[0x01003EC0,0x01003F00)|

保留区仍是[0x01000000,0x01100000)，总使用16128字节。8000字节包和8064字节槽步长均64字节对齐。状态/trace是链接在程序区的静态对象；不分配于RX，也不允许核1、其他DMA或XSDB在运行中访问RX。

所有权：FREE→DMA_OWNED→CPU_READY→CPU_OWNED→FREE。只有FREE槽可填哨兵、flush并invalidate整个槽（含guard），完成后才交DMA。DMA完成且长度正好8000才转CPU_READY；CPU取得前invalidate，逐组检查ID/符号范围/flags/reserved/guard，检查通过才释放。失败保留CPU_OWNED/DMA_OWNED状态，不回收。下一槽DMA与前槽CPU检查可以重叠，绝不能重写前槽。simple DMA不支持两个同时活动的S2MM请求。

实际编译的同一预处理单元将地址、包长、槽数、guard、DDR范围和10秒阈值导出到常量符号；检查.o与ELF相同，扫描全部ALLOC/PT_LOAD和heap/stack，不只看end。冻结当前固定合同，不允许任意搬迁。

配置速率为1,536,000字节/秒，每包约5.208ms；1024组FIFO的满容量时间约21.333ms，不是保证可用的调度余量。PS在连续段内不打印UART；在线检查后允许回收，仅保存计数、逐路统计和最近16包状态。`max_check_us`及`max_arm_gap_us`由实板计时填充后再判断，模拟时间不能冒充实测。

## 本轮上板含义

同一ELF启动两段，每段至少480000组且RUN保持至少10秒，再停止/排空；中间等待1秒，不复位PL、PS、DMA。两段分别报告，不拼接。PC不获得完整10秒音频，不应对轮转区运行旧H1导出器。失败可导出16128字节诊断缓冲，但它包含两个槽和guard，不是连续H1。
