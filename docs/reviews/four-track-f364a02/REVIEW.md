# A 独立复核：四路跟踪与三路离线音频

2026-09-16。结论：**通过限定复核**；未发现本次研究／诊断材料入库的阻断问题。不是目标存在门、定位精度、音频改善、默认算法替换、实时、定点、实板或完整 H2/H3 验收。

## 1. 固定版本与批准范围

- 作者分支：`task/member-b-four-track-01`。
- 实际直接查询并复核的远端 SHA：`f364a023830b105e6075d853da83cfd51127cf64`；不是按移动分支名批准。
- 合入前 main：`8371f014711e04553749e6c2ffc29f34b9d5ccc9`。
- 父跟踪提交 `e93169d526e9e94a98947c86d2c92bcab3c46a2e`、音频实现 `5d905b29c4f77c63b4d4a205b6a74a6ed7a48a91` 一并检查；最终 f364a02 补试听与审核说明。
- 相对 main 只有 `task-packages/PKG-B-ALG/tasks/four-channel-track-01/` 下 **95 个新增文件**。原 PHAT、Tracker、DAS、读取器、适配器、reference25、A/C 录音、旧复核及主流程状态页均未改。
- **只批准上述固定提交的 95 个文件及本目录 A 审核材料。** 不覆盖之后提交，不批准六麦性能或四路生产算法替换。
- 本地准确范围合并提交：`30770f6951a6cb2746a6c35acedb72e7e9e6ae50`。任务包与 f364a02 的差异检查退出 0；发布及真实共享目录核对另见本目录 `PUBLICATION.md`。

## 2. 环境与实际命令

独立检出：`E:/ss-four-track-review-0916`，首次在固定 f364a02 检查；随后在上述合并提交及相同最终任务路径重跑。未切换或重置脏共享目录，未访问或清理 B 日常 `F:/NUEC/develop`。

环境：CPython **3.12.14**、NumPy **2.3.5**、Windows 11 `10.0.26200`，AMD64 进程架构；未据此推断 CPU 厂商。无 AMD FFT DLL 依赖。

以下在仓库根运行，`$py` 实际是 `C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`。所有输出路径运行前均不存在。

```powershell
$p='task-packages/PKG-B-ALG/tasks/four-channel-track-01'
$a="$p/audio-01"
& $py -B "$a/verify_package.py"
& $py -B "$a/reproduce.py" --out E:/ss-four-track-review-0916-output/audio-run01
& $py -B "$a/verify_package.py" --compare-saved
& $py -B "$p/reproduce.py" --out E:/ss-four-track-review-0916-output/parent-run01
& $py -B "$p/verify.py" --compare E:/ss-four-track-review-0916-output/parent-run01/replay
```

以上全部退出 0。另执行本目录 `independent_check.py`，从 CSV 自行读整数码及编号、自行构造插值与淡化系数，再逐码核算；并将 A 新生成父包帧接到音频入口验证。旧实现的两个失败用例和四项拒绝覆盖用例为**预期失败**，不伪报为被测程序退出 0。

合并后实际完整记录入口：

```powershell
& $py -B docs/reviews/four-track-f364a02/record_run.py `
  --repo E:/ss-four-track-review-0916 `
  --out E:/ss-four-track-review-0916-output/merged-path-run01
```

该入口重新运行上述完整适用检查、独立核查及末次完整性验证，7 个阶段均退出 0。精确参数、时间、子命令与结果见 [evidence/commands.json](evidence/commands.json)、各子目录 `commands.json` 和日志；完整输出哈希／字节数见 [run-inventory.json](evidence/run-inventory.json)。今后复跑必须换新输出路径，不删除旧输出冒充首次运行。

## 3. 结果与重点逐项结论

| 检查 | A 实际结果与判断 |
| --- | --- |
| 完整性 | 父包原 28 个文件、本轮 66 个 manifest 条目及清单本身、26 个输入／依赖绑定、7 个原已测源码绑定、3 个试听文件绑定均通过。未改旧父包清单来隐藏新增音频目录。 |
| 测试 | 音频入口 21+21+8=50 项通过；父包 21+18+24=63 项通过。两者重复执行 21 项适配测试，合计 **92 个不重复测试用例**，不是 113 个独立测试。 |
| PCM | 两段各 31,984 样点、3 路×raw/preview，共 12 WAV、**383,808 个码值**，独立 CSV／`np.interp`／PCM24 解码重算全部 0 码差；无饱和。12 WAV 均与 B run02 字节一致。 |
| 同时钟与对齐 | 三路共同参考行 `[8,31992)`；center 原编号 17421～49404，quiet 17246～49229。mic0 保留原码；手动分支对应原获准手动 WAV 裁剪。所有分支 raw=1、preview=32，不分别归一化。 |
| 延迟符号 | 手动 +X 相对 mic0 正延迟 `[0,5.597667638484,5.597667638484,0]`；`x_i[n-d_i]` 符号一致。各候选最晚插值抽头不超过 `n+8`。8 样点只是统一离线可用性假设，不是整机延迟。 |
| 方向生效 | 帧末才可用，不回填该分析帧；center 首次 fresh 为相对录音起点 256 ms、参考行 12288；切换该行保持旧权重，12289 才首次有非零波束权重。不是“说话后 256 ms”实测响应。 |
| HOLD 与淡化 | 每个方向独立期限，HOLD 不刷新；480 样点凸组合，临期开始淡出；即使没有后续帧，过期方向权重仍归零。跨 clean interval 重置，不跨错误／缺样拼接；干净不足一帧尾段仍按旧期限逐样点处理。 |
| 修复前失败 | 在独立模块名下装载哈希绑定旧 mixer，运行当前两项临期换方向／释放用例，**2 项均如预期失败，权重跳变均 0.25**；当前 21 项音频测试通过。原失败日志、run01 和逆向恢复来源完整保留，未把恢复文件冒称当时保存快照。 |
| 防覆盖 | 对既有音频复现目录、渲染目录、audit JSON、父包复现目录的四次再运行均被拒绝（退出 1）；前后输出与整个作者任务包的哈希不变。 |
| 父包跟踪 | center 61 帧：SEARCH 14、ACQUIRE 8、LOCKED/fresh 21、HOLD 18，数值候选 36。quiet 61 帧全 SEARCH，但有 35 个数值一致且在扇区外的候选；并非目标存在门已有效拒绝背景。重叠帧不是独立样本或音频时长分母。 |
| 端到端增量 | 不仅使用作者冻结帧。把 A 独立复算的新父包帧送入音频接口，center 时延最大差 `8.881784197001252e-16` 样点，quiet 为 0，全部 WAV PCM 仍 0 码差。 |
| B 试听 | 3 个 center preview 哈希与试听记录一致；仅保留 B“无差别、无所列异常”的反馈。设备／固定音量／次数未知；A 未作主观试听，不将听感相近视为降噪改善。 |

