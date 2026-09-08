# 允许方向范围与跟踪状态：操作说明

阶段说明：后续多种子整批对照和目标存在标注已完成，见同目录batch-presence-evaluation.md；本文保留跟踪接入阶段的操作说明和当时结果。

开发版本 sector-tracking-entry-0.1；属于 B 的 H1 后、H3 前离线软件开发。链路为六麦连续合成输入 → 分帧 → 原六麦定位基线 → 方向范围筛选 → 跟踪状态。没有硬件验收或完整包审批。

## 已接入的选择规则

沿用用户选择：先指定允许方向范围，再锁定其中的稳定声源方向。范围是三维圆锥，默认中心 [1,0,0] 即正前方，半角 30°，含边界；不是方位和俯仰分别 ±30° 的矩形。

配置文件为 `payload/config/sector-tracking.json`，含七个字段：

| 配置 | 默认值 | 含义 |
|---|---|---|
| cone_center | [1,0,0] | 范围中心，输入非零向量后归一化 |
| cone_half_angle_deg | 30 | 候选方向与中心的三维夹角上限 |
| acquire_frames | 5 | 连续合格帧数，足够后才锁定 |
| acquire_spread_deg | 8 | 捕获窗口中任意两候选的夹角上限 |
| track_step_deg | 20 | 锁定后新候选与上次新有效方向的夹角上限 |
| hold_ms | 200 | 自最后新有效输出起，旧方向允许保持显示的时长 |
| max_input_gap_ms | 30 | 相邻输入超过这个时间间隔则清空旧状态 |

所有参数继承旧 SIM6-002-01 实验。旧 tracker.py 按字节复制为 `sector_tracker.py`；原策略、报告、测试及哈希保留在 reference/sector-lock-v0.1/。入口额外校验配置类型、拒绝布尔数值和未知/缺失字段，没有调整旧跟踪算法或阈值。旧实验仍作为历史证据，不单独等待审批。

## 先运行稳定声源

```powershell
cd F:\NUEC\task-packages\PKG-B-ALG
& 'C:\Users\BryanZheng\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B payload/model/python/six_mic_track.py --demo stable --config payload/config/sector-tracking.json --out evidence/my-tracking-stable-01
```

每次使用尚不存在的输出目录。默认示例目标在正前方，使用一整段连续的六麦浮点合成信号；不把旧模型的独立试验拼成连续输入。原 1024/512 分帧和 GCC/LS 定位代码没有修改。

输出包括 input/ 下的 NPY 和元数据、frames.json、summary.json、tracking-config.json、run.json。共有 89 帧；前 4 帧 ACQUIRE，第 5 帧（索引 4）LOCKED。第五帧可用时间为 64 ms，之后共有 85 帧新有效输出。这是采样时间，不是程序运行耗时，也不是实测系统延迟。从第一候选可用到第五候选可用的间隔约 42.667 ms。

## 查看每帧输出

frames.json 的每项包含两个对象：

- `baseline`：原定位输出，完整保留原有效标志、方向、时差和拒绝原因。
- `tracking`：后处理输出，包含 state、fresh_valid、direction、display_direction、stale、reason、acquire_count、last_fresh_ms、display_expires_at_ms、timestamp_ms、input_reset、angular_error_deg。

| 状态 | 含义 | 能否提供新有效方向 |
|---|---|---|
| SEARCH | 尚无合格候选，或已释放 | 否 |
| ACQUIRE | 正在积累连续稳定候选 | 否 |
| LOCKED | 捕获成功或本帧通过更新门 | 是，fresh_valid=true |
| HOLD | 本帧被拒绝，短暂保留上次方向显示 | 否，fresh_valid=false，stale=true |

`direction` 仅在 fresh_valid=true 时提供。HOLD 的旧向量只出现在 display_direction，禁止拿它填补新输出或计算有效率。SEARCH/ACQUIRE 两个方向均为空。没有独立的 HOLD 精度指标；如果提供固定真值，angular_error_deg 只计算新有效方向的三维误差。

超过 200 ms 才释放，恰好到期的边界仍沿用旧策略允许显示。若流停止，后续没有 update，界面必须自行按 display_expires_at_ms 撤销过期显示；本轮是离线程序，不实现 UI 定时器。输入中断超过 30 ms 的重置优先于 HOLD。

