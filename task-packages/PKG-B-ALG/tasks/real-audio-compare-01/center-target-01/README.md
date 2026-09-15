# 中心 +X 实录对照：步骤1～2

2026-09-15完成本地工程准备和输入绑定，未生成音频、未提交推送。本修订沿用已批准real-audio-compare-01代码，独立保存新增配置和结果，不覆盖旧录音、试听或A复核证据。

## 工程与准确版本

- 唯一开发目录：`F:/NUEC/develop`；本次直接在干净目录建立`task/member-b-center-audio-01`，没有新增worktree或仓库外任务文件夹。
- fetch后的main及origin/main基线：`058aa3095fd4df7392645004b164adb4eec52041`。
- 中心录音批准输入：`f9768b80e5718dcf29baf48015305780f4b9b8e8`；见`docs/reviews/center-target-f9768b8/B-REVIEW.md`，仅诊断接收，不是声学真值/收益验收。
- 复用音频作者版本：`1aa1f219ccdc9bd398d4493dfb44613d11174626`，后获A限定通过。读取器、适配器、延迟函数源码保持原字节。

## 固定输入和手动配置

`config.json`与`pins.json`绑定新批次`center-target-20260914/delivery-01/c-center-target-20260914-01`的CSV、metadata、原delivery哈希清单、操作者说明、批准记录和4份复用源码。共10个文件，生成pins时与当前Git对象逐字节核对；CSV/metadata同时与A原交付SHA清单对应项核对。不复制数据、不重做格式验收。

实际结果`evidence/input-check-01.json`：32000组，声明48kHz，约0.666667秒，原编号17413～49412；[0,32000)连续且无错误行。原ReaderSession/adapt_h1成功，四通道float64(PCM)/8388608严格一致，配置与原几何匹配。运行前后全部10项哈希一致。

固定mic0为单麦参考，几何仍为mic0原点、+X向mic1、+Y向mic3的40mm平面正方形。手动平面波试验0°方位/0°仰角，声速假设343m/s；原延迟函数计算补偿`[0,5.597667638484,5.597667638484,0]`样点，并用独立+X代数式核对。只是配置核验，尚未执行DAS或WAV导出。

中心(.02,.02,0)m、约1.5m/+X/同高是操作者报告；mic0元数据原点不变，1.5m不进入当前平面波延迟模型。位置误差、活动语音区间、独立干净/噪声参考及通道校准未知。旧speech文件已补充说明为手机歌曲，不移用旧批主观反馈到本次现场人声，也不拿新旧录音的音量差当算法收益。

原始四路峰值约0.00691～0.00784满量程。下一步根据新输出的峰值选择共同试听增益，两路使用同一数值，保留原标度输出；不盲目继承旧64倍，不分别归一化。

## 实际运行命令

在`F:/NUEC/develop`执行（本次out为input-check-01.json；下例复跑用新文件名）：

```powershell
$pkg='task-packages/PKG-B-ALG/tasks/real-audio-compare-01/center-target-01'
& 'C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B "$pkg/bind_inputs.py" --out "$pkg/evidence/input-check-02.json"
```

本次退出0，状态STEP1_2_INPUT_BOUND_ONLY，Python3.12.14/NumPy2.3.5/Windows11。机器可将python路径替换为自己的解释器，无AMD DLL依赖。程序拒绝已有报告，输出限定本修订内；结果含配置、绑定脚本和依赖哈希。未声称重复执行原17项输入验收或8项音频测试。

下一步3～4：在本修订加新入口，直接调用原render_interval和write_wav，导出同录音单麦/手动配对，再检查共同裁剪、PCM与饱和；旧主入口绑定旧配置，不直接更改或运行它冒充新批次。完整交付后再交A复核，不自审自合main。

## 步骤3～4：新输入音频导出及基础数值检查完成

`render_center.py`新增录音入口，直接调用未改动的`render_interval`、`write_wav`、`delays_for`及H1读取/适配代码。`render-config.json`绑定步骤2配置哈希。旧配置中的audio_generated=false/preview_gain=null保留为步骤2快照，本次实际输出以`evidence/audio-run01/result.json`为准。

