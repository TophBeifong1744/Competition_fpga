# 分帧与输入适配：开发与动手检查

阶段说明：下文保留分帧阶段的教学步骤；此后已完成六麦定位接入，当前操作见同目录 six-mic-baseline-entry.md。文中的“下一阶段”指这一后续接入步骤。

所属阶段：H1 接口可用之后、H3 完整算法包交付之前的 B 软件开发。当前完成数据准备层；尚未运行定位、跟踪或音频增强。无需等待 C 的真实录音。

## 第一步：理解输入与输出

采样点是一时刻所有麦克风的读数。一帧收集连续 1024 个时刻；步长 512 表示下一帧向后移动 512 点，因此相邻帧重叠一半。在 48 kHz 下，帧长 21.333 ms，步长 10.667 ms。这是数据时间跨度，不是程序耗时，也不是完整系统延迟。

例如 1536 个连续有效采样点，可以产生 `[0,1024)` 和 `[512,1536)` 两帧。这里是 Python 的零起始行索引，右端不包含；它与 CSV 物理行号、原始 sample_id 不同。CSV 有一行表头，所以数据行索引 0 对应文件第 2 行。

遇到错误行或缺样，结束当前区间，下个干净区间从头分帧。错误行保留在读取结果中，算法帧排除它。区间尾部不足一帧就报告未使用点数，不补零；独立文件段不拼接，即便编号相邻。帧之间可以重叠，覆盖统计只计算每个有效行一次。

## 第二步：看两个适配器做了什么

源码：`payload/model/python/audio_frames.py`。依赖原有 `h1_reader.py` 和 NumPy。

| 输入 | 内部统一表示 | 交给算法的帧 |
|---|---|---|
| `ReaderSession.load()` 返回的 H1 四通道 int32，形状 T×4 | float64，T×4；所有通道统一除以 8388608 | 4×1024；保留 H1 的方向使用限制 |
| 六麦旧模型连续有效裁剪，浮点，形状 6×T | float64，T×6；幅度不缩放 | 6×1024；可通过六麦旧基线入口检查 |

H1 的 `-8388608` 转换成 `-1.0`，`8388607` 转换成 `0.9999998807907104`。这是固定比例的单位转换；不会各通道独立归一化，也不会抹平通道幅度差异。

六麦适配器是独立的 Python 内存接口 `six-mic-baseline-synthetic-v1`，不是 H1 0.3 协议扩展。必须显式提供 48 kHz、与旧模型一致的六麦坐标及顺序、来源名称、生成代码 SHA-256。它拒绝四通道、转置错误、非浮点、NaN/Inf 和不匹配的几何；不猜测轴、不补通道、不重采样。生成代码哈希是调用方声明；适配器另算标准化数组哈希以追溯内容，不验证声明来源真实性。

旧模型渲染使用周期延迟，调用者必须先选取有效内部裁剪，再传适配器；不能把周期接缝当成真实连续音频。不同试验不能拼成一个连续段。六麦文件格式、生成场景的自动加载及完整算法 CLI 留待统一入口阶段开发。

本层不去直流、不滤波、不加 Hann 窗。旧 `gcc()` 已经内部加窗，重复加窗会改变原基线。帧输出仍是送入算法前的数据。

## 第三步：自己运行一个能检查的例子

在 `F:\NUEC\task-packages\PKG-B-ALG` 打开 PowerShell，执行：

```powershell
& 'C:\Users\BryanZheng\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B run_framing_demo.py --out evidence/my-framing-demo-01
```

每次换一个新的输出目录名，程序拒绝覆盖非空目录。它生成四通道固定码型，包含 3073 个数据行；第 1536 行索引处缺了一个编号，并将当前行标记 `drop`。原始编号从 9007199254740993 开始，专门验证大整数不会经过浮点数而丢失精度。

你只需核对以下表格与输出是否一致：

| 帧 | 数据行区间（不含右端） | reset_before | 含义 |
|---|---|---|---|
| 0 | [0,1024) | true | 第一段开始，后续状态应清空 |
| 1 | [512,1536) | false | 第一段的重叠帧 |
| 2 | [1537,2561) | true | 错误之后的新段，后续状态应清空 |
| 3 | [2049,3073) | false | 第二段的重叠帧 |

打开输出目录里的 `framing.json`：`frames` 应为 4、`error_rows` 为 1、`missing_samples` 为 1；没有任何一帧包含数据行索引 1536。这些是三种不同统计：缺失样本没有 CSV 行，错误行有 CSV 行但不能进帧，帧数量来自足够长的连续区间。

正式 A 样例只有 6 行和 2 行，本来就不能产生 1024 点帧；输出零帧是正确结果。教学用长码型单独生成，未修改 A 的参考样例，也不是四麦声学模拟。

## 第四步：开发接口与验证

```python
from h1_reader import ReaderSession
from audio_frames import adapt_h1, iter_frames, framing_summary

recording = ReaderSession().load('某个包含 metadata.json 和 samples.csv 的目录')
segment = adapt_h1(recording)
print(framing_summary(segment))
for frame in iter_frames(segment):
    print(frame.summary())
    # frame.samples: 4×1024。此处尚不调用六麦算法。
```

六麦调用方式（`x` 是旧模型已裁剪好的 6×T 浮点数组）：

```python
from audio_frames import adapt_six_mic_baseline, iter_frames, to_six_mic_baseline

segment = adapt_six_mic_baseline(
    x, sample_rate_hz=48000, positions_m=positions,
    source_id='试验名称、种子与裁剪区间', source_sha256=generating_source_sha256,
    first_sample_id=crop_start,
)
for frame in iter_frames(segment):
    gcc_input = to_six_mic_baseline(frame)  # 返回独立的 6×1024 数组
    # 下一开发阶段接 tau = baseline.gcc(gcc_input)。本轮尚未接入。
```

`FrameSpec` 默认 1024/512，也支持 `1 <= hop <= length` 的整数配置；六麦旧基线守卫仍要求 6×1024、48 kHz 与专用输入来源。H1 模式可以做四通道格式分帧，但固定码型始终禁止 DOA；坐标未知也禁止 DOA。几何存在不代表物理校准已通过。

帧包含原始首末编号、数据行区间、区间索引、段内帧序号、时间范围及 `reset_before`。时间以该段首个记录编号为零点，由整数编号差除以采样率计算，保留缺样造成的时间间隔；不是墙上时钟时间。HOLD/跟踪状态的实际重置要由下一阶段消费者执行，本层只提供标记。不同段的相对时间不可直接连成同一时钟。JSON 大编号需要无损整数解析，JavaScript 不能直接当普通 Number。

适配器复制输入；帧数组独立且默认只读，避免重叠帧被下游原地操作串改。`InputSegment` 和 `AudioFrame` 属于包内可信对象，需通过适配器创建并保持不变；不是对任意手工拼造对象的防御性解析器。仍会将完整段放入内存，本轮没有长录音吞吐或实时性能结论。

运行完整回归：

```powershell
& 'C:\Users\BryanZheng\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B run_validation.py --out evidence/my-framing-validation-01
```

测试覆盖原有读取器、1023/1024/1536 等帧边界、缺样/错误/重启、uint64 上界、通道与幅度、帧隔离、六麦形状/几何及入口限制。测试通过只证明本层行为，不证明定位性能。

你负责运行示例、核对表格并了解输出含义；代码、边界验证和证据整理已由助手完成。下一开发阶段在同包内接六麦基线，输出每帧方向、有效标志与拒绝原因，再接评价。无需为本子功能单独等 A 批准；完整 H3 版本交 A 复核，由 A 确认后合入。
