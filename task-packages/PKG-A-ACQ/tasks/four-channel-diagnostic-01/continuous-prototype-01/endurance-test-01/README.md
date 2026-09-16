# E1：一段连续5分钟＋10次短段启停（准备候选）

2026-09-16。用户选择复用continuous_platform，新建four_mic_endurance，并已自行建立副本。Codex仅只读核对F盘工程，在本目录准备修改建议和主机测试；没有修改实际应用、构建ARM固件、下载或运行。

状态：**待用户复制修改稿并接入检查；B对入口的放行尚未在本批确认；不能Build/Run当作已获准实板测试。** 取得B放行记录及配置检查通过后，由用户执行Vitis构建，再检查实际ELF/map/加载配置，才安排实板。

## 不变项

沿用C1四麦bit/XSA、61.44MHz数据域、四路同源CLOCK、PDM/CIC/H1及编号、两槽所有权、缓存维护。RX=[0x01000000,0x01100000)，每包250组×8字×4=8000字节，每槽额外64字节guard，步长8064，两槽16128字节。在线检查后回收，不产生完整5分钟BIN/WAV。正常段间不复位PS/PL/DMA，原four_mic_continuous和原计时修复证据不改。

## 最小实现差异

修改建议在proposed-src，由用户操作复制，未接入实际工程：

- continuous_core.h/c：新增只支持两种配置的session_run_config及const调度表；保留原session_run短段包装用于原16项回归。调度实际使用表中值；先验证配对的时限/组数，之后同时满足时限和组数才请求停止。
- 调度为300000000微秒/14400000组一次，再10000000微秒/480000组十次；段间在排空后打印统计，再等待至少1000000微秒。32位单段字节计数足够本合同，组编号仍64位。
- TIMEOUT_US保持2000000，不随长段放大；新增SESSION_TIMEOUT：达到run_us+2秒仍未达到组数时失败，避免无限等待。请求停止后的排空另限2秒，包/传输原超时保持。
- main_continuous.c：11段独立状态，初始化仅一次，逐相邻段检查原编号前进；段内逐组、逐包和guard检查不变。新增配置/汇总，11段成功后留存，首个致命错误即终止，不继续凑满次数。
- 错误统计是fail-fast的首错/失败段计数，不是出错后继续采集的累计错误率；成功段记录0次已检测致命错误，失败保留错误类别、首次数据、最近16包和寄存器。每通道clip_flags、min/max/zero仍单独报告；clip_flags不是本轮新增的致命错误条件。正常段间无复位；失败路径沿用先记录、再DMA复位静止、保留PL sticky、不自动重试。
- UserConfig.cmake：恢复只编译main.c。实际新副本被IDE列入了continuous两个.c，main.c又include它们，会重复定义，必须删除这两项或用本修改稿替换。
- 不修改链接脚本；新BSS增大后必须由真实map/ELF检查不与RX重叠。

## 检查合同与复用

check_endurance.py复用timerfixed-entry-01/check_entry.py的符号/ELF读取、计时指令验证、固定内存合同、加载路径验证及current_build安全助手。冻结检查器不改；POLICY绑定依赖文件与固定候选源码/配置，支持CRLF/LF差异但不放宽C语义。

- 保留continuous_contract原16字段，后两个为10秒短段默认值，不将其误报成长段配置。
- 新增endurance_contract十个32位字段：magic=0x454e4431、version=1、长时限、长组数、短时限、短组数、短段数10、总段数11、段间等待、2秒超时。
- 额外核对本次对象和ELF中**实际被main引用的endurance_schedule**：11组(run_us,min_groups)，共88字节；不能仅改标签或另放无关JSON。
- pre校验源码、CMake、平台/BSP及固定XSA；post校验编译单元/实际命令、对象/ELF两份合同与调度表、计时指令/除数、程序边界和map；load才要求新应用专用launch配置及匹配bit/init，且需本应用成功post及相同源码/产物。
- post状态明确为E1_ARTIFACT_PASS_NOT_LOAD_NOT_BOARD；不是加载通过，也不是B批准。未提供自动上板入口，不得借用旧加载脚本绕过新合同。后续加载操作单在B放行和真实产物核对后交给用户。
- 与旧入口不同，新source哈希只绑定固定源码/配置，不绑定clangd缓存；额外代码/影子头文件拒绝。未知编译/合同布局拒绝，不能无条件更新POLICY放行。

## 本次实际自检

1. run_model.py使用现有主机GCC编译候选portable C循环，执行原16项模型用例（含背压、溢出、编号、guard、DMA和停止超时、所有权等），全部通过。
2. 同一模拟外设实例、不复位的11段调度通过；长段14400250组/57601包，模拟capture_command_us=300038520；十个短段各480250组/1921包。跨段模型仅重置槽交替断言的观察起点，不重置外设或编号；停段中编号人为前进用来测试允许段间间隔。这不是实板时长/吞吐数据。
3. 新增时限/组数不匹配、失败不可重用、空配置、全段期限4项断言通过。
4. run_gate_tests.py：7个Python测试方法通过，包含10个合同字段及22个调度字段逐项变异；真实旧修复版ELF因缺新合同而被拒绝；旧表达式、重复编译源、额外头文件拒绝。合成合同字节正例不是本次真实ARM对象检查。
5. 对尚未修改的F盘four_mic_endurance执行pre，预期拒绝旧main_continuous.c，原始failure.json保留。这是预期负例，不是新程序运行失败。

日志都在evidence的新时间目录。实际ARM编译、main的BSP端执行、真实缓存/DMA行为、新配置加载验证、5分钟及十次实板均**未执行**。本轮未重跑RTL仿真/综合实现；PL未改。也未重新运行旧入口18/4/10/34项检查套件，不将上一批通过次数算本批。

## 运行与下一阶段

操作单：OPERATOR.md。主机测试可用已有Python运行 `run_model.py`、`run_gate_tests.py`；前者接受--gcc，默认F:/Program/env/mingw64/bin/gcc.exe。每次创建新证据目录，不覆盖失败。

pre示例（仅检查，不编译下载；输出放本目录evidence的新子目录）：

```powershell
& 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B 'E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/endurance-test-01/check_endurance.py' --stage pre --app F:/College/verilog_digital_system/Vitis/four_mic_endurance --platform F:/College/verilog_digital_system/Vitis/continuous_platform --tools-bin F:/AMD/2025.2/Vitis/gnu/aarch32/nt/gcc-arm-none-eabi/bin --record-root 'E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/endurance-test-01/evidence'
```

实际Build/Run之前尚需：B入口放行记录、用户安装候选通过pre、用户构建后真实对象/ELF/map/新launch检查。首次硬件测试只加载一次，段间由程序自己停止/排空/重启，不能点击11次Run；长段期间不打印串口，需事先开启完整串口保存，不能因暂时无输出而重置。失败就留存日志，禁止清错误后当同一段续跑。

所有新数据、配置、产物哈希和失败追加本目录，不改冻结原件，不提交/推送/合入。不称M1、长稳或独立验收。
