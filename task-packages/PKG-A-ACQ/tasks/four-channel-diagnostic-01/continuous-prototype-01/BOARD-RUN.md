# 下一大步：一次加载，完成两段连续采集与停止/重启

上板由拓芙操作。先确认本目录README中的最终构建结果；未生成delivery-01/release或哈希不符则不要上板。不要覆盖原one/short-capture启动配置，也不要运行旧迁移脚本。

## 1. 加载前与日志

- 保持当前已核对的C转接板四麦、供电/共地和CLOCK/DATA接线，不新增仪器测量门槛。相机等共享输出仍不得接入。不要加载旧单麦bit（旧W10输出会与新DATA2争用）。
- COM3、115200，**先开启完整串口保存**，建议`continuous_c1_20260915_01.log`。不启动旧four_mic_capture的Run配置；它会换回短抓取bit/ELF。
- 用下面的只读校验命令核对待加载文件；Python路径可换成本机已有Python 3.11+，不需安装新环境。

```powershell
& 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B `
  'E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/check_release.py' `
  --release 'E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/delivery-01/release'
if ($LASTEXITCODE -ne 0) { throw '版本校验失败，不加载' }
```

## 2. 在现有XSDB控制台加载候选

这两行是**你执行的上板操作**。第一行只定义过程，第二行才进行一次系统复位、加载配套bit/PS初始化/ELF并启动。连接多个JTAG目标时先只保留本次目标，选择歧义要停止处理。

```tcl
source {E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/load_candidate.tcl}
continuous_load {E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/delivery-01/release}
```

本轮XSA为硬件描述，**不内嵌bit**；脚本显式加载同目录`system_continuous.bit`，不能让Vitis自动挑历史bit。不要自行修改GROUPS/LIMIT或编译宏。

## 3. 等待一轮自动测试，交回完整日志

- 预期先看到`FOUR CONTINUOUS C1 prototype`，随后`START session=0`。连续段内约10秒没有UART输出是刻意安排，不是卡住。
- session 0应检查至少480000组（48kHz约10秒），请求LOW并在完整包边界停止排空，打印独立结果。
- 休息1秒后，同一程序再次拉高RUN，执行session 1，再停止排空。**这两段之间不复位PS/PL/DMA，也不点击第二次Run。**整个过程通常二十余秒，加串口输出时间。
- 最后应出现`CONTINUOUS_TWO_SESSIONS_PASS_NOT_ACCEPTANCE`。这只是程序自检标记；带回完整日志后还要核对编号跨度、包长、DMA/源状态、guard和计时，之后交工作执行/B。
- 本轮不用保存10秒BIN或WAV；槽在检查后反复回收，不能把结束时两个槽拼成10秒录音，不能套旧H1导出器。

出现FAIL、长时间停住或未打印最终标记：**保留全部串口，不反复Run覆盖现场**。程序会在失败日志后请求停止并尝试DMA reset；若`RESET_TIMEOUT DDR_NOT_STABLE`，不要把DDR导出当有效数据。需要错误缓冲时，在确认DMA复位完成后按后续诊断提示导出0x01000000起4032个32位字（16128字节，含两槽guard），只标故障快照。

回报：完整串口log、实际加载前哈希输出、是否出现两段各自OK及最终标记、有无异常。声音内容不要求标定，也不据此宣称同步精度、定位或一小时长稳。

## 回退

停止本次调试任务后，用原`four_mic_capture_app_hw_1`的完整Run流程重新加载**原四麦短抓取**bit、原PS初始化和原ELF（不是单麦）。它包含系统/PL重置，不能只换回旧ELF。原工程及冻结录音未被本候选改写；完整原始输入快照和哈希在交付evidence/build/preflight.json及历史构建压缩包中。不要把本候选源码导入原one来“回退”。
