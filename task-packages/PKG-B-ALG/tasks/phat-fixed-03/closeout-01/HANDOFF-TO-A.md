# 交 A：定点收口草稿包级复核

2026-09-11。作者B；指定复核人A；分支 `task/member-b-fixed-closeout-01`。请按本目录Git提交固定新增评审范围，连同固定上游 `bff45e7bbedab321fc4815e1432f1575c750edc4` 阅读。作者不自行合并；此文件是可转交评审入口，不代表A已经收到、审完或批准。稳定后一次包级复核，不要求逐次实验审批。

## 完整交付索引

所有相对路径从 `task-packages/PKG-B-ALG/tasks/` 起算，上游源文件版本均为bff45e7。

| 层次 | 源码/配置与golden | 已有验证与边界 |
|---|---|---|
| A原候选 | PKG-A-ACQ/tasks/fft-ip-budget-01（位于同级PKG-A包）；来源ac0ff38e954dac094fd84e28b329dcb24dded7fb | 原25位XSim/OOC/调度证据；非整机 |
| FFT位精确适配 | fft-bitexact-01/compare_cmodel.py；evidence/cmodel-run03 | 22528复样点、45056分量逐码零差；API标度与应用标度分开；CSV LF/CRLF字节不同 |
| 窗/补谱 | fft-window-02/window_model.py、run_vectors.py、check_simulation.py、source-snapshot | 输入窗/PCM码、C模型golden及XSim比较见该包evidence和RESULT.md；Python窗实现并非窗RTL |
| PHAT | phat-fixed-03/phat_model.py、validate.py、sources.json | F16失败/对照、F24开发及heldout记录见evidence；Decimal/Fraction独立算术对照，未RTL化 |
| 串接 | phat-fixed-03/integration/chain.py、validate_chain.py、protocol.json | run02的36个NPZ及frames/summary为golden；run01序列化失败保留；几何/LS仍浮点 |
| 动态范围 | phat-fixed-03/dynamic-range/scan.py、check_model.py、pack_evidence.py、protocol.json | run01含196个NPZ、frames.json.gz/packing.json/summary.json；analytic01为解析检查；非新RTL |
| 本轮收口 | phat-fixed-03/closeout-01/analyze.py、ANALYSIS.md、BUDGET.md | 归档哈希/整数数组/离散比较/分层复算及新增整数窗浮点对照；evidence/run01 |

固定上游来源、DLL和依赖SHA在原summary/sources记录；本轮verification.json验证7个直接研究源文件及196个NPZ。读取完整目录内原manifest，但不把本轮7源核验声称为全部338文件独立验证。未复制、重封或修改历史manifest/失败证据。

本轮快速复跑见README。需要重新执行供应商整链时，在仓库根目录使用新输出目录：

```powershell
$py='C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$dll='D:/AMD/2025.2/win64/tools/fft_v9_1/libIp_xfft_v9_1_bitacc_cmodel.dll'
$dep='D:/AMD/2025.2/win64/tools/fpo_v7_1'
$task='task-packages/PKG-B-ALG/tasks/phat-fixed-03'
& $py -B "$task/validate.py" --seed-offset 10000 --out "$task/evidence/reviewer-closeout01"
& $py -B "$task/integration/validate_chain.py" --dll $dll --dependency-dir $dep --out "$task/integration/evidence/reviewer-closeout01"
& $py -B "$task/dynamic-range/check_model.py" --dll $dll --dependency-dir $dep --out "$task/dynamic-range/evidence/reviewer-closeout-analytic01"
& $py -B "$task/dynamic-range/scan.py" --dll $dll --dependency-dir $dep --out "$task/dynamic-range/evidence/reviewer-closeout01"
& $py -B "$task/dynamic-range/pack_evidence.py" --directory "$task/dynamic-range/evidence/reviewer-closeout01"
```

这些是可复跑入口，本轮没有重跑这些历史扫描/RTL。FFT/窗口XSim准确构建及比较命令见各自README；各自合法安装AMD2025.2，不分发DLL/加密HDL。复核先固定归档输入：输入bytes不同需先定位；输入数值一致后再比每级整数码，随后掩码/有效性/峰/时延；不能用相同最终有效数代替逐码对照。

## 请求A包级检查及返回后待补

1. 核对本次误差分母、参考线标签、共同指数解释和缓存/调度假设。原25位保留，wide29是候选；组内时延/方向门限仍待确定。
2. 提供29位准确commit、IP参数（旋转因子/缩放/舍入/顺序）、新RTL与C模型逐码结果、overflow/AXI状态以及对应OOC资源/时序。这里全部**待验证**，不预填PASS。
3. 确定双IP或统一29位方案。统一29位IFFT尚无输入输出适配golden；双IP尚无实际调度/资源总和，不能套用原6DSP/3Tile/1.56ms。
4. B补PHAT/峰RTL实现及宽乘/开方/除法实际延迟，外部RAM端口/DMA/公共指数屏障预算；验证异常传播，特别IFFT真实异常/帧末错误与恢复。已有注入不等于硬件故障覆盖。
5. 后续在合适真实输入/标定与认可误差要求下选择幅值范围；四路实录登记由另一任务处理，本包不改其内容，不等待其到齐才交本草稿。跟踪、音频和整数几何仍待实现，不以浮点差异冒充真实方向精度。

## 发布与阶段收尾边界

本轮新增材料只有closeout-01目录。9/16可复现进展草稿已备齐，完整PKG-B-ALG/H3尚未验收，不提前承诺9/22必通过。没有新增获准源码可转活动目录，原因是本轮仍待A准确版本复核；A批准范围后由复核/主流程执行阶段归位、实际新位置测试和集中归档。保留原快照、工作树及其他未提交内容。

网络读取main先遇直连失败、受限环境代理Schannel凭据失败、OpenSSL尝试未成功，之后经授权代理fetch成功，未改全局Git配置。研究分析一次运行退出0，无本轮数值失败；旧DLL依赖加载、Vivado appinit和JSON序列化失败均仍在原包，本轮不删改。