summary.json 分别有 baseline 与 tracking 两组统计。tracking.valid_frames/valid_rate 只数 fresh_valid；rejected_frames 表示本帧没有新有效输出，包含正在捕获和 HOLD，不一定是原算法拒绝。tracking.reason_counts 记录所有跟踪结果原因；通用统计中的空 rejection_reason_counts 不用于跟踪原因计数。有效但误差 >30° 的错误率分别以全部帧和新有效帧为分母；没有真值时误差为 null。不要只看错误数为零而忽略新有效率也为零。

## 检查丢失和恢复

```powershell
& 'C:\Users\BryanZheng\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B payload/model/python/six_mic_track.py --demo drop-return --config payload/config/sector-tracking.json --out evidence/my-tracking-return-01
```

这个教学输入在中间一段将六通道同时静音，模拟候选丢失，不模拟真实房间声衰减。预期先锁定、进入 HOLD、超过期限释放，再用完整五帧重新捕获。实跑首次锁定时间 64 ms，第二次 640 ms；有 18 帧 HOLD，这些都不计为新有效方向。

该段存在目标不发声时间，未提供覆盖整段的固定真值，因此本例不输出角度准确率，也不声称计算了“目标不在场时误输出率”。逐帧目标存在标签与相应评价仍待后续整批实验补齐。

另外可选择 --demo outside、band_noise0、interferer0；分别检查范围外稳定声源、同频带独立噪声和等强竞争声源。它们是新的单种子教学输入，不替代旧 SIM6-001/SIM6-002 的整体性能证据。对称正前方的理想示例误差可能为零，不能推论真实阵列精度。

之前六麦定位 clean 示例只有两帧，而且默认方向 35°/25°在当前正前方 30°圆锥之外；它无法展示五帧捕获。此处专门使用长的正前方 stable 示例，不放宽条件。

## 设置其他允许方向

复制配置文件到你自己的文件，再修改 cone_center。例如 [0,1,0] 表示正左，半角不变；然后用 --config 指定新文件。三个轴的约定为 x 前、y 左、z 上。一般方位 a、俯仰 e 对应 [cos(e)cos(a), cos(e)sin(a), sin(e)]，三角函数使用弧度。

命令行每次运行读取一次配置，不监听文件变化。省略 --config 时使用相同默认值。tracking-config.json 保存实际参数，run.json 保存归一化中心与配置文件哈希。只有三维范围和稳定性规则，没有说话人身份选择。

可以用同一输入重放：

```powershell
& 'C:\Users\BryanZheng\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B payload/model/python/six_mic_track.py --input evidence/my-tracking-stable-01/input --config payload/config/sector-tracking.json --out evidence/my-tracking-replay-01
```

同输入、同配置、同代码和运行环境下，四个结果 JSON 按字节一致，回归测试已经验证。处理完成退出码为 0，即使没有任何锁定；输入错误退出 2。结果目录拒绝覆盖，执行失败留下的部分文件不代表完成。

## 程序接口及状态边界

`run_tracking(segment, truth=None, config=Config())` 返回逐帧结果与两组统计，每个独立输入段新建一个会话，时间不跨文件拼接。跟踪实际只接收原定位的 unit_vector、valid 和帧时间，真值仅供输出后的评价，范围外声源及场景标签均不参与状态决策。

时间取 `end_seconds_exclusive * 1000`，表示帧全部采样可用的时刻，以该段首个样本为零点。`reset_before=true` 会先释放旧状态再处理当前帧，无需等待超过 30 ms；适用于分帧器标记的有效区间边界。独立段的时间重启由新会话处理，不能复用旧会话的时钟。

`TrackingSession.update(baseline_row)` 可逐帧接入；`release()` 人工释放；`configure(Config(...))` 更改配置并释放，随后重新积累五帧。两者保留当前段的时钟单调约束。无效配置或倒退时间在修改状态前拒绝。该接口接收可信的本包定位行，不是任意外部 JSON 的通用加载器。

## 当前验证与限制

128 项回归通过，包括历史 18 项跟踪规则、500 次更新的新旧同结果对照、范围边界、极点/方位跨界、配置改变、人工释放、中断重置、HOLD 过期及连续声学接入。当前基线源码、读取器、分帧器均保持不变。

本轮低信噪比和等强竞争教学例子均没有捕获，保留零输出结果；没有调整条件来提高表面有效率。同锥内另一个稳定声源仍可能被接受，系统不能仅凭方向判断它是不是你想跟踪的人。旧实验对此的失败证据仍保留在 reference/sector-lock-v0.1/REPORT.md。

下一步在同一 PKG-B-ALG 做多种子整批对照和目标存在标注，再根据证据决定是否改进候选/捕获方法；音频增强与定点准备仍待开发。完整包交 A 复核，由 A 明确通过后合入总工程。
