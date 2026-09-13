# 离线检查及实际运行入口

本轮已完成实录，不要求再上板。以下命令给复核/重现使用，不自动下载。仓库根PowerShell：

```powershell
$CapturePython = 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$CaptureBatch = Join-Path (Get-Location) 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/c-adapter-first-20260913'
& $CapturePython -B "$CaptureBatch/verify_delivery.py" "$CaptureBatch/delivery-01"
if ($LASTEXITCODE -ne 0) { throw '离线校验未通过，保留输出' }
& $CapturePython -B 'task-packages/PKG-B-ALG/payload/model/python/h1_reader.py' "$CaptureBatch/delivery-01/c-adapter-quiet-20260913-01" "$CaptureBatch/delivery-01/c-adapter-speech-20260913-01"
if ($LASTEXITCODE -ne 0) { throw '读取器未通过，保留输出' }
```

期望：ARCHIVE_CHECK_PASS_NOT_ACCEPTANCE及PASS_FORMAT_ONLY。读取器由工程实现执行，不能写成B本人已复核。

若需要完整重新导出，下面必须使用不存在的新目录。此次实际执行输出为delivery-01；复跑示例delivery-02，不得先创建它：

```powershell
& $CapturePython -B "$CaptureBatch/prepare_delivery.py" --output "$CaptureBatch/delivery-02" --vitis-workspace 'F:/College/verilog_digital_system/Vitis'
if ($LASTEXITCODE -ne 0) { throw '导出失败，不覆盖失败目录' }
```

依赖Python和numpy（现有B读取器需要）、任务source原导出器和17项测试、received-01、operator-record.json，以及已核对的F盘四麦产物。不会调用Vivado、编译或板卡；版本文件哈希改变时拒绝，不猜替代文件。每个实际子命令/返回码见delivery-01/commands.json，原始输出见logs。原导出器输出metadata另存logs，再仅在新副本补几何和独立H1配置版本。

本轮使用的板上Run配置快照见delivery-01/versions/launch.json。用户两次Run后分别通过XSDB导出，路径如下；每次READY后导出完成再下一次Run，禁止旧单麦bit和C板同时使用。

```tcl
targets -set -filter {name =~ "*Cortex-A9*#0"}
mrd -bin -file F:/College/verilog_digital_system/Vitis/c_adapter_quiet_20260913_01.bin -size w 0x01000000 256000
# 第二次独立Run完成后，另存新文件；不是紧接第一条读取同一缓存。
mrd -bin -file F:/College/verilog_digital_system/Vitis/c_adapter_speech_20260913_01.bin -size w 0x01000000 256000
```

原串口为同名.log。文件已存在不得重录覆盖。本页说明原操作入口，不是精确时间戳的JTAG执行日志。当前无需再跑这些上板命令。
