# A/B 最小数据接口

版本：`ss-data-draft-0.2`，2026-09-08。状态：可据此开发的起草版本，待 A/B 共同确认；不是物理接口冻结。本文件定义离线交换格式，不替代 AXI/DMA 二进制布局，也不改变既有 RTL packed 顺序。

## 首版交换格式

每段数据包含 `metadata.json` 和 `samples.csv`。先采用易读格式，后续二进制/WAV适配由 A/B 在接口内扩展，不阻塞读取器。CSV 每行是一组同采样序号的各通道，不是各通道独立时间轴。

| 字段 | 起草约定 | 状态 |
|---|---|---|
| `schema_version` | `ss-data-draft-0.2` | 软件版本，不是硬件版本 |
| `channel_order` | V1 `[mic0,mic1,mic2,mic3]`，数组列顺序 | 暂定软件映射，实物映射待 A/B 核对 |
| `coordinates_m` | 与 channel_order 一一对应的 N×3 坐标，单位 m | 首测候选为正方形边长 0.04 m；实际值与排列须随数据明确写出，不由读取器猜测 |
| 坐标轴 | x 前、y 左、z 上；方向指向声源，角度单位 deg | 暂定共同约定，须做正负轴符号测试 |
| `geometry_version` | 每套坐标唯一字符串，不从通道数推断 | 必填 |
| `sample_rate_hz` | 暂定 48000，实录写实际配置值 | 是否实测另填状态 |
| `sample_format` | 暂定 signed PCM、存储 int32、有意义 24 bit、右对齐并符号扩展，fractional_bits=0 | 仅软件起点，不声称采集原始精度是 24 bit |
| `sample_id` | 每行十进制非负整数，按一次 acquisition_id 内的原始采样时刻递增 | 丢样保留跳号；重启新 acquisition_id；内部按 uint64 校验，不经浮点转换 |
| `config_version` | 一段数据只用一个配置版本；改变配置另存一段 | 每版关联完整元数据，不只存无从查验的编号 |
| `stream_error` | 每行 0/1，0=未报告完整性错误，1=存在错误 | 0 不是硬件验收通过 |
| `error_flags` | 每行文本列表，以分号分隔：drop/overflow/relock/unknown 等 | 不定义硬件 bitmask；未知不能写成正常 |
| `acquisition_id` | 一次采集/输入序列的唯一标识 | 必填，复位/重开新值 |
| `source_kind` | synthetic-code / synthetic-acoustic / hardware-test-pattern / hardware-audio | 区分格式码型、声学模拟、板上码型与声学录音 |
| `evidence_level` | synthetic / diagnostic / accepted | 首批实录 diagnostic；accepted 必须关联正式验收记录 |
| `provisional_fields` | 列出暂定/未知字段及原因 | 未标定量另附状态，不能默认已校准 |

V1 的 CSV 头为 `sample_id,mic0,mic1,mic2,mic3,stream_error,error_flags`。底层四路 packed 为 `{mic3,mic2,mic1,mic0}`（mic0 位于低位）；文件列从 mic0 起，适配器显式转换，不能把两种写法视为倒序冲突。

为尽快测试，可使用固定码型和边界整数写读取器测试，不算新四麦声学仿真。已有六麦软件数据必须使用独立 channel_order/geometry_version 和六列配置，不能伪装成四路或改写现有结果文件。具体六麦声学坐标按其原 config.json 读取。

供 A/B 起步的明确候选坐标（不是实物测量）：`geometry_version=square40-provisional-0.1`，mic0=(-0.02,-0.02,0)、mic1=(0.02,-0.02,0)、mic2=(0.02,0.02,0)、mic3=(-0.02,0.02,0)，单位 m。这只是 H1 软件默认配置；实录若映射不同必须写实际顺序并升版，不重贴旧数据标签。

## 读取器最低行为（B 实现，A 消费）

- 拒绝未知 schema、缺列、坐标数量与通道数不一致、重复通道、PCM 越界、无法识别的配置；定位首个错误行。
- 保留采样跳号与错误标记，不默默重新编号、裁切或补零；允许隔离可解释的连续诊断区间。
- 不同 acquisition/config/geometry 分段，不默认拼接；实录未知坐标仍可做幅值/格式诊断，但方向输出须标假设或无效。
- 最小测试覆盖列序、正负/零/极值、跳号、重启、错误标志和版本拒绝，记录预期与实际。

本文件不要求新建一套复杂验证平台。A/B 在同一完整工作包内维护配置和测试；参数确认一次记入 README，只有实质接口变化再版本化对齐。
