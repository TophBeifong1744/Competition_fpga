# 首次连续实板日志：传输自检成功，计时换算待修

日期：2026-09-15。操作者：拓芙。范围：用户在原 F 盘 one 完成构建、新建 continuous_platform / four_mic_continuous 后执行的首次两段运行。不是独立验收。

## 原件与实际结果

原始串口为 `F:/College/verilog_digital_system/Vitis/1.log`，本目录完整复制并核对 SHA-256；没有改写日志中的时间或 PASS。`prefix` 文件名表示 pre-fix（修复前），不是截断日志。另保留修改前 ELF、源码、map、编译命令及实际 BSP 频率宏。

| 项目 | session 0 | session 1 |
| --- | --- | --- |
| 程序结果 | OK | OK |
| 组数 | 1920250 | 1920250 |
| 包数（每包250组） | 7681 | 7681 |
| 累计在线检查字节 | 61448000 | 61448000 |
| 原始首编号(hex) | 3B80 | 1E5DEC |
| 原始末编号(hex) | 1D8879 | 3BAAE5 |
| 软件打印 capture_command_us（有误） | 10000009 | 10000008 |
| 按配置48kHz由组数推导时长 | 40.0052083 s | 40.0052083 s |

两段分别核对：末编号减首编号加一等于组数，包数乘250等于组数，组数乘32等于字节数。段间编号有意留间隔，不拼接为一段。

两段结束均有 stop_sent=1、SOURCE=C100000A、DMA_SR=00001002、active=-1、owners=0,0。依据当前代码，这是请求停止、排空后两槽释放、无被检查到的 DMA / 编号 / 范围 / 非法flags / guard 等故障的程序自检证据；两段之间由同一程序自动重启采集，不复位 PS/PL/DMA。四路均有非零幅度变化，clip_flags均为0。没有保存完整连续音频，不能把回收后的两槽解释为完整录音。

日志中的 bad_group / bad_lane / bad_value 每次检查正常样本时也更新；result=OK 下它们是最终检查位置，不是新增错误。

## 根因（本次实际编译器已复现）

实际 `main_continuous.c:27` 使用：

```c
return (uint64_t)t*1000000U/COUNTS_PER_SECOND;
```

实际 BSP 的 `xtimer_config.h` 定义 COUNTS_PER_SECOND 为 XSLEEPTIMER_FREQ，再定义后者为未加括号的 `XPAR_CPU_CORE_CLOCK_FREQ_HZ/2`。CPU 宏为666666687。使用实际 ARM GCC 对当前源码只做预处理，返回式展开为：

```c
return (uint64_t)t*1000000U/666666687/2;
```

除法左结合，因此计时约缩小四倍。本目录不改 BSP 宏；应用调用处应把整个频率表达式括起来。对内存中的拟修文本再做预处理，结果为：

```c
return (uint64_t)t*1000000U/(666666687/2);
```

使用每秒333333343计数的算术检查：理想经过1/10/40秒，旧公式分别得到249999/2499999/9999999微秒；括号修正后得到1000000/10000000/40000000微秒。此为预处理与算术检查，不是修复后的 ELF 编译或实板测试。BSP globaltimer_sleep_zynq.c 的 XTime_GetTime 读取64位原始全局计数，sleep 路径先计算独立的 CpuFreq/2，故不应把段间 usleep 也自动解释为同一错误。

影响：capture_command_us、drain_us、max_check_us、max_arm_gap_us 及基于 now_us 的软件超时均不应按原打印值作为真实微秒证据。组数推导支持每段约40秒，但未单独测量墙钟或采样时钟，不能将推导时长称为独立实测。

## 下一步（用户在 Vitis 操作）

1. 只修改 `F:/College/verilog_digital_system/Vitis/four_mic_continuous/src/continuous/main_continuous.c` 的 now_us：分母改为 `(COUNTS_PER_SECOND)`。不改 BSP、RUN_US、MIN_GROUPS、DDR、RTL 或 BD。
2. Build 当前应用，使用当前 four_mic_continuous Run 配置。保持已匹配的连续采集 bit，不切回短抓取/单麦配置。Vivado及平台不需要因这一行重建。
3. 先开启完整串口保存，再点一次 Run；程序自动完成两段各约10秒、停止排空及一次采集重启。段间不人工复位、不再次 Run。
4. 新日志使用 `continuous_c1_timerfix_20260915_02.log`，不要覆盖本次原件。预期每段约48万组（包边界可略多），capture_command_us约10000000。观察实际等待时长是否相符；如 FAIL 保留全部输出，勿反复 Run 覆盖。

## 版本与验证边界

- ELF：本目录 four_mic_continuous_prefix.elf；build Sep 15 2026 20:13:41；SHA见SHA256SUMS.txt。
- 本次检查的 Vitis launch bit：`F:/College/verilog_digital_system/Vitis/four_mic_continuous/_ide/bitstream/system_continuous_20260915.bit`；SHA-256 `b15991bc0f8595970361be553b542e334dbb7dca268c01864ecd80fcffbbffaf`。对应原one当天的连续采集构建，不是旧单麦。
- map程序末端0x00112640；RX保留区[0x01000000,0x01100000)，两槽实际占用16128字节。累计检查字节不是同时占用的DDR容量。
- 本轮只读检查 F 盘，新增本目录归档；没有修改用户工程、编译、下载或代替用户操作板卡。未提交/推送。
- 功能：首次实板传输/停启自检已有记录；计时缺陷未修复重跑。时序：引用用户此前构建核对结果，本次未综合/实现。声学/独立验收/一小时长稳：未执行或不在本次结论内。
- 旧 delivery-01、ps 源码及历史测试记录未覆盖；后续修复需记录新的源码/ELF哈希及复测，不能将旧测试重新标为已覆盖此宏展开问题。

## 复现预处理

下列命令只向控制台输出，不生成新固件或修改工程：

```powershell
& 'F:/AMD/2025.2/Vitis/gnu/aarch32/nt/gcc-arm-none-eabi/bin/arm-none-eabi-gcc.exe' -E -P -DSDT -mcpu=cortex-a9 -mfpu=vfpv3 -mfloat-abi=hard -O2 -std=c11 -U__clang__ -I 'F:/College/verilog_digital_system/Vitis/four_mic_continuous/src' -isystem 'F:/College/verilog_digital_system/Vitis/continuous_platform/export/continuous_platform/sw/standalone_ps7_cortexa9_0/include' 'F:/College/verilog_digital_system/Vitis/four_mic_continuous/src/main.c' | Select-String -Pattern '^static uint64_t now_us'
```

修正后再运行该命令应看到带括号的分母；本次修复前/拟修文本结果已如上记录。
