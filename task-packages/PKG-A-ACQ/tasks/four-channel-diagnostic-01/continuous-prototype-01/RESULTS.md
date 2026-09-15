# 实际执行结果（2026-09-15）

## 1. 功能仿真：通过，非实板

实际工具XSim/Vivado 2025.2。最终源与构建源逐字节核对一致。

|检查|本轮实际结果|原始证据|
|---|---|---|
|4组/包、16组FIFO，随机背压、逐字/通道/ID、TLAST、停止及重启|5894次断言检查通过|delivery-01/evidence/simulation/logs/simulate.log|
|真实250组/包、1024组FIFO，同类检查|314127次断言检查通过；主要轮转段4250组/17包，另有零组停止、积压排空、故障注入|delivery-01/evidence/simulation/logs/production-simulate.log|
|四CLOCK同源/复位、前端valid同步、停止区间原ID继续、通道打包|67个前端有效组，其中56组捕获并检查；85771周期|delivery-01/evidence/simulation/logs/frontend-simulate.log|

overflow、部分通道valid及饱和诊断状态是**人为故障/状态注入**，要求锁存错误、禁用正常完成和无复位重启；不是实际硬件丢样证据。TB验证AXIS握手和输入输出匹配；并未仿真整个Zynq处理器或真实麦克风。

## 2. PS及构建安全检查

- 实际连续接收C循环在主机上编译执行：16个确定性场景通过。正常场景完成两次各至少480000组，时间源为**模拟时钟**；检查跨32位ID进位、两槽交替和所有权，不代表实板10秒。
- 负例覆盖DMA超时、无完整包超时、停止不完成超时、错号、guard破坏、signed24越界、flags/reserved异常、错误长度、旧ABI、源溢出/失步、DMA错误、arm失败、消费者50ms延迟导致FIFO预算超限、非FREE槽拒绝开始。失败对象再次调用仍保持原错误。
- 入口10项检查（含BASE/LIMIT/分包/guard源码改变拒绝），以及保留的原34项安全测试，本轮实际运行通过。没有把其他B补充测试计入本轮。
- 实际Cortex-A9 gcc使用SDT BSP、-O2，编译/链接通过；end=0x00112640。检查实际预处理单元、.o和ELF常量相同、全部ALLOC/PT_LOAD/heap/stack与RX不重叠。两槽最后guard终点为0x01003F00，没有扩大1MiB保留区。
- 真实BSP一致性检查：PS、DMA、GPIO、Clock Wizard全部参数/地址记录及ps7_init.c一致。只复用BSP，未声称重新生成或独立审核了BSP。

证据：delivery-01/evidence/ps-model/logs/test.log、safety/logs/、build/logs/ps-*.log、build/ps/contract-result.json、build/reports/bsp-binding.json。

## 3. 实际综合、实现与时序

最终完整运行：continuous-work12；Vivado 2025.2，xc7z020clg400-2。Validate Design、直接synth_design、opt_design、place_design、route_design、bit和硬件描述XSA全部完成。没有复用旧DCP作为本轮结果。run10的成功bit和失败XSA步骤另存历史；export11只导出，不算新的综合/实现。

|指标|实际值|
|---|---|
|WNS / TNS|5.281 ns / 0 ns|
|WHS / THS|0.023 ns / 0 ns|
|WPWS / TPWS|3.000 ns / 0 ns|
|无时钟端点 / 无约束内部端点|0 / 0|
|总LUT / FF|8329 / 4368|
|RAMB36 / RAMB18 / DSP|1 / 1 / 0|
|综合后黑盒|0|

原有约束仍有**4个输入无input delay、4个输出无output delay**。内部已声明时序满足，不等于外部麦克风采样窗口或四路物理偏斜已保证。沿用docs/deferred-acquisition-risks.md的外部时序条目及CBR-01，不补造测量、不放宽约束。

DRC有6条warning（PDCN-1569×5、RTSTAT-10×1）和2条advisory（REQP-165/181）；methodology有LUTAR-1×5。均在原DMA/互联IP相关层次，报告原件保留，不能写成“所有警告为零”。bitgen前DRC无error。

报告io.rpt确认：Y9/W10/W14/V15分别为pdm_data[0..3]输入，V11/Y13/U14/V12为四CLOCK输出，均LVCMOS33。没有把旧单麦W10输出约束带入候选。

## 4. 实板：未执行

本次没有连接目标、下载、采样或声学分析。实际DMA/CPU并行调度、缓存维护、guard、两段各≥10秒及无复位重启，要由拓芙运行BOARD-RUN.md后核对日志。主机时间与XSim周期不能充当这些证据。

## 5. 配套产物

最终配套bit SHA-256：`44bf76e1babb0a094b0289775d0ce01e02de004b47b7a217e7089bfdb579dcfe`。

最终ELF SHA-256：`445f7c7ed14c6c5d16fad41b202c811ccc64dfdc2a8da64613de7f5faf223322`。

XSA SHA-256：`d3d5f59aa17ad5a7d810c1345e9c932a38c3c9d5412111ff0f605d2c4f436e81`，**不内嵌bit**。以release/SHA256.json为完整清单，不能按相似文件名选择旧产物。
