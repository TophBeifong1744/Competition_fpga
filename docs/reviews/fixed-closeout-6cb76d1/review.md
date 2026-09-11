# A 包级复核：B 定点误差与预算收口草稿

2026-09-11；复核人 A。**通过限定研究材料复核**：数据、分层统计及草案主要结论可复现；无阻断本次研究归档的问题。保留 reference25，不冻结数制或应用误差限。两项非阻断说明及已有 29 位证据补充如下。

## 1. 准确输入与隔离

- 远端 `task/member-b-fixed-closeout-01` 实际 head：`6cb76d11615b3f58e8350767a86479946fc34133`。
- 固定研究基线：`bff45e7bbedab321fc4815e1432f1575c750edc4`。
- 本次差异严格为 `task-packages/PKG-B-ALG/tasks/phat-fixed-03/closeout-01/` 的 17 个新增文件；未修改上游 manifest、FFT/PHAT 默认代码、四路接收入口或 A/C 文件。
- A 独立 detached worktree：`E:/ss-fixed-closeout-review-01`，HEAD 为上述准确 SHA；全部运行后仍干净，17 项文件运行前后哈希未变。
- 最新主线规则读取于 `48a981733f4bf5bb1231d2ca42a705f593e02e7b` 的 AGENTS.md、docs/phase-closeout.md、docs/phases/2026-09-11-to-09-16/B.md。研究基线没有这些新文件，不为补规则混入 main；共享工作区和 B 工作区均未切换/重置。
- 本机使用 A 的 Python 3.12.14 / NumPy 2.3.5，未使用本机不存在的 BryanZheng 路径。

## 2. 实际命令与结果

在独立仓库根目录，先运行完整性检查，再输出到包外的新目录：

```powershell
$py='C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $py -B task-packages/PKG-B-ALG/tasks/phat-fixed-03/closeout-01/verify_delivery.py
& $py -B task-packages/PKG-B-ALG/tasks/phat-fixed-03/closeout-01/analyze.py --out 'E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/docs/reviews/fixed-closeout-6cb76d1/run01/analysis'
```

两条均退出 0。第一条核验 16 个清单文件（另加 manifest 本身共 17 个）、12 个本地链接、源码和输出哈希；第二条得到 `Verified 196 NPZ / 11760 candidate pairs / 96 archived amplitude groups`。

由本目录 `run_review.py --mode fixed` 实际调用上述命令；完整 cwd/解释器/参数/时刻/退出码见 `run01/commands.json`，stdout/stderr 原件同目录保存。输出目录事先不存在，未向 closeout-01 增加任何文件。仅重新分析归档，不生成新场景，不重跑供应商模型或全部历史研究。

另执行 A 自编、**不导入 B analyze/chain** 的交叉核验：

```powershell
& $py -B docs/reviews/fixed-closeout-6cb76d1/independent_checks.py --repo E:/ss-fixed-closeout-review-01 --analysis 'E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/docs/reviews/fixed-closeout-6cb76d1/run01/analysis' --out 'E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/docs/reviews/fixed-closeout-6cb76d1/independent01'
```

退出 0；结果见 `independent01/independent.json`。`git diff --check bff45e7 6cb76d1` 退出 0。两台作者/复核机器环境相同版本不等于独立算法证据；本轮用另写的整数舍入、掩码、峰和统计代码交叉验证。

## 3. 核验结果

| 层次 | 实际检查及结论 |
| --- | --- |
| 压缩归档字节 | 1,679,402 字节，SHA-256 `ef514321c591196260f281f5504becc0c965ad43019e188ae4c735ff6e80faa1`；解压 219,818,744 字节，SHA-256 `8ca204725f6fb802fd9b2add8eeb74f245cffb4c3b44327e210a289acc409efa`，均匹配 |
| 输入/来源 | 196 个 NPZ 的 SHA 全匹配；case 0..195 唯一齐全，192 个幅值帧与协议笛卡尔积一致，4 个压力帧另列；B 分析入口验证 7 个直接依赖源码哈希；未声称整个上游包均获独立验收 |
| 整数数组 | 独立验证 PCM+整数窗 2,408,448 个分量、packing 9,633,792 个分量；使用有符号整数最近偶数舍入，检查 S25 范围与公共右移最小性 |
| 离散结果 | 用 packed FFT 重算整数平方阈值掩码；从归档 IFFT 实相关独立重算峰、Q12 和时延有效性，保留整帧 overflow 拒绝；掩码、峰、整数时延及有效标志全一致 |
| 浮点对照 | 从同一 NPZ 的原输入、PCM、整数窗重新计算浮点相关，不重生成声源；原输入/PCM 浮点掩码、峰、有效性一致，时延差容差 1e-12 采样内 |
| 分层统计 | 11,760 对配置结果、96 幅值汇总、1,248 个边际/联合分层全部重算；8 帧/120 对的分母和共享通道/波形依赖说明正确；线性 P95/P99 独立实现与报告一致 |
| 失效处理 | 仅双方有效计算误差和峰变化；空集合保持 null/空，不把失效填零；跟踪失效、新增有效及总数，不用较少幸存样本的 max 下降宣称恢复 |
| 尾部与研究线 | 前 30 个尾部的 case/candidate/pair/delta 完全一致；最坏 case186、shift6_early、pair2，3.105176727729989 采样；研究线从 2^-1 连续前缀计算，不跳坏档 |
| 输出容器与值 | 9 个复跑 JSON/CSV **本轮实际全部字节相同**，解析值亦相同；各项 SHA 见 independent.json。未预设跨机必须字节相同，也未用哈希相同代替整数/统计独立复算 |

