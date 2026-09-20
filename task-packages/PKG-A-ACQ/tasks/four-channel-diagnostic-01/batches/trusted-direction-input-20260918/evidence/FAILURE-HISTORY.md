# 准备阶段失败记录（不涉及实板）

以下为本任务工具实际返回的首错，原工具输出留在工程实现任务；这里保留命令与结果。没有失败采集，也没有覆盖历史材料。

1. 当前 Python `import numpy, scipy`：`ModuleNotFoundError: No module named 'scipy'`。不用安装依赖，离线标记检测改用已有 NumPy FFT。
2. `scripts/make_speech.ps1 -OutputDirectory evidence/speech-generation-01`，当前受限 PowerShell：`SelectVoice: No voice installed on the system or none available with the current security setting.`，退出1。
3. `powershell.exe -NoProfile -File scripts/make_speech.ps1 -OutputDirectory evidence/speech-generation-02`：本机脚本策略拒绝执行，退出1；未改变持久策略。
4. 上条命令仅加进程级 `-ExecutionPolicy Bypass`：`SelectVoice: Object reference not set to an instance of an object.`，退出1，仍受限。
5. `prepare.py playback --speech-dir evidence/speech-generation-02 --out playback`：缺少 speech-original.wav，退出1；保留空输出目录，不复用。
6. 增加已安装语音列表检查，`make_speech.ps1 ...speech-generation-03`：仍在 SelectVoice 报与第2项相同错误，退出1。
7. 已确认语音列表包含 Microsoft Huihui Desktop。对仅调用本机语音引擎的命令申请受限环境外执行，使用新目录 `speech-generation-04`，退出0；不联网、不安装、不改变系统配置、不操作板卡。
8. `prepare.py playback --speech-dir evidence/speech-generation-04 --out playback-v1`，退出0；输出文件已回读验证。

结论：限制发生在本机语音引擎初始化，不是采集固件或硬件故障。后续直接使用冻结 WAV，不要求重复生成语音。
