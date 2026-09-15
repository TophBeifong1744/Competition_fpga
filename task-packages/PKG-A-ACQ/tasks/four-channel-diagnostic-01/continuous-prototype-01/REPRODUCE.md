# 复跑入口与版本绑定

所有命令输出目录必须是**尚不存在**的完整路径，父目录需存在。不要以-force删除旧运行，换一个新后缀即可。这里只生成隔离副本，不更新实际one/短抓取PS，不调用旧适配脚本，不连接实板。

## 一条完整构建命令

以下沿用本机已核对依赖，参数可按另一台机器真实位置替换；不应把示例目录直接创建成空文件夹，因为入口会拒绝已有目录。

```powershell
$continuousPython = 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$continuousTask = 'E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01'
$continuousInputs = @(
  '--project', 'F:/College/verilog_digital_system/AMD/Competiton/one/one.xpr',
  '--vivado', 'F:/AMD/2025.2/Vivado/bin/vivado.bat',
  '--gcc', 'F:/AMD/2025.2/Vitis/gnu/aarch32/nt/gcc-arm-none-eabi/bin/arm-none-eabi-gcc.exe',
  '--bsp', 'F:/College/verilog_digital_system/Vitis/c_adapter_platform/export/c_adapter_platform/sw/standalone_ps7_cortexa9_0',
  '--bsp-xsa', 'F:/College/verilog_digital_system/Vitis/c_adapter_platform/export/c_adapter_platform/hw/system_c_adapter.xsa',
  '--ps-source', 'F:/College/verilog_digital_system/Vitis/four_mic_capture/src',
  '--output', 'E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/continuous-rebuild-NEW',
  '--jobs', '4'
)
& $continuousPython -B "$continuousTask/run.py" check @continuousInputs
if ($LASTEXITCODE -ne 0) { throw '预检失败；不要继续' }
& $continuousPython -B "$continuousTask/run.py" build @continuousInputs
if ($LASTEXITCODE -ne 0) { throw '构建失败；保留整个输出目录' }
```

`--ps-source`用于保护/复制原短抓取基线及其linker；真正编译的是本候选ps目录的固定源码，绝不会覆盖原main_four_capture.c。`ps-check`只编译并校验PS，不产生新硬件结果。构建会保存输入、源码、预处理.i、.o、ELF/map、Vivado报告、工具环境、命令及哈希。

本轮最终完整构建实际输出是`E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/continuous-work12`。其完整原件压缩快照为delivery-01/history/continuous-work12.zip。压缩包保留历史绝对路径用于追溯；跨机器复现请运行入口重新快照，不直接启动旧生成脚本中的个人路径。

## 功能仿真、实际PS循环模型、安全检查

```powershell
& $continuousPython -B "$continuousTask/run.py" sim `
  --vivado-bin 'F:/AMD/2025.2/Vivado/bin' `
  --cic 'F:/College/verilog_digital_system/AMD/Competiton/one/one.srcs/sources_1/imports/rtl/pdm_cic3.v' `
  --output 'E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/continuous-sim-NEW'
if ($LASTEXITCODE -ne 0) { throw '仿真失败' }
& $continuousPython -B "$continuousTask/run.py" host `
  --host-gcc 'F:/Program/env/mingw64/bin/gcc.exe' `
  --output 'E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/continuous-host-NEW'
if ($LASTEXITCODE -ne 0) { throw 'PS模型检查失败' }
& $continuousPython -B "$continuousTask/verify_offline.py" `
  --output 'E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/continuous-safety-NEW'
if ($LASTEXITCODE -ne 0) { throw '安全检查失败' }
```

最终执行位置：ss-cont-sim-final-01、ss-cont-host-02、ss-cont-safety-final-02，详见delivery-01/evidence各logs中的完整argv/cwd。两次直接手动unit test检查后来由verify_offline重跑保存日志，不把重复次数累加成更多不同用例。

`collect.py --build <完整构建目录> --sim <仿真目录> --host <主机模型目录> --safety <安全目录> --short-app <原four_mic_capture目录> --output <新交付目录>`核对源码和状态后整理，可多次附加`--history <失败或历史目录>`；所有输出仍拒绝覆盖。

工具包支持文件从AMD已有安装目录读取，仅在本次Python进程及其子Vivado设置TCLLIBPATH，不改全局环境。直接synth/place/route规避受限Windows Script Host，不写假run完成标志。XSA不嵌入bit；加载时使用同一release中的显式bit路径。

已知PS源码体由SHA-256白名单绑定，实际编译合同还必须通过；任意改BASE/LIMIT、逻辑或长度都会拒绝放行，不能只改版本字符串通过。候选局部.gitattributes保留字节，防止Windows换行转换破坏证据。改变代码须作为新候选复测，不静默更新白名单冒充原结果。
