# 下一大步：给现有Vitis应用接入检查，再Clean、Build

目标：每次重新编译都先拒绝旧计时源码/错配依赖，链接后核对真实对象与ELF。复用 continuous_platform / four_mic_continuous；不改Vivado、平台、采集源码或DDR。

## 你在Vitis完成

1. 打开 `F:/College/verilog_digital_system/Vitis/four_mic_continuous/src/CMakeLists.txt`，确认是应用src下的文件，不是平台，也不是build自动生成文件。
2. 在文件最后一个 `endif()` **后面**空一行，原内容不动，追加：

```cmake
# BEGIN C1 TIMERFIX ENTRY
include("E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/timerfixed-entry-01/vitis_gate.cmake")
# END C1 TIMERFIX ENTRY
```

3. 保存。只对 `four_mic_continuous` 应用执行 **Clean，再Build**；不要Clean平台，也不要修改UserConfig或把嵌套两个C再加入独立编译。旧运行ELF/对象/日志已有冻结归档，Clean针对当前可再生构建目录。
4. 保存完整构建输出。成功时应依次出现 `PRECHECK_ONLY` 和 `ARTIFACT_CHECK_PASS_NOT_BOARD`，最终Vitis Build成功；`PRECHECK_ONLY`单独出现不算新产物检查通过。
5. **不要点Run。** 将完整构建输出交回，并告知编译完成。我会只读检查应用build和新增c1_checks，确认新对象确实编译、ELF除数333333343、RX合同及加载配置匹配。

## 易错点

- 三行放在最后的endif之后，不放进旧if块，不新增endif；之前的嵌套错误不要再次引入。
- 不改main_continuous.c，它已经是正确的括号修复版。不要从根ps或delivery-01复制旧文件。
- 不切回four_mic_capture、单麦平台或旧Run配置；本次正确配置名为four_mic_continuous_app_hw_1。
- 发现REJECTED时保留完整输出和c1_checks，不删除检查入口强行编译；先交回实际错误。
- Python位置可通过CMake变量C1_PYTHON指定；当前默认已核实存在。C1_PLATFORM/C1_RECORD_ROOT也是参数。首版限当前已核对工具/BSP布局，变更时须重新核实，不能无条件改POLICY放行。
- CMake检查脚本位于仓库含空格路径，include及命令参数已加引号；实际Vivado/Vitis工程仍在原F盘无空格路径。本轮没有新建工程副本。

## 以后需要受检加载时（本轮不执行）

使用本目录load_timerfixed.tcl，不使用旧load_candidate.tcl。过程参数依次为Python、应用根目录、平台根目录、ARM工具bin、检查记录根目录、dry_run。默认dry_run=1只检查；显式0才复位和加载。

在Vitis的XSDB Console中定义和执行dry-run的示例：

```tcl
source {E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/timerfixed-entry-01/load_timerfixed.tcl}
c1_timerfixed_load {C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe} {F:/College/verilog_digital_system/Vitis/four_mic_continuous} {F:/College/verilog_digital_system/Vitis/continuous_platform} {F:/AMD/2025.2/Vitis/gnu/aarch32/nt/gcc-arm-none-eabi/bin} {F:/College/verilog_digital_system/Vitis/four_mic_continuous/c1_checks}
```

dry-run会重新校验实际产物及之前的post记录，打印 `DRY_RUN: no connect/reset/program/download`；检查失败不接触板卡。多个JTAG目标时不要执行真实加载，需要另行明确目标选择。当前不要求操作这一段或重复10秒实录。
