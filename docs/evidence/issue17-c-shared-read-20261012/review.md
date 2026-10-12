# 独立技术复核摘要：C READ/DUMP 共享选字

2026-10-12，只读独立复核任务 `/root/c_mux_review` 对准确候选作出 **PASS_WITH_SCOPE / PASS WITH CONDITIONS**。本页由执行方按主协调转交的结论登记，不是作者自批，也不代表 A/B 成员或其指定 AI 的批准。

复核候选：`project/rtl/c_board/i17_vio_evidence.sv` SHA256 `a3cc8415a9d6875f94433319f71c0b861a3cc0c705a408d10af49863941e1fef`；比较基线 SHA256 `135271131d893eba2b8e22a7b596c78292de4050a69855f131b5fe5a582fdfd6`。范围仅 READ/DUMP 共享组合读取及其公开输出影响锥。

复核核对了 8 项冻结资产、30 份仿真日志及 12 份综合原件哈希，确认与运行/冻结清单匹配。有限仿真行为保持和同条件 OOC 资源改善通过；没有本轮 BLOCKER/HIGH。全部函数文本保留，原时序仅四处消费者替换，READ type 9 旁路和 procedural `if(dumping)` 保持；没有新增寄存级或 Cycle Contract Delta。

三个负例的实际首错及无完成标记均已独立核实：

| Canary | 实际首错 |
|---|---|
| 原事务 checker | cycle 79，kind 3 / word 17，expected `90060060`，observed `90060160` |
| 新定向 checker | cycle 10，word 0，expected `d0e0f001`，observed `d0e0f101` |
| 新 19-output miter | cycle 195，`all19 mismatch` |

保留项与边界：

| Finding | 级别/状态 | 限定说明 |
|---|---|---|
| `C-EVID-SHARED-REV-001` | LOW，保留 | 新 canary runner 没有自动绑定完整失败周期；本轮首错已独立核实。未来自动接受前应完整匹配，或继续独立核实准确首错。本轮未修改 checker 或补跑 EDA。 |
| `C-META-SH-001` | INFO，范围限制 | 未逐项隔离非零 `diag_bank`、`report_seq` 变化、空闲 `partial=1` 场景，不宣称穷举。 |
| `C-IMPL-LUT-001` | 历史 HIGH，范围外 OPEN | 单模块改善不关闭整机资源问题。 |
| `C-AB-CTRL-001` | 历史 HIGH，范围外 OPEN | 本轮没有处理启动控制接口接合。 |

OOC 总 LUT 6634→3684、逻辑 LUT 6546→3640、Memory LUT 88→44、FF 10509→10451。合成诊断 WNS 8.674→8.216 ns；未设置 I/O delay 与 `HD.CLK_SRC`、未布局布线，不作 STA、整机适配或板测通过结论。Power NOT APPLICABLE。

主协调依据既有用户授权，在此限定复核后安排准确字节的原工程单文件接入；[接入回执](originals/integration/integration-receipt.json)记录实际操作。原始 manifest 中的 pending 标签是当时历史状态，保持原字节；本页承载后续复核结论，不改写原件。
