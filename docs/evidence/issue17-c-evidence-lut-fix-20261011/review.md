# 独立技术复核摘要

日期：2026-10-11。以下为协调者根据 `/root/ab_integration_review` 最终输出提供的概述，角色 `fpga_reviewer`；这是独立AI技术复核摘要，不是逐字原文、A/B成员签字或整机批准。

---

**Verdict: PASS WITH CONDITIONS。** 准许将准确候选作为单文件修复接入原 D 工程；结论限定为 C-EVID-LUT-001 的读字逻辑优化、有限仿真及隔离综合资源改善。

候选 SHA256 135271131d893eba2b8e22a7b596c78292de4050a69855f131b5fe5a582fdfd6；基线 d6b7096d55bdcc44ff275bdad2b208c25092ad6e9668aff4edcd83dcac76fc6a；run-manifest 38d77c4060188d6fe4481ef499f284c0ee6571cf685ea7b04fb0d4f0ee1b4e76。冻结索引内66项均匹配；D原源仍基线，用户未跟踪文件保持。

i17_vio_evidence.sv:107–135以外源字节相同。各记录LSW顺序、尾字补零、无效类型/索引返回零、X/Z守卫和诊断区0–63原始字读取语义保持；无新增状态、流水级、端口、时钟或复位变化。

独立shadow支持409600次位级oracle/旧函数比较、6656次公共READ、29178次检查和7772周期19输出差分。覆盖释放后读、短诊断留下旧字、未初始化字63和padding；四态测试为单地址位X/Z注入，非全部四态组合穷举。实际canary在sim_canary/xsim.log:92精确拒绝kind3/word17注入错误。

同选项OOC综合diagnostic_synth.log:340,621成功；synth_before/after/utilization.rpt:34–43：logic20546→6546,total20634→6634,LUTRAM88→88,FF+20,F7/F8+328/+56。无latch/blackbox。不能直接把差值从旧整机扣除作为fit证据。

C-EVID-LUT-SH-001 LOW：run_selftests.py:26只匹配任意Fatal: DATA_CHECK；报告声称还检查无完成标记，描述较runner严格；本次原件确为预期注入拒绝且无完成，未否定本次证据。要求更正描述，未来复用前核预定首错及完成标记。

C-IMPL-LUT-001既有HIGH：无新整机实现，保持OPEN，接入后人执行新综合/实现。

C-AB-CTRL-001既有HIGH：启动协议问题未在此文件修复，保持OPEN按原控制任务处理。

Disputed Findings无。shadow的INCONCLUSIVE针对完整功能验收，未否定本批有限仿真。新整机fit、布局布线时序及板测仍未验证。接入须精确字节，只替换指定单文件，核XPR/其他源保护项。单文件候选不需因范围外缺口重跑局部测试。本次未运行EDA、未改文件，不替A/B、整机功能或板级可用性背书。

---

## 接入后的事实（不属于上方复核摘要）

`WRITER-REPORT.md` 已按 `C-EVID-LUT-SH-001` 更正canary说明，runner/TB/RTL和测试原件未改。报告新SHA256为`2046b81c35035a7305b344ad896871ff4bec04ef61354811a5260c366c2d8cc5`；原run-manifest仍为`38d77c4060188d6fe4481ef499f284c0ee6571cf685ea7b04fb0d4f0ee1b4e76`。

已于2026-10-11 22:44（UTC+8）把准确候选`135271…582fdfd6`接回原D工程。99项前后校验中只有指定源变化，其余98项hash/mtime一致；无EDA/板操作。接入回执SHA256：`4c1ce453facc4623c95d666f099b622be1c2f66e90528c9318067f41f3dccdca`。本次发布资料随后获得用户“那有推送吗，带上说明”的授权。

本目录只携带必要原件；历史66项冻结索引中的本地工作资产未全部随本包发布。完整发布范围以本目录`publication-index.json`为准。大备份/DCP和vendor缓存不在本包内。
