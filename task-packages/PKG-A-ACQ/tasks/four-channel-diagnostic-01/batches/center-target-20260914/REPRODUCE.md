# 本批复现及检查命令

仓库根PowerShell。使用现有Python/numpy和未改的原导出器/B读取器，不调用Vivado或板卡。

```powershell
$CapturePython = 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$CaptureBatch = Join-Path (Get-Location) 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/center-target-20260914'
& $CapturePython -B "$CaptureBatch/finish_capture.py" --verify "$CaptureBatch/delivery-01"
if ($LASTEXITCODE -ne 0) { throw '交付校验失败，保留输出' }
& $CapturePython -B 'task-packages/PKG-B-ALG/payload/model/python/h1_reader.py' "$CaptureBatch/delivery-01/c-center-target-20260914-01"
if ($LASTEXITCODE -ne 0) { throw '读取器失败，保留输出' }
```

期望ARCHIVE_CHECK_PASS_NOT_B_ACCEPTANCE、PASS_FORMAT_ONLY。verify核对归档清单、BIN/串口、CSV、各路统计和WAV，并与旧两个C板H1段进行同会话配置检查。旧数据只读，不宣称重验旧验收。

本轮实际导出命令如下；delivery-01已存在，勿重跑覆盖。重新导出使用新的delivery-02，文件版本改变先按inspect_current的入口记录新预检，不猜替代物。

```powershell
& $CapturePython -B "$CaptureBatch/finish_capture.py" --raw 'F:/College/verilog_digital_system/Vitis/c_center_target_20260914_01.bin' --serial 'F:/College/verilog_digital_system/Vitis/c_center_target_20260914_01.log' --inspection "$CaptureBatch/evidence/preflight-02" --record "$CaptureBatch/actual-record-20260915.json" --output "$CaptureBatch/delivery-01"
```

所有实际子命令/工作目录/退出码在delivery-01/commands.json；依赖哈希在dependencies.json。9/15磁盘复查沿STATUS.md的inspect_current命令，仅输出改为evidence/preflight-02。旧preflight-01和规划capture-notes.json不覆盖。

用户实物步骤沿RUN.md，当前已经完成最小新段，不要求再次Run。原导出命令为：

```tcl
targets -set -filter {name =~ "*Cortex-A9*#0"}
mrd -bin -file F:/College/verilog_digital_system/Vitis/c_center_target_20260914_01.bin -size w 0x01000000 256000
```

该命令说明操作入口，不冒充新取得的JTAG命令日志。继续录制须新文件名，不用不同Run拼成连续流。
