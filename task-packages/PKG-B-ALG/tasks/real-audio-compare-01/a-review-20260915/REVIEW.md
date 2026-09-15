# A 独立复核：同实录单麦／手动指向音频对照

2026-09-15。**通过限定复核，无技术阻断项。** 仅批准本包离线四路实录单麦/手动DAS源码、配置及证据入库；不是音频改善、完整H3、自动指向、定点DAS、实时连续性、定位精度或实板验收通过。

## 1. 固定版本与边界

- 远端分支 `task/member-b-real-audio-compare-01`，直接远端核对SHA：`1aa1f219ccdc9bd398d4493dfb44613d11174626`。
- B基线 `09ecf267813e1ac289dae9358d9e097a87906c86`；基线至待审提交仅新增 `task-packages/PKG-B-ALG/tasks/real-audio-compare-01/` 下25个文件。没有改默认算法、跟踪器、冻结输入、旧复核、其他成员文件或阶段状态。
- 独立审核工作树 `E:/ss-real-audio-review-0915`；新输出 `E:/ss-real-audio-review-0915-output`。没有修改B原件或用户Vivado/Vitis工程。
- 以本目录README为离线入口，不迁入默认算法。本次不是9/18完整包或阶段总验收；缺项仍按原计划执行，不向C派新任务。

## 2. 实际命令与环境

Windows 11 build26200；CPython3.12.14；NumPy2.3.5。本轮不需要AMD DLL。以下在固定SHA独立工作树根目录实际运行，全部退出0：

```powershell
$py='C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$pkg='task-packages/PKG-B-ALG/tasks/real-audio-compare-01'
$out='E:/ss-real-audio-review-0915-output'
& $py -B "$pkg/verify_delivery.py"
& $py -B -m unittest discover -s $pkg -p test_render_audio.py -v
& $py -B "$pkg/check_inputs.py" --out "$out/input-check.json"
& $py -B "$pkg/render_audio.py" --out "$out/audio"
$env:PYTHONPATH=Join-Path (Get-Location) 'task-packages/PKG-B-ALG/payload/model/python'
& $py -B -m unittest discover -s task-packages/PKG-B-ALG/payload/tb/python -p test_audio_frames.py -v
& $py -B "$pkg/a-review-20260915/audit_real_audio.py" . $out "$out/comparison.json"
```

末条独立审计脚本最初从A可写临时目录运行；入库源码与运行源码相同。重新复现须使用尚不存在的输出目录/报告路径。

- 8项音频测试、24项原适配/分帧回归均实际通过，不沿用作者旧结果冒充本轮运行。
- `verify_delivery.py`通过：24项包内manifest条目、冻结5项输入、复用源码、8个WAV及试听文件哈希绑定。
- 再次向既有audio目录和input-check文件运行对应命令，分别得到预期 `FileExistsError` 和 `ValueError`、退出1；既有WAV逐文件哈希未变。负向检查日志保留，不能当成功生成日志。
- B历史 `delivery-check-failure01.txt` 是其GBK/UTF-8修复说明，不是A本轮失败；当前源码显式UTF-8，中文反馈可读取。原说明未覆盖。

## 3. 逐项核验

| 项目 | 结论及证据 |
|---|---|
| 几何与方向 | 四麦40mm正方形采用当前冻结坐标。−45°、0°是预选试验方向；约10cm/−45°以mic1为参考，不被转换或冒充阵列中心准确真值 |
| 符号 | 向声源单位向量u，到达差为−(p_i−p_ref)·u/c，故补偿 `output_i[n]=input_i[n-delay_i]`、delay=(p_i−p_ref)·u Fs/c 正确；冲激符号测试通过 |
| 裁剪/编号 | 独立枚举四路源索引交集得到[4,31996)，两段各31992样本/0.6665秒。speech编号16546～48537、quiet17242～49233；编号为mic0参考时间，不冒称其他通道只使用这些编号 |
| 间断保护 | 逐clean_interval处理，无跨错误拼接、环绕或补零。原适配24项包括编号间断/错误/独立段测试；本批真实输入只有单连续段，不能据此批准实时边界或长稳 |
| 标度与增益 | CSV独立解析；PCM统一除8388608，mic0固定单麦参考，四路等权平均。两段两路preview均统一64倍，raw为1倍；未逐通道/逐输出归一化 |
| 独立数值重算 | 不调用B渲染器生成预期值；独立CSV读取、`numpy.interp`补偿、WAV signed24解码重算。8份WAV均与历史逐码一致，单麦raw与原CSV mic0裁剪严格一致 |
| 量化/饱和 | 24位最近偶数舍入及端点测试通过；8份均无饱和。manual-raw独立最大误差5.945248413019577e-8，manual-preview 5.923870838309142e-8，均小于半LSB=5.960464477539063e-8 |
| 新旧证据 | 8份WAV字节完全相同；result.json及input-check.json本次字节也相同。逐字段离散值/浮点值比较均一致，比较入口预设浮点1e-12容差，未放宽或关闭断言 |
| 主观记录 | 两个人声preview哈希与listening-01.json一致。反馈是B提交的“差不多清楚，无发闷失真断音爆音”；A未另作试听，不冒称独立听感复核。设备、固定音量、背景变化未知；quiet未确认试听 |

## 4. 问题与限制

无阻断问题、无必须修改项。以下非阻断边界不得被后续报告省略：

1. `render_audio.py::render_interval`为线性分数延迟，存在频率相关衰减。试验方向未按中心精确声源真值校准，录音只有约0.667秒。未证明目标增强、降噪/SNR改善或定位精度。
2. `README.md`按步骤保留“尚未生成/尚未推送”的历史文字，config/result中false也是生成时状态。当前发布/复核状态以本记录及准确提交为准；不改冻结JSON来回填通过。
3. `verify_delivery.py`证明绑定与完整性，不单独证明WAV解码或算法正确；本轮已补独立解码/CSV数值检查。试听文件绑定不证明播放设备、音量控制或A实际听过。
4. 自动分支、定点DAS、动态指向过渡、实时连续性、RTL与实板播放未测试；本轮没有批准这些能力。后续在同源录音下完善自动对照及适用真值/干净参考，不以反复调角追求好听替代验证。

## 5. 证据去向与批次收尾

本目录保存A命令日志、独立审计源码与comparison.json。重新生成的8份WAV、result.json、input-check.json与作者原证据字节相同，由comparison.json哈希指向原文件，避免重复存储；不删除作者原WAV、历史失败说明或试听记录。

发布前实际共享目录：`E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga` 的main为 `57c50e6c99731cd57e7738ac91b02f985ad229b1`，实际远端为 `be26c276b266f1c2cfd6d6ca458d2bffbb91e02a`。共享10项已修改路径及215项未跟踪文件与远端新增/修改路径重叠，涉及AGENTS及两项Skill。它们非本次B音频包内容，不在本轮静默覆盖、暂存或清除。连续采集目录、中心录音及其余未提交工作也保留。

本包在隔离工作树按准确范围合入并执行验证。**本地共享main同步收尾待处理**：应由A工作执行/主流程协调原文件负责人，保留用户9/15新约定并完成既有Skill发布去重后安全同步；不能将本次远端推送称整个共享目录已同步。B短期分支暂保留至本地材料处置确认，B的F盘工作树本机不可访问，不代签清理完成。
