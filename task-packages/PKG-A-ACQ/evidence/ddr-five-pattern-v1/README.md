# DDR 五模式自检 v1：交付记录

2026-09-08。范围为 PKG-A-ACQ 中最小 PS 平台的 DDR 自检，状态：用户报告三次冷启动通过、作者侧源码/ELF 检查完成，待 B 技术复核；不是整个采集包验收。

## 结果与证据层次

- 测试区 [0x01000000,0x01100000)，1 MiB；每模式 262144 个 32 位字。
- 五模式：ZERO、ONES、AA、55、ADDRESS（写入当前字的地址）。每模式先写满区域再读回；错误计数返回，任一失败停止后续模式。
- 用户确认三次输出相同：5/5、零错误，详见 [用户回传](user-reported-runs.md)。本轮没有再次上板运行或直接观测冷启动。
- 链接脚本把程序 DDR 可分配范围限制为 [0x00100000,0x01000000)，另设测试区。ELF LOAD 段终止于 0x001119C0，含堆/栈，不与测试区重叠；符号起止和日志一致。
- main 调用 Xil_DCacheFlush、Xil_DCacheDisable 与 dsb；volatile 指针逐字读写。实际 ELF 的关闭逻辑涵盖 L1 数据缓存和共享 L2。前提是单核非 AMP，核1和其他主设备不访问测试区；本轮没有独立板上核验该运行前提。

## 源码与构建检查

源码 mtime 为 20:12:09，ELF 为 20:10:42（文件系统本地时间）。不能只凭时间宣称源码对应。

使用原 build/compile_commands.json 参数在独立临时目录重新编译 main.c，并对新旧 main.c.obj 运行 objdump -dr（仅去掉文件名头行）比较：指令与重定位输出无差异。初次工具调用因带空格的输出路径造成依赖文件写入失败；改在临时目录使用相对输出路径后编译成功，未改 F 盘工程。此检查不是完整重链接或完整源码/BSP 可复现验收。

ELF program headers、符号表和缓存反汇编保存在本目录。没有找到链接 map，使用 ELF 实际 LOAD 段和符号替代布局核查；不伪造 map 文件。

## 文件与复现入口

- 源码/链接/构建描述：../../payload/ps/ddr_test/src/。
- artifacts/ddr_test.elf：当前构建 ELF 原始字节。
- artifacts/system_wrapper.xsa：实际 ps_platform 使用的 XSA，hw 与 export 副本哈希一致；包含 bitstream。
- artifacts/system_wrapper.bit、ps7_init.tcl：当前 ddr_test JTAG 配置所引用的文件，单独保存方便核对。
- 原工程：F:/College/verilog_digital_system/Vitis/ddr_test；工具目录为 AMD/Vitis 2025.2，处理器 ps7_cortexa9_0，standalone。

在 Vitis 2025.2 中基于随附 XSA 生成 standalone Cortex-A9 核0平台，再导入所附应用源文件和链接脚本。app.yaml 保存的是原环境路径，需在新机器重新关联平台；不把旧绝对路径当通用构建入口。使用同版工具链/BSP，重建后重新检查 LOAD 段、符号和缓存配置；新 ELF 是新版本，应重新记录哈希和测试。

已保存现有 JTAG 初始化文件与 bit/ELF，具体下载由操作者核对设备后执行；本包不自动编程、不上电。测试是破坏性写入，不得用于运行中的业务内存；确认核1/DMA无并发访问后，每次断电重新初始化并运行，预期见用户回传。以后应保存逐轮串口原文件、时间与 ELF 哈希。

## 不能由此推导

未验证 DDR 全容量、全部地址线/数据线故障、不同温度/频率、压力并发或长期稳定性；三轮不是一小时长稳。串口输出不等于双向回显验收。未验证 PYNQ、DMA、麦克风采集、H2、H3 或声学效果。完整 PKG-A-ACQ 继续进行，只有 B 明确复核准确版本后才能合入。
