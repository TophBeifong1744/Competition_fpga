# R1/R2 增量返修与复核入口

基线 `bb964cbd5b4bee005702bebe6b9cee16d9b885d9`；A 报告准确提交 `5e343f2d9e9a372ad59bcc618571d4fb0002a7df`，路径 `docs/reviews/b-checkpoint-bb964cb/REVIEW.md`。本轮仅复现入口、比较器、原字节准备、反例测试及说明，不改变研究算法/配置/冻结数值或 H3 批准范围。A 的18测试、48 WAV、120整数数组结论可复用；新入口运行结果另行归档。

## R1：字段语义及固定容差

比较规则在 `source/compare_outputs.py` 中预先声明，使用 `abs(actual-expected) <= atol + rtol*abs(expected)`，不统一舍入，不修改 JSON 原件。类型先严格比较（bool 不等于 int，int 不等于 float），对象键、列表长度、顺序、字符串、输入/源码哈希、整数、状态及拒绝原因全部严格一致；未列入规则的浮点也严格一致。每个浮点都必须有限，包括期望值；NaN、正负 Inf 均失败。

| 语义字段 | atol | rtol | 单位/依据 |
|---|---:|---:|---|
| numeric_angle、projection方位、numeric偏差P50/P95 | 1e-10 | 0 | 度；远小于角度量化，不允许绕回替代原数值 |
| projection_xy/norm、residual_samples | 1e-12 | 1e-12 | 无量纲或样点；只吸收线性代数浮点尾差 |
| features raw/centered RMS | 1e-8 | 1e-12 | PCM码；远小于1码 |
| band_power、标定功率、golden float_power | 1e-6 | 1e-12 | PCM码平方；随大幅值尺度约束，相对误差上限万亿分之一 |
| descriptive_audio幅值、文件rms/peak/量化误差 | 1e-12 | 1e-12 | 归一化幅值；远小于S24的1 LSB |
| 描述性音量变化 | 1e-10 | 0 | dB；不是收益验收容差 |
| golden relative_power_difference | 1e-12 | 1e-12 | 无量纲；不会抹去已报告约0.389%的量化差异 |

计数导出的 output_fraction/比例、整码 features.peak、混合器 max_weight_step 等仍精确比较。golden summary 单独使用其两种浮点字段规则，NPZ 键、dtype、shape、整数码逐项严格检查；WAV 整文件 SHA-256 相同才能通过。

`json-comparison.json` 分开列每份文件的字节哈希/是否一致、浮点差异路径/绝对误差/允许上限。唯一沿用的内容排除是 study summary.environment，仍将两端环境原样写入报告；派生 OUTPUT-SHA256.json 不要求相同，因为 JSON 字节允许不同，但其余输入哈希字符串绝不豁免。

新增12项测试覆盖 A 报告尾差、近零/越界、golden功率尺度、NaN/Inf、状态/整数/布尔/类型/键/长度/哈希篡改、NPZ dtype/shape/code、PCM字节修改，以及准备流程和具体失配提示。

## R2：Windows 原字节独立准备与运行

请在原仓库根目录使用已安装的 CPython3.12、NumPy2.3.5（`python -c "import sys,numpy; print(sys.version,numpy.__version__)"` 可核对）。如需独立依赖环境，在仓库外创建 venv 并用其 Python 执行 `-m pip install numpy==2.3.5`；不改系统或全局 Git 配置。

将下列 `<本轮远端完整SHA>` 替换为本次发布回执。两个输出路径必须不存在且在原仓库之外；原字节目录是本包及33项依赖的可运行子集，**不是全工程检出**。

```powershell
$reviewSha = '<本轮远端完整SHA>'
$taskSource = 'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923/source'
python -B "$taskSource/prepare_exact.py" --repo . --commit $reviewSha --out ../b-checkpoint-exact-new
if ($LASTEXITCODE -ne 0) { throw '原字节准备失败；保留输出排查' }
Push-Location ../b-checkpoint-exact-new
try {
    python -B "$taskSource/verify.py"
    if ($LASTEXITCODE -ne 0) { throw '哈希核对失败' }
    python -B "$taskSource/reproduce.py" --out ../b-checkpoint-reproduce-new
    if ($LASTEXITCODE -ne 0) { throw '复现失败；保留failure.txt与日志' }
} finally { Pop-Location }
```

准备脚本应取自本次任务分支。它从明确 commit 的 Git blob 读取本包和 dependencies.json 指定文件，原字节写入新目录，逐项验证写后SHA及依赖预期值，并生成根目录 EXACT-EXPORT.json（准确commit、每文件SHA/字节数）。不使用工作区文件内容作为输出，不依赖 autocrlf/smudge 设置，不改任何已有检出。若输出已存在则拒绝，途中失败保留局部目录供诊断，不自动覆盖/删除。新目录的 source 本身也与所选提交blob逐字节匹配。

直接在默认 Windows 检出运行若依赖失配，verify 会列出具体路径、预期/实际SHA（缺失为MISSING）及准备命令。**失配不自动判成换行问题**，更不允许对任意内容归一化后放行。指定提交的依赖blob本身不匹配清单也立即失败。

## 证据与下次复核

旧 SNAPSHOT 原样保存至 `evidence/repair-r1-r2/SNAPSHOT-before-bb964cb.json`；父包清单、dependencies、run01、golden01失败、golden02及旧日志均不覆盖。当前快照仅重新封存返修后的实际集合，不改冻结结果哈希。A 的独立失败由准确报告/diagnostic引用保留，不伪称本机拥有 A 所有外部run目录。

待审仅限研究复现工具返修；本机成功不代表 A Intel 环境已复核通过，不合入 main，不批准生产profile、完整H3或实板/实时。

首次本机真实准备（1786f86，外部 exact-01）退出1：Git show 将长 commit:path 参数参与文件路径判定，报 Filename too long；该局部目录保留。已改用 git cat-file blob 按对象读取，后续在新目录运行，不将首次失败覆盖为通过。
