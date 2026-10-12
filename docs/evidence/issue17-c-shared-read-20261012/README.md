# Issue 17：C evidence 共享 READ/DUMP 选字

本轮仅优化 C 自有 [`i17_vio_evidence.sv`](../../../project/rtl/c_board/i17_vio_evidence.sv)，准确候选 SHA256 为 `a3cc8415a9d6875f94433319f71c0b861a3cc0c705a408d10af49863941e1fef`；修改前基线为 `135271131d893eba2b8e22a7b596c78292de4050a69855f131b5fe5a582fdfd6`。独立技术复核结论为 **PASS_WITH_SCOPE**，接受本轮有限功能仿真和同条件单模块 OOC 资源改善；范围及保留项见 [review.md](review.md)。这不是 A/B 成员批准或整机验收。

原逻辑分别为 READ 和 DUMP 调用一次 `word_for`、`meta_for`。DUMP 活跃时 `busy` 拒绝 READ，两路不会同拍消费，因此可在调用前共享类型和字索引，并各调用函数一次。新增组合块使用 `always_comb` 和 procedural `if(dumping)`，保留原四态选择语义；READ type 9 的实时 `live_status` 旁路保留原位。

全部函数正文与签名原样，原时序过程仅替换四处结果消费者。没有新增寄存或流水级，不改变接口、容量、精度、LSW-first、尾字补零、READ 返回边沿、DUMP 每拍一字、metadata/cycle/magic 对齐、握手、释放、STOP、同步 reset 或错误优先级。包括 DUMP 最后一字同拍 READ 仍忙拒绝，下一空闲边沿才可读取，以及同拍捕获与错误更新仍采旧值。A/B、其他 C 源码、IP 和 XDC 未修改。

## 同条件资源结果

两次真实综合均使用 Vivado 2025.2 SW6299465、`xc7z020clg400-1`、`synth_design -mode out_of_context -flatten_hierarchy rebuilt`，共同诊断时钟 16.276041667 ns（工具舍入为 16.276 ns）。基线和候选各一次，顺序执行，进程退出 0。

| 资源 | 修改前 | 候选 | 变化 |
|---|---:|---:|---:|
| 总 LUT | 6634 | 3684 | −2950（−44.47%） |
| 逻辑 LUT | 6546 | 3640 | −2906（−44.39%） |
| Memory LUT | 88 | 44 | −44 |
| FF | 10509 | 10451 | −58 |
| F7 / F8 mux | 2271 / 750 | 1260 / 416 | −1011 / −334 |

没有 latch、黑盒、BRAM 或 DSP。Memory LUT 减少来自共享读取后的映射变化，不是缩减逻辑记录容量。无错误或 critical warning；候选新增 16 条生成层常量端口警告，原始警告完整保留。

合成诊断 WNS 为 8.674→8.216 ns，变化 −0.458 ns；缺少 I/O delay 和 `HD.CLK_SRC`，且没有布局布线，**不能据此签 STA 通过、整机资源适配或板测通过**。具体原始报告、起止输入哈希及工具启动失败分类见 [synthesis-run.json](originals/synthesis-run.json) 和 [synthesis-result.json](originals/synthesis-result.json)。

## 已执行验证

旧事务 TB 原样重跑：6656 次公开 READ、29178 项检查、7772 周期全部 19 个输出差分。新定向 TB 对本轮准确基线作 195 周期全部 19 个输出差分（含 reset），并执行 127 项独立预期检查、64 项公开 selector X/Z、2 项明确标注的白盒 `dumping=X/Z` 差分；白盒场景不代表自然生产场景。两组均 `pending=0`。

覆盖 DUMP 首/中/末边沿 READ 忙拒绝、idle/dump 中多 action 报错、DUMP 中 ABORT 脉冲、在途 reset、外部 selector 变化、live DUMP 冻结与 READ 实时值、同拍 record 捕获，以及稳定地址下 record/diag/error/count 内容更新。三个隔离 canary 的实际首错均经独立核查，未出现完成标记；新 canary 自动匹配仍有 LOW 保留项，不宣称验证穷举。

实际命令为 `python codex_out/i17-evidence-shared-read-20261012/run_selftests.py`；原生综合在该诊断目录执行 `vivado -mode batch -source diagnostic_synth.tcl -log diagnostic_synth-attempt4.log -journal diagnostic_synth-attempt4.jou`。全部五组 `xvlog/xelab/xsim` 阶段退出 0；XSim 的 `$fatal` 也可能返回 0，因此 runner 和独立复核检查首错及完成标记。入口拒绝覆盖已有输出，不要直接在归档目录重新执行。原件保留当时绝对路径与 pending 状态；当前限定复核结论由 [review.md](review.md) 补充，不倒填原始 manifest。

## 原工程接入与下一步

2026-10-12 22:19:57（UTC+8）已将准确候选接回唯一原工程的既有 import 源路径，无需重新导入：

`D:/vavido_project/i17_live_loop/project/par/i17_live_loop/i17_live_loop.xpr`

目标文件为 `i17_live_loop.srcs/sources_1/imports/i17-i19-live-loop-c-20261010/board-prep/rtl/i17_vio_evidence.sv`。复制前后未发现活动构建；完整原工程及仓库 RTL 清点共 421 项，仅该源文件变化，其余 420 项 hash、mtime 和长度不变，包括 XPR、IP/XDC、原 native runs、其他 RTL 和未跟踪 `sound_servo_clock.sv`。源与 XPR 已先备份；[接入回执](originals/integration/integration-receipt.json)、[前清单](originals/integration/before.json)、[后清单](originals/integration/after.json)可核验。

本轮没有启动全工程综合、实现、下载或板测。原 run/DCP 保持旧版本，不能作为新候选结果。**新 C 候选接入不等于 A/B 新包已经接入**；建议在当前 A/B 增量按其准确范围接入后，由现场操作人统一执行一次整机综合，保存原生 log、利用率与层次报告，再按结果决定实现。旧 HIGH `C-IMPL-LUT-001`、`C-AB-CTRL-001` 仍在原范围内 OPEN。

[original-copy-manifest.json](original-copy-manifest.json)逐项证明选定原件字节一致；[publication-index.json](publication-index.json)给出本目录文件和活动候选哈希。本包仅含必要文本资产，不含 vendor 缓存、WDB、PB、DCP 或完整工程 ZIP；没有修改旧证据目录。Power 为 NOT APPLICABLE。
