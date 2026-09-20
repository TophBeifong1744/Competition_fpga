# 输入、状态与结果接口草案

本页是B提交A裁决的合同提案。已有H1格式/离线分帧语义可引用；PS/PL传输ABI、寄存器和握手实现未开发，以下提案不宣称已在硬件运行。

## 输入与异常规则

每组8个little-endian uint32字：id_lo,id_hi,mic0..3,flags,reserved。ID按uint64保留，JSON表示为十进制字符串以避免JavaScript丢精度。PCM按signed int32解释并验证signed24范围。raw flags[3:0]保留各路clip，其他位/reserved非零拒绝；H1当前将clip映射stream_error=1/error_flags=unknown，同时保留raw。

| 条件 | 已有行为及本提案 |
| --- | --- |
| clip | 原采集PS只统计，不自动失败；H1导出把该行作错误行，分帧不得跨该行。实时提案：含clip帧不发布fresh方向、错误原因/原位图保留；不静默限幅后当正常 |
| 丢ID/错误行 | H1缺号首行带drop且为错误行，不补样；清除跨界重叠，从下一clean interval独立起帧，首帧reset_before=true；重复/倒序ID拒绝 |
| DMA/guard/PL overflow/sync故障 | 采集fail-stop证据复用；当前会话不继续发布正常帧，旧未提交结果作废。缓存满不得覆写消费者拥有帧，须报显式QUEUE_OVERFLOW并进入同等断流恢复；实际实现待定 |
| 停止/重启 | 停止排空包，保留原尾部但不足1024不生帧；新Run新session，纵使ID相邻也不能拼接，清跟踪/TTL/重叠 |
| 无目标/低能量 | 无可信目标存在结论时target_presence=unknown；候选能量门失败表示LOW_ENERGY，不等于证明无目标。正式direction_accepted=false。允许research_candidate另栏记录数值 |
| 算术/IP/晚到状态错误 | frame_invalid；不得先提交有效方向后吞掉overflow/TLAST/status故障。当前golden饱和计数不等于硬件检测完成 |

存在门现状：rms>=2048、peak>=4096，至少3路，stream_error/clip拒绝；center和quiet各61/61通过，因此不能准入正式存在判定。fresh=0可能只是扇区/跟踪拒绝，不能算无目标识别成功。

## 握手与所有权提案

- 接收组以valid&&ready为唯一推进条件；背压期间payload/ID/flags/sideband稳定。采样源不能随ready暂停，无界背压不可接受。
- 帧描述符带session_id、interval_id、frame_id、first/last uint64原ID、row_start/stop、reset_before、N/H、channel_order、config_id、错误位图、数值profile_id。四路通道标识随数据走，禁止借用六麦矩阵。
- FFT输入一个事务含1024个复数样点，TLAST只在第1024个**被接受**样点；DMA第250组包尾不是FFT帧尾。配置握手成功后才发该事务；输出数据数目、索引、TLAST与最终status都验齐。
- 帧状态：ASSEMBLING→READY→PROCESSING→WAIT_STATUS→COMMITTED，任一故障→INVALID；ERROR/RESET可从任意未提交态终止。COMMITTED之前不向上层发布有效方向；每帧结果唯一。
- 帧数据FREE→FILLING→READY→IN_USE→FREE；ready/valid等待不改变数据。RX槽CPU_OWNED时复制到算法拥有缓存，复制完才FREE；不得保留FREE槽指针。
- 队列满、停声/停止、reset与DMA错误的优先级和硬件同步必须在适配器实现中验证。本包只提供无实时背压的离线包/槽golden，尚不能证明ready稳定/队列溢出响应。
- 若61.44MHz采集接100MHz算法PL，使用带元数据的CDC队列/复位协议；本包未实现CDC。

## 结果输出包提案（逻辑JSON，不是已冻结线缆ABI）

每个已分析帧产生一个结果，即使INVALID也给原因；不足一帧的尾部产生独立interval_end摘要。字段：

```json
{
  "schema": "h3-result-proposal-0.1",
  "session_id": "run-id", "interval_id": 0, "frame_id": 0,
  "first_sample_id": "17246", "last_sample_id": "18269",
  "config_id": "exact-contract-hash", "numeric_profile": "candidate-only",
  "frame_status": "INVALID", "error_reasons": ["NOT_VALIDATED"],
  "target_presence": "unknown", "direction_accepted": false,
  "fresh_valid": false, "angle_q8_deg": null,
  "held_angle_q8_deg": null, "valid_through_sample": null,
  "available_sample": null, "processing_cycles": null,
  "overflow_count": 0, "clip_mask": 0,
  "research_candidate": null
}
```

angle仅fresh时非null；HOLD另给held_angle，不能混充新测量。TTL以当前session原样点时间线计，session结束即失效；结果到达晚于TTL则拒绝使用。run05的gap_reset事件清旧TTL、切单麦目标并480样点淡变，属于已复核软件控制规则；8样点可用延迟是假设，非实测。

字段宽度/字节序/CRC/版本协商/吞吐、方向分发和板端音频输出介质仍待A+B共同冻结；没有接DAC或承诺实时包周期。
