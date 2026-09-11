# 四路短诊断录音：H2 最小交接清单

2026-09-11；A 工作执行负责采集/导出实现，H2 支持只核对交换格式，B 负责接收诊断。按本阶段 README、A.md、B.md 执行；9月16日为进展检查，不新增交接点。

**先交一段可解析的真实四路短数据，B收到即诊断；不等两种场景齐全、精细补证或一小时长稳。** 建议1～10秒但不是硬性时长门槛。只有单麦或码型就按实际交付，不记四路H2完成；不新增四麦声学模拟。

## 1. 一段录音交什么

放在本任务目录的 `captures/<segment-id>/`，另在本任务 `evidence/` 留验证和B回执：

- [ ] `samples.csv`：真实四路同一采样时刻的码值、原始编号与错误。
- [ ] `metadata.json`：下表全部H1必填字段。未知项显式写明，不靠读取器猜。
- [ ] 原始抓取文件或可追溯原件引用、SHA-256；若非CSV，给实际转换脚本路径/版本及完整运行命令。原始文件和失败记录不覆盖。
- [ ] 简短录制说明：操作者/时间、真实通道数和列序对应、场景、声源/摆放信息知道多少写多少；说明来源是用户标注、串口转录还是自动日志。
- [ ] 当前采集/导出代码、配置版本与运行入口；新运行顺手记录所用构建路径/标识，不倒填历史加载记录、不要求补整套旧证据。
- [ ] 文件字节数、样本组数、首尾ID、错误/缺号摘要及本次验证输出；原始数据、CSV、metadata的SHA-256。哈希绑定文件，不代替真实性核查。

原始抓取点应说明在抽取/校准/滤波链的哪一级、如何到DDR/文件。数值转换须写清符号扩展、位移/增益、舍入、饱和与错误映射；不按各通道峰值独立归一化。

## 2. H1 0.3 的精确字段（不重新签字）

阶段 A.md 的“H1六字段”不是列数规范：现行合同和读取器实际固定为以下 **7列**，以此为准，不改阶段文件：

```text
sample_id,mic0,mic1,mic2,mic3,stream_error,error_flags
```

一行是一组同步四通道样本。UTF-8；整数十进制，无浮点/科学计数法/空白；无重复表头、空数据行。`error_flags`为空时最后一列仍保留。CSV不定义DMA字宽、字节序或物理接口。

| metadata字段 | 本次填写规则 |
|---|---|
| `schema_version` | `ss-data-draft-0.3` |
| `acquisition_id` | 非空；一次启动采集的标识，重启换新值和目录 |
| `config_version` | 非空；绑定实际完整配置，映射/采样率/格式等变化须换版本 |
| `channel_order` | 严格为 `["mic0","mic1","mic2","mic3"]`；另附实际模块/接线到列的映射，不复制单麦凑列 |
| `coordinates_m` | 有依据的4×3有限数值，单位m；完全未知填 `null`，并在 `provisional_fields` 说明，禁止DOA |
| `geometry_version` | 非空；坐标未知也须明确版本，不从通道数猜几何 |
| `coordinate_system` | `x-forward_y-left_z-up` |
| `direction_convention` | `array-to-source` |
| `angle_unit` | `deg` |
| `sample_rate_hz` | 实际使用的配置值，通常48000；未经测量就在 `provisional_fields` 注明配置值而非实测 |
| `sample_format` | 固定见下方，不把码位数当声学有效精度 |
| `source_kind` | 有录制来源依据的真实麦克风输入用 `hardware-audio`；码型必须为 `hardware-test-pattern` 或相应synthetic类型 |
| `evidence_level` | 首批真实录音用 `diagnostic`，不能自行写 `accepted` |
| `capture_point` | 非空，填写实际抓取点；不知道写 `unknown` 并在暂定项解释 |
| `provisional_fields` | 对象；键是未知/暂定字段路径，值为非空原因；没有暂定项才用 `{}` |
| `calibration_status` | 未标定用 `not-calibrated`；不得由文件可解析推定已标定 |

```json
{"encoding":"signed-pcm","storage_dtype":"int32","valid_bits":24,"alignment":"right","fractional_bits":0}
```

PCM范围 `[-8388608,8388607]`，负数写负值，符号扩展不改变增益。H1保存整数码，B的浮点适配为 `pcm / 8388608`；不是声压标定。24位容器不等于24位有效声学精度。

特别注意：单麦包用过 `source_kind=user-reported-hardware-audio`、`configuration_version`、`microphone_positions_m`。这些不是四路H1标准字段/枚举，不能照搬：四路须分别填写合法 `hardware-audio`（附来源说明）、`config_version`、`coordinates_m`。来源证据不明则不能靠换标签称实录；现有信息不足时先反馈缺口。可用额外描述字段/sidecar保留用户标注、未测参数和日志性质，不覆盖H1标准语义。

## 3. 编号、错误与分段不能丢

