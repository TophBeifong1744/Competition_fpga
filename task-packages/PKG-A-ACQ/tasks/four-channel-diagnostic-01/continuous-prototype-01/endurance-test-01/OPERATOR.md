# 当前整阶段：安装E1测试修改稿，接入检查，先不Build/Run

目标应用仅为 F:/College/verilog_digital_system/Vitis/four_mic_endurance。continuous_platform、原four_mic_continuous及Vivado one都不动。

## 在Vitis/文件管理器执行

1. 将本目录proposed-src/continuous下3个文件复制到新应用src/continuous，替换副本中的同名文件。不要复制进原four_mic_continuous。
2. 将proposed-src/UserConfig.cmake复制到新应用src/UserConfig.cmake。这里USER_COMPILE_SOURCES只列main.c，优化仍O2，保留memory.map输出及原链接脚本路径。
3. 保留新应用原main.c（include两个.c），保留lscript.ld及平台配置，不导入额外独立编译源。
4. 打开新应用src/CMakeLists.txt，在最后一个endif()之后空一行，追加下面三行。不要添加第二个endif，也不使用C1旧hook：

```cmake
# BEGIN E1 ENDURANCE ENTRY
include("E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/endurance-test-01/vitis_gate.cmake")
# END E1 ENDURANCE ENTRY
```

5. 保存，确认应用名仍four_mic_endurance，USER_COMPILE_SOURCES只有main.c。本阶段不要Build或Run；告诉Codex“修改稿已接入”，进行只读pre检查。

## 易错点和含义

- 当前副本的UserConfig确实自动列入了continuous_core.c/main_continuous.c；若Vitis再次添加，先从编译源列表去掉两项，不删文件，不改main.c的include来绕开。
- 调度：session0是300秒/14400000组；session1～10各10秒/480000组。它们不是一条400秒连续录音，不拼接；只有session0用于5分钟连续段。
- DMA一次初始化，正常段间仅RUN低→排空→统计输出及等待→RUN高。故障后不进入下一段；DMA复位只属于已失败后的静止处理，不计入正常启停成功。
- 数据仍逐包回收。保护区、RX_BASE/RX_LIMIT、每包长度都不改，不能用扩大DDR解决延长运行。
- 原计时修复入口不认识E1副本/长段，这是预期限制；不要关闭校验、修改旧POLICY或旧freeze来放行。
- 软件模型和合同变异测试已经由Codex完成；本次没有ARM编译结果，不能提前写ELF通过。

## 后续门槛（现在不执行）

B入口放行及pre检查后，用户在Vitis对新应用Clean/Build，保存完整输出；正常链接末尾应出现E1_ARTIFACT_PASS_NOT_LOAD_NOT_BOARD。随后核对新ELF/map及创建的新应用运行配置；禁止使用原应用旧ELF路径。真实运行操作单在这些检查完成后给出，本阶段不先下载板卡。

回退：原four_mic_continuous仍可用于其已核对的历史范围；本候选所有修改限新应用。不要把E1候选覆盖到原应用。