- 共同裁剪`[6,32000)`，两路各31994样本、0.666541667秒；mic0参考编号17419～49412。保留原录音，不补零、不循环拼接、不跨错误行；此批只有一个完整连续输入区间。
- 延迟沿用`[0,5.597667638484,5.597667638484,0]`，四路线性分数延迟后等权平均；单麦mic0裁相同参考时间。补偿定义`y_i[n]=x_i[n-d_i]`，并不是给两路增加不同播放延迟。
- 输出4份PCM24、48kHz WAV：`interval00-single-raw.wav`、`interval00-manual-raw.wav`保留原标度；对应`*-preview.wav`为统一增益试听版。
- 试听增益按新录音全部干净四通道与两路输出的最大幅值共同选择，取不超过128的2次幂，使峰值≤0.5。零输入用1倍。本次峰值依据0.007843017578125，选择32倍；未分别归一化，也未盲用旧64倍。此增益仅用于播放，不是算法收益。
- 每份写出后回读PCM，头字段、整数码严格匹配预期；4份饱和计数均0，单麦raw与原CSV mic0裁剪逐码一致。所有10项绑定输入/依赖前后哈希一致。

### 实际验证

8项原音频测试实际复跑通过；新增4项测试验证预览增益边界、非有限/负值拒绝、已有输出不可覆盖和修订外输出拒绝，全部通过。已有输出拒绝测试前后对目录5个文件哈希核对无变化，不产生覆盖或删除。

`audit_audio.py`使用独立CSV解析、`numpy.interp`和24位有符号字节解码重算预期，不调用渲染器生成golden；这是作者交叉数值自测，不是A独立复核。四份WAV与该方法预期均0码差；两份manual最大量化误差分别5.9430871148e-8、5.9430891097e-8满量程，低于半个24位LSB（约5.9604644775e-8）。审计程序预设不同浮点评估最多1码且绝对误差≤半LSB+1e-12，未因本批结果放宽容差；实际全部0码差。

证据：`evidence/render-tests-01.log`、`entry-tests-01.log`、`render-01.log`、`audit-01.log`、`audit-01.json`，以及`audio-run01/result.json`中的源码/输入/WAV哈希、配置、运行环境、量化和幅值统计。无算法运行失败；预期的拒绝由测试捕获并确认输出未变。

仓库根复跑命令（原audio-run01与audit-01保留，下面使用新输出）：

```powershell
$py='C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$pkg='task-packages/PKG-B-ALG/tasks/real-audio-compare-01'
$rev="$pkg/center-target-01"
& $py -B -m unittest discover -s $pkg -p test_render_audio.py -v
& $py -B "$rev/render_center.py" --out "$rev/evidence/audio-run02"
& $py -B "$rev/audit_audio.py" --audio "$rev/evidence/audio-run02" --out "$rev/evidence/audit-02.json"
& $py -B -m unittest discover -s $rev -p test_center.py -v
```

### 新录音试听反馈与处理

用户已对本次呈现的两份preview反馈：“都差不多，无发闷、失真、断音或爆音，可以下一步”。记录在`evidence/listening-01.json`，绑定两份新WAV哈希；“都差不多”按所提清晰度/背景问题记录，保留原话，不新增改善结论。播放设备及固定音量是否遵守未提供，保持未知。

处理决定：保持当前配置、源码和WAV，不根据此次主观反馈调角/改增益。旧输入配置与生成报告的未生成/未试听字段是当时快照，本次反馈另存，不回填覆盖。本轮只完成单麦/手动同录音对照和作者自测，待A限定复核。

限制不变：短片段、操作者近似位置、无独立干净/噪声参考，不能报告SNR提升或精确方位误差。线性插值本身有频率相关衰减；本次5.598样点的小数部分与旧批不同，不能把新旧音色差都算声学效果。当前为一次离线连续段，不代表流式分帧边界、动态指向/自动跟踪、定点DAS、板端播放或完整H3通过。

### 集中交付

本轮源码、配置、原结果、实际日志、4份WAV、试听记录及复核提示词均在本目录。`MANIFEST.json`固定本次包内文件哈希（不含自身），`verify_package.py`检查包、原输入/复用代码、音频和试听绑定。只作交付完整性检查，不代替实际音频数值复算或独立审核。

复核完整命令、请求范围和清理边界见`REVIEW-PROMPT.md`；准确提交/远端SHA由工作执行推送回报。本轮不改主流程状态、不推main。当前分支`task/member-b-center-audio-01`直接位于用户日常项目`F:/NUEC/develop`，不是可删除的临时worktree。
