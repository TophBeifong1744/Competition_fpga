# 交 B 独立复核

本包由 A 实现并自检，尚未获得 B 独立复核。新任务分支 `codex/toph/fft29-bitexact-budget-01`；A 的准确交付 SHA 以交接消息及远端分支为准，不把父提交当本次交付。

请先读 `README.md`、`configuration.json`、`reuse-and-schedule.md`，再按 `REPRODUCE.md` 在独立输出目录复跑。固定被检 B 输入提交 `bff45e7bbedab321fc4815e1432f1575c750edc4`，不要换用已推进的分支 HEAD。

重点：

1. 本轮为 60/196 帧、360 个不同归档 FFT 加 1 个背压重复，只有 wide29；不是全部 784 次整链配置通过。
2. 直接读取 NPZ `windowed` 左移 4 位，对 `wide29_raw_fft` 逐实虚整数码比较；检查自然序、缩放、TLAST、溢出和实际 job 数。
3. 六通道公共右移目前只复算了软件模型，原 IFFT 仍 25 位；不能批准单 IP 混合位宽已经可用。
4. 区分 OOC 综合与 OOC 核布局布线。检查 100 MHz、part、8 DSP、3 BRAM Tile、LUT/FF 和 WNS；留意缺少系统 I/O 延迟与实际时钟源、PS7 的边界。
5. 重新比较单变换与六 FFT 预算；不要沿用旧约 1.56 ms 作为完整新链结论。资源表未含适配缓存、PHAT、IFFT、PS/DDR 或采集链。
6. B README 的旧 HEAD 说明与缺少 `run01-console.log` 已单独列为交付问题，不擅自改原件。失败下载记录及 A 辅助审计脚本的已修正错误均保留。

请复核后另写绑定准确 A SHA 的结论、允许合入范围和限制。可批准范围仅候选 FFT 实现/预算研究材料；不默认替换算法、不冻结数制、不扩大到完整定点链、四麦实录、音频、实板或 H2/H3。作者 A 本次不自行合入 main。