限制：没有重新执行 PHAT 归一化算术及供应商 IFFT；对这些层检查源码、哈希和归档数组的后续关系，不把本次数组审计宣称完整定点逐码链或新 RTL 仿真。

## 4. 误差与预算判断

- `ANALYSIS.md:19`：wide29 / 2^-20 为 120/120 对有效；median 0.1262737956、P95 **0.4771063002**、P99 0.8223754015、max **0.8796478522** 采样；26 对整数峰变化，68 对大于 0.1、6 对大于 0.5。noise0 场景贡献本档尾部。均为相对未量化浮点链的差，**不是相对真实 TDOA 的误差**。
- `ANALYSIS.md:51,60,62`：PCM/窗/后端对照区分正确；wide29_vs_window 包含 FFT、PHAT、IFFT 和 Q12，不能全归 FFT，更不能相加各级最大值/分位数。2^-22 与 2^-23 的整数窗浮点均有 120 对达到频点数条件，但最终均仅 **119/120** 有效；2^-24 PCM 为零，后级不能恢复。
- `ANALYSIS.md:35` 起的研究线是事后描述，未获组内应用门限批准。暂保留 reference25 的决定合理；wide29 不是低幅度精度保证，不据本包替换默认算法。
- 两个 shift6 候选在 DC/交替/900 Hz 的三个压力帧分别有 6 通道溢出并拒绝全部麦对。不能选其较低幅度档表现而忽略强信号失效。
- `BUDGET.md:9–23` 的格式和保守宽度与源码相符：S24 PCM、U18F17 Hann、S29F27 前向、公共 r 回 S25、后端仍 S25 IFFT；epsilon 是带缩放的有理数，本批 <1 才允许原显式零/非零分支。PCM 削顶当前只计数，尚无整帧接受策略。
- 每帧 6 FFT + 至多 15 IFFT；6144 窗乘、7695 个当前互谱频点、30780 实乘；带内 1185 点/4740 实乘只是未实现优化。峰搜索 207 点/192 次比较，缓存槽合计 **165713 B**，独立复算相符。
- 缓存未含 IP 内 RAM、FIFO、宽算术状态、DMA/系统缓存等，不能直接换算成整链 BRAM。公共指数需要屏障与重读，不免费；75 轮开方模型不等于 PHAT 总周期。25 位 6 DSP / 3 Tile / 约 1.56 ms 仅保留原候选引用，未套用到 29 位或整链。

## 5. 按严重程度列发现

**阻断本次研究归档的问题：无。**

1. **[非阻断／合入限制] 运行依赖尚未入 main。** `README.md:5` 和 `analyze.py:14` 绑定上游 bff45e7；该上游相对本轮 main 有 360 个文件差异，FFT 位精确、窗及 PHAT/integration/dynamic-range 不在 main。本轮不能据 17 文件审核批准那 360 文件；仅允许研究快照归档。main 直接运行 analyze 并非已验证工作流，应在固定 **6cb76d1 的独立 worktree** 中复现。活动入口集成留待上游完整包审核，不构造缺依赖的活动算法入口。
2. **[P3／文字澄清] `ANALYSIS.md:72` 的“交替帧又均接受15对”缺少主语。** case194 实际是浮点、PCM 浮点、reference25、wide29 各 15 对有效；shift6_late/early 各 0 对且 6 路 overflow。不能理解成四候选全部接受。本审核补充给出准确解释，原证据不改；B 下轮或引用报告时应写明上述对象。该段前文和归档对溢出拒绝均正确，不改变本轮数值结论。
3. **[P3／来源更新] `BUDGET.md:81,84` 的“29位项全部待A”是作者交付时点状态。** 现在已有下节证据，可以作为新研究输入；不能把该更新升级成 B 独立批准 A 的 29 位交付或整链批准。

