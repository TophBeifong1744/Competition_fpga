# H3 工程收口增量：一页入口

**2026-09-21 最新批准：A已关闭R1/R2，准确实现ad30bda获限定离线软件材料批准并合入main。** 见 [A正式报告](../../../../../docs/reviews/b-engineering-ad30bda/REVIEW.md)。合并a78f81b，发布/报告e4ac088；43项回归、A新增14项邻接及合后检查均通过，本轮不重复运行。活动入口仍为本任务包，生产/AMD/RTL/实时及完整H3未批准，REALTIME_BLOCKED保持。下面NEEDS_FIX/待审措辞为原交付时点，已由本条覆盖；未审尾部文档保留任务分支，不自动并入main。

**2026-09-21 A复核后覆盖：原整包为NEEDS_FIX，R1/R2已完成作者返修、待A增量复核。** 当前入口改用 [返修说明与43项增量检查](repair-r1-r2/README.md)。A原报告逐字节保存在该子目录；没有自行将返修标成独立批准。下文run05及旧复现命令保留为d3d2a3d历史，数值/预算不重跑。旧 `check_delivery.py` 绑定旧checker哈希，不能用于新checker；新入口 `repair-r1-r2/run_repair.py` 同时检查旧证据原字节与新源码。

实际2026-09-21，沿既有 `h3-interface-review-20260918` 包新增本子目录。作者B完成软件增量和证据整理，**待A独立复核，未自审自合main**。没有修改A/C原件、声学研究、旧冻结材料、默认算法、阈值或主流程状态文件。

本轮完成：[准确合同表](CONTRACT.md)、[动态/数据流语义](FLOW.md)、[完整服务与内存账本](BUDGET.md)、可运行小向量CORDIC候选、轨迹检查器及异常夹具。已有R1/R2、集中整理、B1–B6、f879/a7f70c5 E01～03、268e526动态批准都复用原报告，不重实现或复核。最新main核对/提交身份见 [交付记录](DELIVERY.md)。

## 复现与结果

仓库根运行，CPython3.12.14 / NumPy2.3.5。系统默认Python3.7不适用；本机解释器为 `C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`。输出目录必须不存在。

```powershell
python -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/engineering-closeout-20260921/run_all.py --repo . --out ../h3-engineering-new
```

最终运行入口为 `evidence/run05/runner.json`（逐阶段命令、cwd、源码哈希、真实退出码）；结果 `checks/result.json`，原失败向量 `checks/original-cordic-counterexamples.json`，配置为本目录 `budget_config.json`，预算输出为 `budget.json`，完整日志 `stage-*.log`，结果封存 `OUTPUT-SHA256.json`。首次run01及中间run02保留，不累计测试数量。

新验证：1215 CORDIC向量，候选圆周误差≤1 Q8码，实际最大约0.508码；原942个超界反例保留，最大2530码（9.8828125°）。这些是通用小向量测试，不能写成当前经过模长门的DOA已出现对应误差。候选拒绝6非法输入；162 RNE及6饱和边界；动态S24极端32输出与Fraction参考；14种轨迹变异均拒绝，正常/late-reset/背压取消通过。最终以result.json实测为准。

软件自测不是独立验收。FFT/IFFT整变换调用0；AMD、RTL、Vivado/Vitis、综合/实现、板测0；只读检查PATH未找到xsim/vivado/iverilog，不宣称全机没有工具。未测清单/集中下一动作如下，实际one从未操作。

## 缺项、负责人及预计时间

时间是本轮工作量估计，需责任人接单/工具可用后起算，不代替承诺。

| 项目 | 本轮状态 | 负责人/预计 |
|---|---|---|
| B新候选独立审 | 完整离线增量已交；不默认接入 | A优先1个工作日内结果或预计时间 |
| profile/动态策略/时基集中选择 | 已列候选与代价，未双方冻结 | A裁决+B确认，预计一次0.5工作日；明确原/归一化CORDIC及20ms策略是否接受 |
| AMD逐级golden | 旧分支证据分列；新分支未运行 | A导出准确IP/profile，B比对，输入齐后约1工作日；全域误差另估 |
| 生产事务/PS C/RTL/CDC | 模型限定批准保持；生产NOT_RUN | A工程实现，9/23检查点给实际进度；完整工期由A按工程选择估计 |
| 内存/有界服务/输出 | 全项列账但Ttotal=null，REALTIME_BLOCKED | A地址/端口/服务证据；齐后B约0.5工作日重算。无上界则不能承诺实时完成日期 |
| 声学基线/真值/音频收益 | 本轮未涉及，完整H3仍未关闭 | 另一声学对话；本包不派新录音、不追加其交期 |

本轮可独立工作已完成，不以等A为由停止于计划。9.18遗留交付为合同/golden准备/异常/预算资料；9.23工作才是实际RTL、PS及工程映射。二者验收边界分开。

## 用户执行的一整阶段操作单（准备材料，不立即要求操作）

仓库AGENTS的“2026-09-15 Vivado/Vitis操作分工”要求用户选择原one/副本并执行实际工程修改。本轮尚无具体生产profile批准，因此没有创建/修改工程，也不让用户现在逐点击等待。

1. A/B完成上表集中选择后，A一次列出确切XCI/wrapper、ROM哈希、模块端口、工程文件与预期变化；用户选择复用one还是新副本，Vitis同样选择平台/应用。该选择之前不执行工程修改。
2. 用户按A完整变更清单导入/修改RTL、BD、XDC/IP与PS源码/链接区间，确认FFT29和IFFT25静态宽度、配置字/状态端口、epoch及输出full策略；固定工程与配置哈希。不要把软件Q30 ROM当AMD24 golden。
3. Codex负责测试平台/仿真：复用原IP逐码scoreboard，先验证样点数/index/TLAST/status，再导出本包轨迹schema；真实完成集合/时钟/最大stall来自已决定合同，不使用本包两unit示例冒充14事务。异常包括末拍背压、晚status、reset/STOP、旧epoch回调与输出full。
4. 用户执行综合/实现/bitstream，Vitis构建/下载/运行；A/B只读核对同版本资源、时序、地址/所有权和最坏服务报告。时序失败或服务无界保留REALTIME_BLOCKED。
5. 仅在版本/准入齐全后执行相应板测，保存真实日志，分开报告功能仿真、实现、实板。无需为本离线包重新采录或重跑历史FFT/耐久。

给A的可复制请求见 [A-REVIEW-PROMPT](A-REVIEW-PROMPT.md)。目标活动位置仍是本任务包候选目录；不自动迁入生产库。
