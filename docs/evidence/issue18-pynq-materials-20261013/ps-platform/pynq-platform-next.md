# C：PYNQ 下一步操作单

2026-10-15收件核验版。两个厂商包已收到、CRC检查通过；AI已核文件和配置，**不用你再运行校验脚本，也不用重搭one或live_loop工程**。完整依据见 [厂商平台核验](vendor-platform-audit.md)。

## 现在到哪一步

| 项目 | 状态 |
|---|---|
| PYNQ原件 | 已收到；镜像内确为PYNQ2.7.0、Python3.8、Linux5.4.0-xilinx-v2020.2 |
| DDR | one、历史采集XSA、厂商base都使用 `MT41J256M16 RE-125`，32位、约533MHz；已有依据可复用 |
| 旧one | 有PS/DDR；CPU约666MHz，但SD/网口禁用、IO PLL1800MHz；原器件为-2 |
| 当前live_loop | 2025.2 / -1，已有PL链路、引脚和61.44MHz时钟；无PS/DDR启动配置 |
| 首次启动 | **先修正启动包再做。** 厂商镜像FSBL及设备树含约766MHz CPU配置，已确认-1的上限为667MHz |
| 当前声源工程Overlay | A/B尚未交齐与当前控制/数据接口匹配的bit/HWH和可运行板端adapter；厂商base不能代替 |

## 你现在可以做的事

1. 保留下载的两个ZIP，不需要再下载整套资料盘。
2. 准备一张可用于本项目的 **16GB或更大SD卡**和读卡器；镜像展开为8090591232字节。当前先不写卡、不切启动模式、不运行厂商Notebook。
3. 保留现有live_loop工程和接线。无需为PYNQ重新导入四麦/算法/舵机，也不要运行仍是占位的 `prepare_bd.tcl`。

当前没有必须由你手动完成的Vivado配置步骤。先由A/E沿原工程完成下面的增量，再交你执行构建/启动。文件核对继续由AI负责。

## A/E 与 B 接着做什么

- **A/E工程增量**：参考one保留DDR/UART和约666.7MHz CPU目标；采用已核的SD0 MIO40..45、CD MIO10、ENET0 MIO16..27和MDIO52..53；按实际-1重新生成PS配置，IO PLL及分频须在额定内。保留现有PL链路，接入实际CPU桥；给准确GUI入口或已完成增量，不另搭第三套总工程。
- **启动文件**：用匹配PS配置正式生成FSBL/BOOT.BIN，同步设备树CPU频率并重新打包IMAGE.UB，提供来源与哈希。不能只改Linux启动后的频率，也不能手改二进制字节。本轮没有生成或声称已有修正版。
- **B软件接合**：以本次镜像PYNQ/NumPy/内核和源码身份为候选依据，沿原adapter绑定地址、IRQ或轮询、buffer/cache、writer退休和恢复。现有离线软件通过不等于板端通过。
- **接合交付**：当前准确bit/HWH、适用XSA、控制入口、原始数据格式、必要资源/时序与安全参数齐备后，再做声源链测试；不拿厂商GPIO/DMA示例替代当前工程。

详细参数、原件路径、时钟差异和A/B状态均在 [核验报告](vendor-platform-audit.md)；完整参数及接续成果见[交付入口](HANDOFF-20261015.md)，你无需逐项人工对照。

## 收到适配包后，你的测试顺序

下面是后续顺序，**当前均未执行**。收到修正版后AI会补准确文件名和该板已有启动拨码/接线图；本单不猜拨码位置。

1. 由你用已确定的镜像写卡工具将核准 `.img` 写入指定SD卡，并启用写后校验。写卡会清空所选卡，按容量核对目标卡，不要选择电脑系统盘。
2. 按这块板的说明设置SD启动，连接已核PS UART0控制台（115200），保持执行器禁用，保存从启动开始的完整串口日志。此阶段只验系统启动。
3. 启动成功后，把 `tools/pynq_platform/collect_runtime.py` 放到板端，在后续PYNQ应用实际使用的Python环境中运行：

   ```sh
   python3 collect_runtime.py --out pynq-runtime-01.json
   ```

   输出名必须未存在。它只读系统/软件元数据，不加载Overlay或操作寄存器/DMA。返回JSON和启动日志，由AI核版本、缺项和身份。
4. A/B同候选产物已核齐后，按实际入口先验Overlay身份和原始采集，再验STOP/重启/超时/复位和buffer退休，最后测试持续方向更新及安全范围内跟随。保留原日志、raw和实际声源位置，数据交B分析。

## 文件位置

```text
原ZIP：D:\BaiduNetdiskDownload\ZYNQ_7020_PYNQ.zip
       D:\BaiduNetdiskDownload\ZYNQ-7020-2.7.0.zip

已解出的原始IMG（仍待-1启动适配）：
C:\Users\hsc\Desktop\fpga_clone\Competition_fpga\codex_out\vendor-pynq-7020\ZYNQ-7020-2.7.0.img

AI核验和原件摘取：
仓库\codex_out\i18-vendor-inspection-20261015\

本机原工程：
D:\vavido_project\i17_live_loop\project\par\i17_live_loop\i17_live_loop.xpr
```

上板尚未通过，也未关闭#18。主要剩余是适配后的启动链和A/B当前工程接合，不需要重跑旧的电脑Python角度测试。
