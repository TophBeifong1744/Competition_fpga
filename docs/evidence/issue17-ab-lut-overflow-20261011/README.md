# #17：A/B 增量组合的 LUT 超限原始证据

2026-10-11，C 在唯一原工程中接入 A 缓存/STOP 八源增量和 B 算术 v02 后，现场重新执行综合、实现。本目录交付这一次真实失败记录，供 A/B 在原任务继续资源优化；不是新源码包或完整工程包。

**结论：综合完成，opt_design 完成；place_design 前置 DRC 因 LUT 超限失败。布局器尚未执行，布线未开始。**

## 准确版本

- Vivado 2025.2，器件 `xc7z020clg400-1`，顶层 `i17_vio_board_top`。
- 仓库父版本 `31cb99676190e9db974b803498b5d60fc001cf9c`；实际运行源为父候选加本批 A/B 增量，不是未修改的父版本。
- [A 八源增量及作者说明](https://github.com/TophBeifong1744/Competition_fpga/issues/17#issuecomment-6107688482)。
- [B v02 限定复核及源码入口](https://github.com/TophBeifong1744/Competition_fpga/issues/17#issuecomment-6107731085)，使用 `PRODUCT-FREEZE-v02.json`，不使用 v01 或 `fixed/` 旧源。
- 9 个文件替换、2 个 helper 新增后，44 项源集合 SHA256 为 `44e7792a692da4c682ab406174f96c95566baae07cad7a79b0d40d4ea65c32d6`。本次回读实际工程，44/44 字节仍与该组合一致。逐源路径、哈希及 ZIP 身份见 [source-identity.json](source-identity.json)。
- 物理顶层、时钟、PWM、VIO/ILA、四官方 IP 和两个 XDC 沿原配置；没有新增 false-path 或修改器件容量检查。

## 本次实际结果

| 阶段 | 原件与位置 | 结果 |
| --- | --- | --- |
| 综合 | [synth-runme.log](raw/synth-runme.log)，第 1999 行 | `synth_design completed successfully`；该命令用时 36 分 03 秒，19:06:52 退出工具 |
| 逻辑优化 | [impl-runme.log](raw/impl-runme.log)，第 247 行 | `opt_design completed successfully` |
| 布局前检查 | 同日志第 281–284 行 | `DRC UTLZ-1`：逻辑 LUT 需求 68,625，可用 53,200；明确 `Placer not run` |
| 布线 | 同日志后续状态 | 未执行；19:12:59 退出工具 |

`C-IMPL-LUT-001` 为本次阻断：逻辑 LUT 达容量约 **129.0%**，超出 **15,425**。这不是最终 STA 超时结论，也不是现场操作或线程设置导致的资源容量变化。

综合阶段的 [utilization-synth.rpt](raw/utilization-synth.rpt) 记录总 Slice LUT 77,456（145.59%），其中 Logic 66,996、Memory 10,460；Block RAM Tile 45.5/140，DSP 66/220。这些是 **综合阶段** 的统计，不能与 opt_design 后的 68,625 Logic LUT 混用；综合报告还列有四个官方 IP black box，因此不能把其中数值直接称为完整链接后的最终资源占用。

本次日志中原 `Synth 8-326`、`Synth 8-295` 未出现，之前 `shortest<=longest` / `4-131` / `4-130` 致命异常未复现；不据此签署全网表无环或 STA 通过。功耗优化仍记录 `HACOOException / Too many TFIs and TFOs` 警告，不能称全部功耗优化成功。

## 原件和使用方式

- [综合原始日志](raw/synth-runme.log)
- [实现原始日志](raw/impl-runme.log)
- [综合资源报告](raw/utilization-synth.rpt)
- [opt_design 后 DRC 报告](raw/drc-opted.rpt)
- [原件 SHA256 和字节数](evidence-index.json)

四份原件按字节复制；本目录 `.gitattributes` 禁止换行转换。未重写原生错误、主机路径或警告；接收方可直接引用日志。大型 DCP 保留 C 本地，本次不重复上传，源码由准确 A/B 原交付及父候选引用。

## 下一步和未测边界

A/C 根据当前综合网表按层级定位 LUT 大户及缓存映射，B 继续负责算法后端数值和算术结构；尚无模块级资源报告，不能把本次全部超限归因于某一成员或 VIO。需在原工程减少实际 LUT 需求，再重新综合和实现；不通过关闭 UTLZ-1 冒充资源适配。

本目录是 C 的原始失败证据交付，没有新增合并、板测或任务完成结论。`C-AB-CTRL-001` 正常启动接合问题、无 VIO 连续入口及 watchdog 预算仍未解决；当前没有新布线、完整 STA 或板级结果。

证据复用：C 主流程及独立只读复核核对日志、44 项源身份和失败边界；未重新执行 EDA 或测试。工程仍保留在现场原路径，后续无需重新搭建。