## 4. 数值差异与文件字节差异

- 父包逐帧／摘要比较：**4,580 个浮点值、8,972 个离散值**；离散结果完全一致，浮点最大差 `2.842170943040401e-14`，通过原有 `atol=rtol=1e-10`。没有放宽阈值。
- A 的 center/quiet 帧 JSON 与 B 原件字节均不同；summary 也不同（含计算尾数、HEAD、运行时长等）。不能把它们写成字节一致。参见 `evidence/parent-comparison.log`。
- 音频：12 WAV、2 个混合 NPZ 均与 B run02 **字节相同**；独立分段系数重建最大差 0。
- 音频 `result.json` 字节不同。逐字段检查只见四个浮点尾数差（最大 `8.881784197001252e-16`）及 `source_sha256` 增列最终提交已有的 `verify_package.py`：`e1415993f5065f192a3f6fb816cfa0f3aa84723129863a2d371867ad60e7770f`。原七个源码哈希保持一致；不是录音或算法被改。其 `SHA256.json` 随之不同。
- 一次只读临时比较最初假设 JSON 全部键集合相等，因上述新增 verifier 哈希断言失败；随后核对新增键来源、所有原键及数值，未改作者数据／断言来“通过复现”。
- B 修复前后短实录本就没有覆盖临期切换边界；其 12 WAV 和 2 NPZ 相同，只能说明这些录音未受影响。真正证明边界修复的是保留的旧失败与当前回归，不是相同音频哈希。

## 5. 问题分级、限制与下一步

**阻断问题：无。需要 B 修改后才能入库的项目：无。** 以下保留为未验证／不得扩大批准的事项，不为本轮增加实验审批：

1. `tracking.py:61` 与父包 `README.md`：`target_presence=unknown`、`direction_accepted=false` 必须继续保留。需后续补目标存在门及背景／干扰误锁验证，才能讨论生产接入。
2. `audio-01/render_three.py:96` 的离线缓存波束和零计算耗时调度不是实时实现；22 路预计算不能充当 PL 缓存／吞吐／背压证据。完整固定点 DOA/DAS、连续流、资源时序和实板仍待验证。
3. 两段短实录无精确方向／语音活动真值；quiet 与 center 不是同场景配对噪声参考。不计算定位精度、错向率、SNR 改善或声学收益达标率。平面水平假设也不是三维方向恢复。
4. `audio-01/evidence/listening-01.json` 是 B 主观记录，与生成时冻结的 `listening_completed=false` 不矛盾；不回填冻结结果。本次没有确认改善，线性插值频率衰减、未标定与短时长仍限制结论。
5. 父包默认 `verify.py` 的全目录清单在 audio 子目录增加后不再是当前完整包入口；使用已核验的 `audio-01/verify_package.py`，比较新父包回放则用 `verify.py --compare`。不偷偷修改旧 manifest。

## 6. 集成与证据保全

批准入口保持任务包内 `four-channel-track-01/run.py` 和 `audio-01/reproduce.py`。它们是限定离线诊断入口，**暂不迁入活动生产模型或 RTL**；原因是目标存在门、完整链与实时证据缺失。达到新的整链批准条件后再单独集成，不由归档合并自动升级。

本目录保存独立审核脚本、命令、日志、数值记录与完整产物哈希。A 复跑 WAV/NPZ 与作者原件字节一致，仓库不再复制二进制；唯一版本由作者包 run02 加准确提交追溯。A 新生成、与作者字节不同的帧 JSON 和摘要已保存。外部初次／合并后复跑路径保留，不删除失败证据。

归档核对：清单中 47 项产物全部在本目录或已证明字节一致的作者 run02 找到，字节数／SHA-256 均匹配；38 项审核文件的暂存字节与磁盘一致。原始 Windows 日志／JSON 保留 CRLF，因此包含原始证据的全量 `git diff --check` 报空白提示；未格式化证据消除提示。审核源码、Markdown 与属性文件的范围内空白检查通过。

本次是包级限定批准，不是 9/16 新增正式阶段验收；不修改既有阶段快照、不派 C 新任务。主流程可在下一正式阶段汇总引用本记录。
