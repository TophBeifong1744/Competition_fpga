# 同实录单麦／手动指向对照

## 步骤1：工程准备（2026-09-15完成）

- 已安全 fetch origin main；本地 main 与 origin/main 同为 `09ecf267813e1ac289dae9358d9e097a87906c86`。
- 新分支：`task/member-b-real-audio-compare-01`，从该基线创建。唯一开发工作树：`F:/NUEC/review-worktrees/member-b-real-audio-compare-01`。
- 成果集中于本目录，后续源文件、配置、验证结果、音频及说明沿此任务继续。尚未实现或导出音频，不构成算法或声学验收。
- 原 `F:/NUEC/develop` 的198条未提交变更保持原样；不复制其未审代码，不恢复已清理工作树。

## 已定位的复用入口（均相对仓库根）

| 入口 | 已核查用途 | 后续使用方式 |
|---|---|---|
| `task-packages/PKG-B-ALG/payload/model/python/h1_reader.py` | 严格读取H1、保留样本编号和错误区间 | 直接引用，不重写读取器 |
| `task-packages/PKG-B-ALG/payload/model/python/audio_frames.py` | `adapt_h1`统一除以2^23、保留通道比例；`iter_frames`不跨错误拼帧 | 复用标度及连续区间；音频边界规则另在实现时明确 |
| `model/python/six_mic_acoustic_review.py` | `das`及`audio_demo`，绑定六麦POS和合成数据 | 参考延迟符号与统一输出增益思路；不能直接当四麦实录入口 |
| `task-packages/PKG-B-ALG/tasks/c-board-algorithm-01` | 已限定批准的四路几何/符号诊断、输入哈希和H3缺项 | 引用既有证据，不覆盖原文件 |
| `task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/c-adapter-first-20260913` | 已接收录音及GEOMETRY.md | 步骤2固定实际录音与配置；本步未冻结新的手动方向 |

## 准备验证

