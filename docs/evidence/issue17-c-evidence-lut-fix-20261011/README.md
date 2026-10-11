# Issue 17：C evidence 读出 LUT 修复

本次由 C 负责修复 `C-EVID-LUT-001`。新的活动源是 [`project/rtl/c_board/i17_vio_evidence.sv`](../../../project/rtl/c_board/i17_vio_evidence.sv)，SHA256：`135271131d893eba2b8e22a7b596c78292de4050a69855f131b5fe5a582fdfd6`。旧 task-package 中的同名文件是冻结历史快照，不能再拿来覆盖活动源。

根因是 `word_for` 先把不同记录选择到6656位宽总线，再取一个32位字，形成两处昂贵的宽多路选择。修复只调整组合选择顺序：先在各记录内取32位，再选记录种类；不新增流水级，不改寄存器、VIO/ILA布局、LSW-first顺序、尾字补零、握手、释放、STOP或错误行为。A/B、top、IP和XDC均未改。

相同 Vivado 2025.2、`xc7z020clg400-1`、OOC单模块综合选项及共同诊断时钟下：

| 资源 | 修复前 | 修复后 | 变化 |
|---|---:|---:|---:|
| 逻辑 LUT | 20546 | 6546 | −14000（−68.14%） |
| 总 LUT | 20634 | 6634 | −14000 |
| LUTRAM | 88 | 88 | 0 |
| FF | 10489 | 10509 | +20 |
| F7 / F8 mux | 1943 / 694 | 2271 / 750 | +328 / +56 |

FF是工具映射后的数量；RTL没有新增寄存级，限定仿真的返回周期保持。**这些是单模块对比，不能据此签整机资源、时序或板测PASS。** 原整机优化阶段的 `u_evidence` 20044逻辑LUT属于另一上下文，也不能与这张表混算。

验证原件已经完成，本次发布没有重跑：独立逐位预期与旧函数差分409600项；公开READ 6656次；事务检查29178项；全部19个输出差分7772周期一致。覆盖非法索引、X/Z、尾字补零、释放后的原始数据、长诊断记录后的短记录残留及未初始化word63。原始日志、最终TB、旧源输入、命令脚本及manifest在 [`originals/`](originals/)。

独立AI技术复核结论为 **PASS WITH CONDITIONS**，仅接受本次限定仿真与隔离资源改善，并允许准确SHA的单文件接入；用户随后授权推送。复核摘要见 [`review.md`](review.md)，本资料不代表A/B成员批准。LOW `C-EVID-LUT-SH-001` 保留：原runner的canary判定仅匹配 `Fatal: DATA_CHECK`；本次独立复核另核实首错确为kind3/word17且没有成功完成标记。没有改动测试来掩盖这一限制。

## 接入原工程

本机已于2026-10-11 22:44（UTC+8）接入原项目：

`D:/vavido_project/i17_live_loop/project/par/i17_live_loop/i17_live_loop.xpr`

只替换XPR原来引用的：

`i17_live_loop.srcs/sources_1/imports/i17-i19-live-loop-c-20261010/board-prep/rtl/i17_vio_evidence.sv`

接入前后99项校验仅此文件变化，其余98项哈希和mtime一致。XPR拓扑与原run文件未改；准确记录见 [`integration-receipt.json`](originals/integration/integration-receipt.json)。旧源、XPR和92.5MB的旧run备份留在本机诊断目录，本发布包不包含DCP、vendor缓存或这些大备份。

其他人复用现有原XPR时，将上述活动源的准确字节复制到自己项目相同的已有import路径，重新打开原XPR，重新综合即可，无需重建工程或重新生成IP。若GUI仍显示旧run完成，先Reset `synth_1`再Run Synthesis，不使用Force Up-to-date。保存新的利用率及原生log；综合满足后再实现并保存DRC/时序报告。旧DCP不对应新源。

**`C-IMPL-LUT-001`（整机资源超限）和 `C-AB-CTRL-001`（启动控制接口未接合）仍OPEN。** 本次没有启动整机综合、实现、下载或板测，不能直接上板或声源联动。

## 原件与复现边界

[`publication-index.json`](publication-index.json)列出本次活动源及发布文件的SHA256；[`original-copy-manifest.json`](original-copy-manifest.json)证明`originals/`从已有证据逐字节复制。日志、manifest中的本机绝对路径和旧状态是**当时的历史执行记录**，不表示其他机器使用该路径，也不替代本页的接入后状态。不要修改原件里的路径或伪造一次新执行记录。

复现所需旧原源、原TB、最终TB、旧模块差分副本、生成脚本和runner均已给齐。参见 [`REPRODUCE.md`](REPRODUCE.md) 使用准确输入在新的空目录运行；本次复核与发布复用原有验证，不要求重复运行。
