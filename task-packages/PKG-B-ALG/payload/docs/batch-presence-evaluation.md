# 多种子整批对照与目标存在标注

版本 batch-presence-0.1；仍在 PKG-B-ALG 内开发。原定位与跟踪参数保持不变，本轮增加实验和评价，不改进算法、不覆盖历史结果。

## 实验方案

冻结计划位于 payload/config/batch-presence.json，跟踪配置为 payload/config/sector-tracking.json。共5场景×10个独立种子，每次5秒、48 kHz、六通道；1024点帧长、512点步长，每次467帧。声学输入共23350帧；原定位、仅圆锥、圆锥加跟踪共享同一帧及原定位结果，共70050行对照。各试验重新创建跟踪状态。

| 场景 | 目标 | 额外声音 |
|---|---|---|
| drop_return | 两次出现，中间和两端不发声 | 独立宽带噪声，幅度0.1 |
| band_noise0 | 同上 | 每通道独立同频带噪声，单位RMS，约0 dB |
| equal_interferer | 同上 | 方位90°、俯仰0°的连续等强竞争源及宽带噪声 |
| interferer_only | 始终没有目标分量 | 同上，只有范围外竞争者及噪声 |
| same_cone_competitor | 两次出现 | 方位20°、俯仰0°的连续同锥竞争者及噪声 |

目标第1段0.5–2.0秒，方位0°、俯仰10°；第2段2.8–4.5秒，方位−10°、俯仰10°。每段两端有20 ms余弦幅度渐变。两个方向均在默认圆锥内。每次生成一个连续宽带探针，按旧1.5 m球面模型渲染，前后各预留1536点再裁剪。幅度包络在渲染后施加，表示阵列处的受控分量变化；没有实际房间衰减或物理人员进出模拟。

随机种子2026090800–2026090809预先固定；目标、竞争者、宽带噪声、同频带噪声使用独立随机流，相同种子跨场景可复用相应声源。算法使用源代码中的原GCC/LS，后处理沿用冻结5帧捕获策略。本轮没有根据结果调参。

## 标注怎样定义

“目标在场”在本实验中仅指目标声学分量存在，不指一个人是否在房间。标注来自生成器包络，不由算法输出反推：

- target_active：整帧同一个目标段的包络都为1，方向真值确定。
- target_absent：整帧所有目标段的包络都为0；竞争者和噪声可以继续发声。
- transition：其余情况，包括渐变、跨开关边缘或跨方向段的帧。

默认计划下，除 interferer_only 外，每个试验289个在场帧、163个不在场帧、15个过渡帧。interferer_only 的467帧全部不在场。逐帧标注包括行区间、原始编号、段索引、目标方向、目标非零样本数和满幅样本数。

同场景的时间表不随种子变化，因此 annotations/ 每场景保存一份标注，10个试验记录分别引用它的SHA-256。标注总计2335个不同时间窗口，对应所有23350声学帧。编号含裁剪起点偏移；row_start/row_stop相对裁剪后的输入，右端不含。

定位与跟踪先处理完整连续数据，再附加标注和评分。标注不会屏蔽输入帧、强制释放或帮助选择声源；过渡帧也正常驱动状态，只从稳态准确率和误输出率分母中排除。测试通过改变标注而保持波形不变，验证算法输出不会随真值改变。

## 统计口径

| 字段 | 分母及解释 |
|---|---|
| active_fresh_rate | 在场帧中有新有效方向的比例 |
| p50_error_deg / p95_error_deg | 仅在场且新有效帧的三维夹角误差 |
| active_wrong_rate_all | 在场且新有效误差严格>30°的帧数 / 全部在场帧 |
| active_wrong_rate_fresh | 上述帧数 / 在场新有效帧 |
| active_correct_within10_rate | 在场且新有效误差≤10°的帧数 / 全部在场帧 |
| absent_false_output_rate | 目标不在场时仍输出新方向的帧数 / 全部不在场帧 |
| absent_hold_display_frames | 目标不在场时仅显示旧方向的HOLD帧数，单独报告 |
| transition_frames / transition_fresh_outputs | 过渡帧及其新输出数，单列 |

HOLD不计新有效、角度误差或不在场错误新输出。范围外竞争者单独发声时，原定位给出竞争者方向可以是正确DOA，但从“只输出指定目标”的任务看仍算错误目标输出；这不能解释为原定位计算本身一定错了。

无在场帧时在场率为null；有在场帧但零新有效时有效率为0、P50/P95及以新有效为分母的错误率为null。CSV将null写为空单元格，JSON保留null。没有用0代替未定义准确率。

per-seed.csv保留150组逐种子结果；pooled.csv/json把同场景的种子样本合计，误差分位数直接从符合条件的帧计算，不平均各种子的P95。seed-distribution.csv给出各种子率的中位数、最小/最大值及有定义种子数。paired-differences.csv逐种子列出跟踪器减原定位/仅圆锥的差；比例差单位为0–1，乘100才是百分点。重叠帧不是独立重复；种子范围是描述性统计，不是置信区间或显著性结论。

latencies.csv记录每个目标段从包络起点，到第一个处于完整在场窗口且误差≤10°的新有效输出的时间。它包括渐变与帧对齐，不是硬件延迟，也不是单纯状态进入LOCKED的时间。无正确捕获记found=false、延迟null；始终无目标的场景记applicable=false。

## 运行与复现

```powershell
cd F:\NUEC\task-packages\PKG-B-ALG
& 'C:\Users\BryanZheng\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B payload/model/python/batch_presence.py --plan payload/config/batch-presence.json --config payload/config/sector-tracking.json --out evidence/my-batch-presence-01
```

输出目录必须不存在。frozen-plan.json与tracking-config.json先写入新目录；完成后才生成run.json中的COMPLETE_SYNTHETIC_BATCH状态。失败后留下的部分文件不能当成已完成结果，重试请使用新目录。

无需保存约576 MB的完整浮点输入副本：源文件、生成方案与种子足以再生成，每个trial记录实际输入数组的SHA-256（时间×通道、float64小端顺序）。算法源文件哈希、所有结果文件哈希及运行环境记录在run.json；若需要取回某次波形，可以调用batch_presence.generate(plan, scenario, seed)，其返回segment.samples为时间×通道数组。

本轮实跑两次，batch-presence-run-01/ 与run-02/的65个生成文件全部按字节一致。独立审计不调用实验的标注/统计函数，使用整数区间重建标注，从70050行结果复算角度、分母、成对差值、种子分布及延迟，并检查哈希：

```powershell
& 'C:\Users\BryanZheng\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B audit_batch_presence.py --run evidence/batch-presence-run-01 --repeat evidence/batch-presence-run-02 --out evidence/my-batch-audit.json
```

审计输出路径须不存在。完整单元回归仍运行run_validation.py --out一个新目录。

## 如何读本轮发现

先阅读evidence/batch-presence-report.md。关键限制是噪声下捕获不足和同锥身份混淆：前者不能只看少量新有效帧的低P95，后者不能只看在场时误差没有超过30°。同锥例子的在场≤10°正确率和不在场错误输出率能揭示单一门槛漏掉的问题。

本轮计划、连续输入、随机流与此前2700帧独立基线和SIM6-002三种子实验不同；不能把不同实验间数值变化解释为算法提升。原始算法与阈值未变。

下一步可以以本批次为冻结参照，另做候选或捕获规则改进，并用新种子检验；同锥身份问题需单独限定产品目标或增加可区分信息，不能靠减少捕获帧数解决。本轮无真实语音、实测RIR、硬件、音频增强或H3批准。仍由A复核完整版本并负责合入。
