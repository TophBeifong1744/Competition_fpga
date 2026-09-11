# H1 读取器实现约定

支持唯一 schema：ss-data-draft-0.3；四路列顺序 sample_id,mic0,mic1,mic2,mic3,stream_error,error_flags。代码不会猜测格式、扩展成六路、补零、重编号、排序或拼接记录。

## Python API

```python
from h1_reader import ReaderSession
session = ReaderSession()
recording = session.load('path/to/segment')
print(recording.summary())
for region in recording.clean_intervals:
    samples = recording.samples[region['row_start']:region['row_stop']]
```

sample_ids 是 uint64 一维数组，samples 是行×4的 int32 数组，stream_error 是 uint8 数组；errors 与 flags 按原行保留。负数精确转换为 int32，没有归一化或增益调整。所有浮点统计只用于幅值均值，不用于采样编号解析。CSV 字面量允许十进制正负号和前导零（0.3 未禁止），拒绝浮点/科学计数法/空白/十六进制；ID和stream_error再作非负范围检查。

clean_intervals 使用零基行索引、左闭右开 row_start/row_stop；不是 CSV 物理行号。每区间保存首尾原始 sample_id。任何错误行切断区间并保留在完整数据中；有明确跳号才列出 missing_intervals。不因 overflow/drop 标记就虚构缺失数。没有足够长的连续区间时，后续分帧器不得跨间断拼成一帧。

样例 code-pattern 产生三个区间 [0,2)、[3,4)、[5,6)，长度2/1/1；六行都保留。唯一明确缺失 ID 为9007199254740994。两条错误行是数据行3（drop;overflow）和5（unknown），物理CSV行4和6。restart 是新 acquisition，采样号0、1可接受，不与前一记录拼接。

## 元数据、版本与会话范围

JSON 重复键、非有限数、数字字段的布尔值、错误样本格式和不匹配坐标维度均拒绝。未知描述字段保留。coordinates_m=null 时必须给 provisional 原因，允许格式/幅值诊断；不能方向求解。码型无论坐标是否齐全都标记 forbidden_non_acoustic_input。

已提供坐标的声学输入只标记 diagnostic_only_requires_geometry_and_algorithm_validation，仍须后续算法/标定验证，不由本读取器签发 DOA 使用许可或验收通过。metadata 的 accepted/calibrated 是来源声明；相应记录引用必填，但真实性要人工核对，summary 始终显示 acceptance_verified=false、calibration_verified=false。

同一 ReaderSession 检查 config_version 对应配置一致性，以及 geometry_version 对应坐标/顺序/坐标系一致性。配置身份包含 schema、通道/几何、坐标/方向/角度约定、采样率/样本格式、抓取点、暂定项、标定状态及记录。acquisition_id、source_kind、evidence_level、验收引用和无关描述是来源/分段信息，不用作配置冲突键。这里对暂定说明变更也要求新配置版本，采用保守一致性检查。

同一 acquisition 的片段必须按时间先后显式加载；重叠或计数倒退拒绝，重启必须新 acquisition。不同片段不自动拼接，片段间不可观察部分不虚构为精确丢样。新 config_version 可以直接读取，只要参数齐全受支持，无硬编码白名单。

版本注册表仅在当前会话内有效，不是磁盘数据库。为检查多个文件之间的冲突，应复用同一 ReaderSession，或在同一次 CLI 调用中给出多个目录。单独启动两个程序不能发现彼此的版本冲突。失败读取不写入注册表，也不修改原文件。

## 数值与证据边界

满量程码值计数不等于削顶结论；样例故意含极值。幅值报告包含错误行，使用名称 amplitude_all_rows；干净区间仅指格式完整，不代表静音、无噪声或硬件可靠。

JSON 诊断输出中的 sample_id 仍是精确十进制整数；JavaScript 等会默认转 double 的消费者应使用无损JSON/BigInt解析。不能让 UI 再把大编号变成不精确值。

本版本整段读入内存，适用于 H2 首批短片段与格式验证；未验证小时级CSV内存和吞吐。没有wav/二进制/DMA布局支持，没有DOA或音频输出，不增加四麦声学模拟。后续读取器/分帧器扩展仍在 PKG-B-ALG 内进行。
