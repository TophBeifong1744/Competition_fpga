# 当前一大步：接入 S1 六秒留存稿，Clean 后 Build，先不 Run

目标：在原 four_mic_endurance 中连续录约6秒；保留原始四路数据，停止并排空后从DDR导出。continuous_platform、one、bit/XSA、链接脚本及DMA两槽不变。不是重新执行五分钟耐久。

## 1. 先保存可恢复的 E1

先在 Vitis 保存文件，确保没有采集正在运行。在资源管理器中复制整个
`F:/College/verilog_digital_system/Vitis/four_mic_endurance`
到一个新的备份位置，例如
`F:/College/verilog_digital_system/Vitis_backup/four_mic_endurance_before_s1_20260917`。
备份已有同名目录时另取时间后缀，不合并覆盖。确认备份含 src、_ide、vitis-comp.json，以及 build 内原 ELF、memory.map 和 main.c.obj。

这只是恢复备份，不导入为新的活动应用。保留原 e1_checks 和串口日志。

## 2. 合并修改稿到原 src

把本目录 [proposed-src](proposed-src/) 的**内容**复制到：

`F:/College/verilog_digital_system/Vitis/four_mic_endurance/src`

合并目录，仅替换/新增下列7个文件；不要删除整个 src，也不要复制成 src/proposed-src 或 src/src：

| 文件 | 操作 / 意义 |
| --- | --- |
| main.c | 替换；仍是唯一编译的 C 文件，包含三个实现文件。 |
| continuous/continuous_core.h | 替换；固定6秒/288000组及保存回调、失败码。 |
| continuous/continuous_core.c | 替换；验证成功后、释放槽之前完成复制；仅接受本次单段配置。 |
| continuous/main_continuous.c | 替换；单段采集、9.6MB静态留存、保护/最终读回、flush、实际导出地址。 |
| continuous/scene_store.h | 新增；留存容量、保护区及接口。 |
| continuous/scene_store.c | 新增；有界原字节复制、首尾保护、FNV。 |
| CMakeLists.txt | 替换；与已核对的原文件相比，仅末尾 E1 检查入口改为本批 S1 检查入口。 |

**不要改** UserConfig.cmake、lscript.ld、Empty_applicationExample.cmake、BSP、优化级别、计时函数或 DDR 范围。不要把 continuous 下的 .c 再添加为独立编译源，避免重复定义。

新 CMakeLists.txt 末尾应只有这一组新入口，旧 E1 include 不应并存：

```cmake
# BEGIN S1 SCENE ENTRY
include("E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/background-target-stop-20260917/vitis_gate.cmake")
# END S1 SCENE ENTRY
```

检查器本批固定当前实际应用/平台/工具路径；不声称通用可移植入口。不要复制修改检查器参数规避 REJECTED。

## 3. Vitis 中 Clean，然后 Build

回到 **four_mic_endurance** 应用，刷新/保存文件；执行该应用的 **Clean**，再 **Build**。
不要 Clean 平台，不需要 Vivado，不生成新bit或XSA。

完成标志：

```text
S1_ARTIFACT_PASS_NOT_LOAD_NOT_BOARD ...
Build Finished successfully
```

新检查记录写入原应用 **scene_checks**，旧 **e1_checks** 不覆盖。程序 .bss 会增加约9.6MB，这是预期的原始录音留存区，不是DMA RX扩容。实际地址只能以新ELF/map及后续READY日志为准。

若仍显示 E1_ARTIFACT_PASS，说明入口未切换；若有 REJECTED 或编译错误，保留完整输出，不删检查记录、不关闭检查器、不手动扩大链接区。发回首个错误及证据路径。

## 本阶段停止点

**先不要点击 Run，也不要沿用旧的 0x01000000 / 32000组 导出命令。**

完成后提供 Build 输出即可；Codex将读取：

- build/four_mic_endurance.elf、对应 main.c.obj、memory.map；
- scene_checks 最新前置/产物记录；
- 实际 src、_ide/launch.json、匹配bit/初始化脚本。

核对真实计时除数、全部程序/堆栈与留存区边界、编译链接参数及加载版本后，才给出一次完整的“背景—说话—停止说话”录制与导出操作单。样本活动起止需人工近似标注/播放记录，不冒充精确样本真值。

## 回退

停止运行、关闭应用后，先把当前 S1 应用目录另行完整保留，再将备份复制回原路径。恢复原E1源码及CMake检查入口后重新Clean/Build并核对原配套bit/加载配置；不要把不同版本的源码、检查记录和缓存ELF混搭。整个过程不需要恢复/改写one工程。