- [ ] `sample_id`为精确uint64整数，允许首行非零；不经float，不排序、重编号、补零或拼接片段。
- [ ] 同段严格递增，允许有据可查的跳号；若出现跳号，当前行必须 `stream_error=1` 且 `error_flags`含 `drop`。缺失区间为前一ID+1至当前ID−1。
- [ ] `stream_error=0`时错误列为空；为1时非空。0.3允许 `drop;overflow;relock;unknown` 中的一个或多个，分号分隔、无空格/重复。原因不明用 `unknown`，不自造错误码。
- [ ] 原始硬件flags必须保留并给映射表；单麦bit1饱和不能误映射为H1的drop/overflow。H1没有独立clip词，若需作为错误行传递，用 `unknown` 并在sidecar标明具体原因；完整原flags/削顶计数照存，不静默丢失。
- [ ] sticky状态不是每行一次新事件；记录清除/重启语义。未观测到缺失编号时不凭overflow计数虚构精确丢样数。
- [ ] 错误行保留供诊断，干净连续区间在错误行或跳号处切断；跨gap不能拼成1024点算法帧。
- [ ] 重启换 `acquisition_id`；配置变化另存目录，同次未重启可保留acquisition及原编号。逐段检查不能替代同会话跨段版本冲突检查。

## 4. 已有可复用入口与边界

| 入口 | 可直接复用 | 不能直接套用 |
|---|---|---|
| `docs/minimal-data-interface.md`；冻结副本 `task-packages/PKG-A-ACQ/payload/docs/minimal-data-interface.md` | H1 0.3字段、错误、版本语义；H1已确认，不再签字 | 旧正文“待共同确认”属历史状态；以本阶段安排为准 |
| `task-packages/PKG-B-ALG/payload/model/python/h1_reader.py` | 四路CSV+metadata读取、幅值摘要、错误/缺失区间、同一ReaderSession配置冲突检查 | 不解码原始BIN，不实现DMA，不给DOA/音质验收；整段读内存只适合当前短片段范围 |
| `task-packages/PKG-B-ALG/payload/docs/h1-reader.md` | API、CLI和诊断输出语义 | `PASS_FORMAT_ONLY`不是H2真实性或正式M1批准 |
| 单麦已发布提交 `93a12aab1eb5d2e70e118761a35d2d654845424b` 中 `task-packages/PKG-A-H2-MONO-DIAGNOSTIC/source/mono_delivery.py` | FNV/SHA、signed24符号检查、保留原ID、CSV导出和拒绝覆盖的实现思路 | 固定两份单麦SHA、768000字节、48000条、`<IIiI`及单麦schema；拒绝所有gap的旧干净捕获规则不等于H1允许保留异常区间 |
| 同一单麦包的 `source/file_manifest.py`、`source/test_delivery.py` | 文件哈希校验方式和截断/符号/编号/flags负例思路 | 原SHA清单只绑定旧文件；原10项测试不证明新四路导出已通过 |

本轮共享目录尚无上述单麦包路径时，应从既有发布/归档副本读取对应入口，不能把文件未在当前落后checkout出现判成“采集实现不存在”。不切换共享main、不另建重复框架；由A在既有任务内适配真实四路布局。四路每记录字节数、TLAST位置、ID/flags封装须以A本次实现为准，本清单不猜定。

## 5. B拿到数据即可运行

Python环境沿用B已有环境（读取器需要NumPy）。仓库根目录，替换为实际存在的片段目录：

```powershell
python -B task-packages/PKG-B-ALG/payload/model/python/h1_reader.py task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/captures/<segment-id>
```

同一次CLI可传多个实际目录，检查跨段配置/编号一致性。不要把模板尖括号当实际路径执行。成功预期退出0、`PASS_FORMAT_ONLY`；失败退出2，返回错误code/field/CSV行信息。此轮只静态核对入口，不伪造“新四路数据已跑通”的输出。

首批回执写到B的 `task-packages/PKG-B-ALG/tasks/four-channel-receipt-01/`，并给A留引用：

1. 审核提交或输入文件SHA、命令、能否解析。
2. 四路样本数、幅值/极值码统计、异常通道、原ID区间、缺号/错误及配置情况。极值码计数不直接等于真实削顶。
3. 可观察结论、未知项、下一处应排查什么；只有相同波形/高相关不能自动判通道复制，应结合映射与原始数据诊断。

## 6. 本阶段完成与不等待条件

四路真实短录音及来源清楚、可解析、B有反馈后，才记H2四路诊断交付完成。正式M1同步/固定差异/停止重启/长稳有多少证据列多少，未全满足不能宣称正式采集通过。

坐标/标定不足时先做格式、幅值及原始相关性诊断，不报告角度精度/SNR达标，不送六麦定位。精细电气/IO/历史加载身份补证按 `docs/deferred-acquisition-risks.md` 暂缓；新测试正常留配置与日志即可，不增加仪器、PYNQ迁移或一小时测试前置。明确接错供电/短路等安全问题仍须立即处理，不能猜接线。

本轮仅完成README/A/B阶段页、H1及既有单麦导出入口的只读核对和此清单；不修改NEXT-ACTION、RTL、活动工程或冻结证据，不进行新板测、录音、声学模拟、提交或推送。
