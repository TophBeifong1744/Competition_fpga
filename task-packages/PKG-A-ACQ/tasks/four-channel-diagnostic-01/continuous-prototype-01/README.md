# 四路连续采集最小原型 C1

2026-09-15：候选实现、功能仿真、实际ARM编译、Vivado综合/实现/bit/XSA构建已完成。**实板未执行，下一步由拓芙按[上板操作单](BOARD-RUN.md)加载一次，完成两段各至少10秒、含停止和重新启动的测试。**不是M1、H3或B独立验收通过。

本地共享基线HEAD为57c50e6c99731cd57e7738ac91b02f985ad229b1；未切换、提交、推送、合并。保留其他Skill/任务未提交工作。实际外部one、c_adapter_platform和four_mic_capture仍为旧短抓取版本，构建器验证其输入哈希未变。

## 交付入口

- [接口、停止与DDR所有权合同](CONTRACT.md)
- [一次上板任务及回退](BOARD-RUN.md)
- [复跑命令](REPRODUCE.md)
- [实际测试与限制](RESULTS.md)、[失败记录](FAILURES.md)
- [可带回工作执行的摘要](HANDOFF.md)
- [配套bit/ELF/XSA、PS初始化和map](delivery-01/release/)、[产物SHA-256](delivery-01/release/SHA256.json)
- [源码](rtl/)、[PS源码](ps/)、[自检TB](sim/)、[软件与入口测试](tests/)
- [原始日志与报告](delivery-01/evidence/)、[完整历史构建/失败快照索引](delivery-01/HISTORY.json)
- [原四麦短抓取的独立回退副本](delivery-01/rollback-short/)

新包在当前任务下独立保存，不覆盖任何旧录音。当前PS仍为Cortex-A9 #0 standalone C、simple DMA S2MM→DDR；没有PYNQ、DAC、DOA/DAS或实时音频输出。在线检查后回收两槽，不把结束时DDR剩余内容当完整10秒录音。

## 改动范围

1. 候选pcm4_continuous_axis支持持续250组/包、RUN低电平请求完整包停止并排空；原始ID来自未改的前端。fatal状态跨正常重启保留，错误后必须显式复位恢复。
2. 候选BD仅将start输入接到GPIO电平，旁路旧start_pulse；四CLOCK/DATA、PS/DMA地址和时钟配置不变。纯Verilog顶层可用于BD。
3. PS两槽各8000字节+64字节guard，总16128字节，仍在[0x01000000,0x01100000)。实际.o/ELF合同、所有链接区段和已知源码体一起校验，拒绝未知配置。
4. 使用xilinx-suite指导的分阶段验证；本机Windows Script Host受限时改用Vivado直接综合/布局布线命令，没有跳过DRC或放宽时序。XSA仅含硬件描述，配套bit显式单独加载。

## 当前停止点

只待实板两段日志及后续工作执行/B检查。功能和内部时序结果不代替缓存一致性、真实调度延迟、连续10秒或实物电气测试；不宣称一小时无丢样。外部CLOCK/DATA窗口仍沿用统一风险记录CBR-01，未新增精细测量门槛。
