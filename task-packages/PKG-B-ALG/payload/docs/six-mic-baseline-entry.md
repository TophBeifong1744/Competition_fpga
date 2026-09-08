# 六麦基线接入：运行与输出

阶段说明：本文记录独立定位入口；后续已接入范围和跟踪，最新运行方法见同目录 sector-tracking-entry.md。独立定位命令仍保持原行为。

版本 baseline-entry-0.1。所属阶段为 H1 之后、H3 之前的 B 离线软件开发。已接通：六麦合成输入 → 1024/512 分帧 → GCC-PHAT 的 15 对时差 → 最小二乘方向 → 逐帧输出及基础统计。跟踪、方向范围锁定与音频增强尚未接入。

## 本轮代码职责

| 文件 | 用途 |
|---|---|
| `six_mic_baseline_core.py` | 旧模型数值核心及合成输入生成函数的原文摘录，只依赖 NumPy |
| `six_mic_localize.py` | 六麦独立文件输入、算法调用、输出整理、统计和命令行 |
| `test_six_mic_localize.py` | 同帧对照、轴向符号、拒绝原因、输入及命令行回归 |
| 包根目录 `run_baseline_regression.py` | 生成可复核的 162 帧对照及六个轴向 golden |

原始完整源码按字节保存在 `reference/six-mic-baseline/`，原文件 SHA-256 为 `b50cdf8eafad2b14998156e705e30f1a353ee6c4b8b3f87ce461fe8e4f086a8b`。LF 规范化哈希为 `fef3cf3de90750f21003a7d23abd02e2b623bc71c597deb9480cf48defa6a4d1`。摘录保留 FS 等常量到 make_trial 的数值代码，没有修改计算、阈值或生成方法；测试逐项比较 AST 验证这一点。完整原脚本的绘图、音频导出和主程序不参与本轮运行。

原算法在 GCC 内加一次 Hann 窗，频带 300–4000 Hz；采样率 48 kHz，声速 343 m/s，固定六麦几何。方向接受条件沿用至少 5 个有限时差、矩阵秩 3、原始方向范数在 [0.7,1.3]、时差残差不超过 0.5 点。没有新增定位策略。

## 第一步：运行干净声源

在 PowerShell 执行：

```powershell
cd F:\NUEC\task-packages\PKG-B-ALG
& 'C:\Users\BryanZheng\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B payload/model/python/six_mic_localize.py --demo clean --out evidence/my-baseline-clean-01
```

输出目录必须尚不存在，每次运行换一个新目录名。默认目标方位角 35°、俯仰角 25°，使用旧模型生成 4096 点，再保留内部 [1536,3072) 的 1536 点，形成两帧。实际定位并不使用真值，真值仅用于算误差。

| 输出 | 查看内容 |
|---|---|
| `input/metadata.json`、`input/samples.npy` | 保留下来的独立六麦合成输入，可重放 |
| `frames.json` | 每帧方向、有效标志、拒绝原因、15 对时差和编号 |
| `summary.json` | 有效帧率、有效帧误差分位数及错误率 |
| `run.json` | 源码与输入哈希、阈值、坐标相关约定、运行环境和限制 |

同一个输入可重放，无需再次生成：

```powershell
& 'C:\Users\BryanZheng\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B payload/model/python/six_mic_localize.py --input evidence/my-baseline-clean-01/input --out evidence/my-baseline-replay-01
```

在相同源码和运行环境下，两次的 frames.json、summary.json 和 run.json 应完全一致，测试已检查。命令返回 0 表示处理完成，不等于所有帧有效；输入错误返回 2，stderr 包含 JSON 错误。执行中失败可能保留不完整输出目录，不能把它当成完成证据，重试应使用新目录。

## 第二步：读懂一帧

有效帧主要字段如下：

- `unit_vector`：从阵列指向声源的单位向量 [x,y,z]；x 前、y 左、z 上。
- `azimuth_deg`：atan2(y,x) 得到的方位角，范围约 [-180°,180°]；正值偏左。
- `elevation_deg`：俯仰角，范围 [-90°,90°]；正值向上。
- `valid`：是否通过原基线自身的数值检查，不能保证选中了你想要的声源。
- `angular_error_deg`：与真值方向的三维夹角，仅在提供真值且帧有效时计算。
- `first_sample_id`、`last_sample_id`、`row_start`、`row_stop`：对应原输入的编号和区间；编号保持整数，不经过浮点转换。
- `reset_before`：分帧器传递的重置标记；当前算法逐帧独立且无状态，未来跟踪器再消费这个标记。