在新工作树根目录，使用本机 CPython 运行原有适配/分帧测试，退出码0，24项通过：

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) 'task-packages/PKG-B-ALG/payload/model/python'
& 'C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B -m unittest discover -s task-packages/PKG-B-ALG/payload/tb/python -p test_audio_frames.py -v
```

结果为工具实际控制台输出：Ran 24 tests in 3.227s / OK。本步仅记录结果，未另存原始日志；不是新增DAS测试或完整历史研究复跑。

下一步：固定同录音输入、几何、单麦参考和手动试验配置，再实现四麦延迟合成。约−45°/10cm以mic1为参考，不标作阵列中心准确远场真值。后续完整交付后推送任务分支交A复核，本步骤不合入main。

## 步骤2：输入与配置固定（2026-09-15完成）

配置：`config.json`；可复跑入口：`check_inputs.py`；实际结果：`evidence/input-check-01.json`。原5文件历史哈希清单直接引用已批准c-board-algorithm-01/inputs.json，并固定该清单SHA-256，不重建或改写历史哈希。校验前后5个输入文件均严格一致。

| 项目 | 本次选择 |
|---|---|
| 主比较输入 | c-adapter-speech-20260913-01，32000行，样本编号16542～48541 |
| 背景诊断输入 | c-adapter-quiet-20260913-01，32000行，样本编号17238～49237；不是已知目标方向样本 |
| 采样率与长度 | 声明48kHz，每段约0.666667秒，保持两段独立；不循环拼接充当新录音 |
| 输入区间 | 每段[0,32000)均格式无错且连续；输出两路的共同裁剪区间在步骤3按延迟实现确定 |
| 几何 | mic0原点，+X指向mic1，+Y指向mic3；40mm平面正方形，沿用操作者声明边界 |
| 单麦参考 | 固定mic0；不是通过试听挑出的最好通道 |
| 标度 | 四路统一PCM/8388608；不做逐通道归一化或校准 |
| 手动试验 | 平面波指向：方位−45°、仰角0°，声速假设343m/s；仅试验配置，ground_truth=false |

这里−45°只作为试听前预先指定的+X/−Y试验指向，**不是**由相对mic1约10cm/−45°转换得到的阵列中心真实方位。模型不使用该距离，也不生成虚假的精确声源坐标。当前未校准、近场声源可能导致平面波模型失配，输出好坏均需如实记录，不据此判定位精度。未扫描角度或选择最好听的结果。

实际校验退出码0，状态INPUT_BINDING_VERIFIED_ONLY：复用原ReaderSession和adapt_h1；两段无错误行，几何/采样率/通道顺序与配置一致，统一标度数组严格一致。人声四路峰值约0.00323～0.00359满量程，安静约0.00262～0.00313，原始数字幅值低。后续保留统一标度输出；若需要可听预览，对配对输出使用同一明确记录的增益，不能分别归一化后报告改善。

```powershell
& 'C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B task-packages/PKG-B-ALG/tasks/real-audio-compare-01/check_inputs.py --out task-packages/PKG-B-ALG/tasks/real-audio-compare-01/evidence/input-check-02.json
```

输出必须使用不存在的文件名；若历史哈希或元数据与配置不符则停止。结果记录配置、输入、源码哈希及Python/NumPy环境。该检查是后续算法输入绑定，不是重签格式验收。尚未生成WAV、实现分数延迟或完成DAS测试；这些是步骤3～4。短录音支持管线诊断，但不足以充分评价语音清晰度，不从重复播放制造独立样本。

## 步骤3：离线手动DAS与WAV导出完成

源码 `render_audio.py`；配置 `render-config.json` 绑定步骤2配置原哈希，步骤2记录不覆盖。`config.json`中的audio_output_created=false是步骤2状态；本次实际生成状态以`evidence/audio-run01/result.json`为准。

采用线性分数延迟：`y_i[n] = x_i[n-d_i]`，其中 `d_i=(p_i-p_mic0)·u*Fs/c`；四路补偿约 `[0,+3.958149,0,-3.958149]` 样点，之后等权平均。与mic0相同参考时间，取所有通道插值索引均在原区间内的交集。单麦也裁同一区间，不做循环移位、补零、不跨错误或拼接录音。

两段本次各裁到 `[4,31996)`，输出31992样点/0.6665秒。人声参考样本编号16546～48537，安静17242～49233。该编号标记mic0参考时间，手动各通道使用分数样点源索引；不是说手动输出只读取该编号范围内的输入。

每段4个单声道、48kHz、24位PCM WAV：`single-raw`、`manual-raw`是统一输入标度；`single-preview`、`manual-preview`在两路、两段全部统一乘64，方便试听。量化使用最近偶数舍入并显式饱和计数。每个文件写出后独立解码回读，严格核对整数码及WAV头；8个文件均无饱和。单麦raw与原整数PCM裁剪严格一致；手动量化误差最大约5.95e-8满量程，小于半个24位LSB。

实际运行命令（首次out为audio-run01；复跑使用新目录，不覆盖）：

```powershell
$py='C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$pkg='task-packages/PKG-B-ALG/tasks/real-audio-compare-01'
& $py -B -m unittest discover -s $pkg -p test_render_audio.py -v
& $py -B "$pkg/render_audio.py" --out "$pkg/evidence/audio-run02"
```

作者实跑8项测试通过，日志`evidence/render-tests-01.log`；包含整数冲激补偿符号、分数延迟斜坡恒等式、几何平移不变性、常量保持、无环绕、短区间/非法输入拒绝及PCM端点/舍入。它们是代数/数组测试，不是新增四麦声学模拟。实录导出日志`audio-run01-console.log`，原输入运行前后哈希一致。result.json保存每个WAV的哈希、样本数、峰值、RMS、饱和计数、量化误差和源码/依赖绑定。

本步限制：线性插值存在随分数延迟变化的频率幅度衰减，尚无校准收益；当前没有加滤波或逐输出归一化。输入全为单连续段，本实现一次性离线处理，无分帧接缝，但不验证实时流边界、动态指向渐变或跟踪HOLD。未实现定点DAS、自动分支或板端播放。8项测试及码值检查属于步骤4的基础数值验证，不代替用户实际试听或完整H3回归。

### 用户试听记录（2026-09-15已收到人声对照反馈）

先听`audio-run01`中人声的single-preview和manual-preview，固定播放设备与音量；两者均已放大64倍，无需分别调音量。然后可比较quiet对应文件。短片段导致“不确定”是合理反馈，不循环拼成长录音来声称样本增多。

- 用户原话：“差不多清楚，无发闷失真断音爆音”。
- 语音清晰度：两路差不多；用户未报告发闷、失真、断音或爆音。
- 播放设备、是否保持固定播放音量、背景声变化：未提供，不推断。quiet试听尚未确认。
- 绑定所呈现WAV哈希的记录：`evidence/listening-01.json`。

本次短人声对照已收到主观反馈，未发现用户可感知的上述明显异常；没有建立手动指向改善或降噪收益结论。步骤6处理决定：保留现有源码/配置/音频，不根据“差不多”扫描方向或调增益追求更好听。render的result.json中listening_completed=false保留为导出时快照，后续反馈以listening-01.json为准。

下一步是步骤7整理完整交付及复核说明；完整H3、自动分支和实时连续性仍未通过。尚未提交推送或合入main。

## 步骤7：完整交付

上述“尚未推送”为各步骤时点记录。本次材料已整理待提交到`task/member-b-real-audio-compare-01`，准确远端SHA以工作执行推送回报为准，不自审自合main。

`verify_delivery.py`检查包内MANIFEST.json、原输入、复用源文件、8份WAV及试听文件绑定；清单不包含自身。`REVIEW-PROMPT.md`给出A完整复核命令和限定范围。全部新增内容只在本目录，原证据不覆盖；本轮无需AMD DLL，仅Python与NumPy。未增加新算法或更改已试听输出。