需阻断后重交的修改项：无。文字澄清以本审核为准；应用报告应采用澄清后的明确对象。未覆写作者 17 个文件或旧 manifest。

## 6. 补交给 B 的 29 位 A 证据

准确远端提交：**`c0b5f8fb44643e81d8c4e6f0be457dddeae9758e`**，分支 `codex/toph/fft29-bitexact-budget-01`，目录 `task-packages/PKG-A-ACQ/tasks/fft29-bitexact-budget-01/`。该 A 作者交付仍待 B 独立复核，本次不自行批准/合入它。

本轮实际执行该包 `source/package_manifest.py check`、`source/check_resources.py`、`source/check.py`，均 `-B`、退出 0；输出到本审核 `fft29-reference01/`，完整命令和保存结果在那里。仅重新核对已有归档整数输出/资源转录，**未启动新的 Vivado/C 模型运行**。检查前后该工作树干净，没有修改 A 原件。

| 项目 | 已有证据与本轮核对 |
| --- | --- |
| 配置 | Vivado/XSim 2025.2 build6299465；FFT9.1 rev15；xc7z020clg400-2；100 MHz；N1024 Radix-2 Burst、实虚29、twiddle24、convergent、natural、nonrealtime；前向0x0AAAAB、十级各右移1 |
| 输入标度 | B NPZ 窗码精确左移4；应用F27，C API 除2^28；输出先逐 raw 整数码比较，不能先缩回S25掩盖差异 |
| 逐码 | 60/196帧×6=360个唯一前向变换，加1个背压重复；361次、369664复数输出、739328实虚码，0不一致，最大码差0；overflow均0；对应已保存C模型归档，未重新运行DLL |
| 覆盖限制 | 仅wide29，56个幅值帧+4压力帧；另136帧无此项RTL覆盖；不含全部784整链配置。不能用前向零差消除2^-20的下游时延差 |
| OOC综合 | 1195 LUT、2043 FF、8 DSP、6 RAMB18=3 Tile；WNS+6.940 ns、WHS+0.190 ns |
| OOC核布局布线 | 1045 LUT、2046 FF、8 DSP、3 Tile；WNS+5.248 ns、WHS+0.037 ns；TNS/THS0，2701网络全布通 |
| 周期 | 常规配置握手到最后输出7361周期；服务槽7366；六FFT预留44196周期=0.44196ms；背压重复7599周期 |
| 时序边界 | 85输入/88输出缺系统I/O delay，无实际HD.CLK_SRC/PS7顶层；ZPS7-1警告及6项AVAL-4建议仍在。不构成整板时序或板测通过 |

对 B 的逐项意见：可将上述准确版本和“作者实现、归档复查、待B独立复核”状态补入候选表；29位单核 DSP 应用8而非6。双核概念性资源至少是前向29位核加原25位IFFT核及适配/外部RAM，不能只引用前向核。统一29位IFFT没有新golden/合同，不能称单IP混合位宽已解决；这里不冻结架构。公共最小右移只软件复算，RTL、端口/屏障、全链调度、异常晚到处理、真实幅值与认可误差线继续待验证。

## 7. 可批准范围、合入与收尾

仅批准准确 6cb76d1 相对 bff45e7 的 **17 个 closeout-01 文件作为六麦合成离线研究材料归档**，附 A 本目录审核证据。允许由复核人从当前 main 建隔离发布分支，仅应用该提交的17文件增量，**不 merge 整个上游待审分支**。

不批准：bff45e7 全包、A29交付本身、默认算法替换、配置/数制/误差门限冻结、活动算法接入、完整定点链、四路实录诊断、M1/H2/H3、资源/时序/实板或整机验收。

原包9个复跑输出与作者证据字节一致，为避免重复归档，发布保存命令、前后哈希和独立统计，完整本机复跑输出仍保留在 run01/analysis。未来重跑须新路径，不覆盖它。审核源码支持从固定提交再生成。

按阶段规则执行本项**研究归档处置**，详见 CLOSEOUT.md；没有本次获准可接入实时系统的源码，不搬入 rtl/tb/sim/model。9/16仍是可复现进展检查；完整包/H3按9/22及成熟度评审。该包级结论不签发9/16阶段验收，不改阶段公共页或已冻结快照。