正上或正下时，方位角本身无定义；若水平分量小于 1e-12，方位角为 null，而方向和俯仰角仍可有效。不输出距离。

无效帧的 unit_vector、azimuth_deg、elevation_deg、angular_error_deg 一律为 null。旧求解器失败时返回的 [1,0,0] 占位值不会成为对外方向。缺失的成对时差和未定义诊断也转换为 JSON null，禁止输出非标准 NaN。

| rejection_reasons | 含义 |
|---|---|
| `insufficient_pairs` | 有限时差少于 5 对 |
| `rank_deficient` | 有限时差对应几何不能完整约束三维方向 |
| `norm_out_of_range` | 原始方向向量范数不在原基线接受区间 |
| `residual_too_large` | 多对时差无法充分符合一个共同方向，残差超过 0.5 点 |

一帧可同时有多个原因，所以原因计数之和可能超过拒绝帧数。这里报告的是原有数值检查，不把残差高直接解释成某种确定的物理故障。

## 第三步：查看困难场景和静音

将命令中的 `--demo clean` 分别换成 `--demo band_noise0`、`--demo interferer0` 或 `--demo silence`，并换新的输出目录。前两个分别沿用同频带独立噪声约 0 dB、等强竞争声源的旧生成方法；silence 是额外的全零边界测试。

可以设置 `--az`、`--el`、`--repeat` 来选择演示方向与旧模型重复编号。这三个参数仅用于 --demo。repeat 进入旧模型的种子公式，不是程序执行次数。内置示例只有两个重叠帧，不能用它们估计总体声学性能，也不替代此前 2700 行基线审计。

统计约定：有效率 = 有效帧/全部帧；P50/P95 仅使用有真值的有效帧；有效但三维误差严格大于 30° 计为错误输出。错误率分别给出以全部帧和有效帧为分母的值。无真值时不计算误差或错误数；零有效帧时 P50/P95 和有效帧错误率为 null；零总帧时有效率也为 null。零错误数可能来自全拒绝，必须结合有效率一起读。

## 独立六麦输入约定

使用 `ss-six-synthetic-offline-0.1`，文件为 metadata.json 和 samples.npy。它属于包内离线合成输入，H1 `ss-data-draft-0.3` 四通道文件不能送入此入口，也不接受硬件录音声明。

samples.npy 是 6×T 的有限浮点数组，只允许数值 NPY，禁止 pickle。metadata 必填 schema_version、source_kind、evidence_level、channel_order、sample_rate_hz、coordinates_m、coordinate_system、direction_convention、angle_unit、source_id、source_sha256、first_sample_id 和 crop。坐标/顺序/采样率必须匹配旧基线；crop 为 start、stop、reason，样本数等于 stop-start，first_sample_id 等于原合成源裁剪起点。完整示例见教学生成的 metadata.json。

truth_unit_vector 可缺省或为 null，提供时必须是有限单位向量；它表示这段数据共同的固定目标方向。暂不支持逐帧移动真值。数据必须来自一个连续有效裁剪，不得跨实验拼接。裁剪理由和源代码哈希属于声明，加载器校验格式并记录实际文件哈希，但不能证明数据真的由声明的源码生成。内置演示按旧模型保留内部裁剪，避免周期接缝进入报告帧。

API 使用：`load_input(directory)` → `run_segment(segment, truth)` → `(rows, summary)`；`localize_frame(frame, truth)` 可单帧调用。已有六麦内存适配器仍可直接使用。包内 segment/frame 是可信工厂对象，不应手工篡改。全段和逐帧结果驻留内存，没有长录音吞吐或硬件实时结论。

## 验证与下一阶段

完整回归运行包根目录 run_validation.py；同帧对照及 golden 运行：

```powershell
& 'C:\Users\BryanZheng\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B run_baseline_regression.py --out evidence/my-baseline-regression-01
```

对照覆盖旧模型 9 个场景、3 个方向、3 个重复、每段 2 帧，共 162 帧。参考计算从完整原始源码的数值定义构建，不调用新入口；对照容差为绝对 1e-12。另提供六个轴向理想时差和可直接加载的 axis-waveforms.npz，数组形状 6×1024。该 NPZ 是验证向量，不是命令行输入格式；其旧基线预期值记录于 axis-golden.json。

本轮接入完成后，可以在同一包中接允许方向范围和跟踪状态，再做整批评价、音频对照与定点准备。原低信噪比和竞争声源问题没有被本次接口接入解决。H2、H3 仍未通过；完整包交 A 明确复核，由 A 合入总工程。
