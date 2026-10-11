# 按层级资源定位：A、B、C 的实际占用

本次从现有检查点直接导出，没有重新综合、优化、布局或布线，也没有修改工程。报告由 Vivado 2025.2 的 `open_checkpoint`、`report_utilization` 和只读网表查询生成。原始脚本和命令记录仅供追溯，不要求收件人重跑。

## 优先查看的原件

- [完整层级报告：opt_utilization_hierarchical.rpt](hierarchical/opt_utilization_hierarchical.rpt)
- [完整总资源报告：opt_utilization_total.rpt](hierarchical/opt_utilization_total.rpt)
- [综合阶段层级对照](hierarchical/synth_utilization_hierarchical.rpt)
- [可解析的层级 JSON](hierarchical/opt_utilization_hierarchical.json)
- [运行、输出校验及未改原件记录](hierarchical/run-manifest.json)

**采用 opt 检查点作为完整资源基线：** 它已经链接四个官方 IP，没有黑盒，Design State 为 Optimized，仍在布局前。综合检查点保留四个 IP 黑盒，不能用它的数值代替完整链接后的总量。该 opt 报告精确复现原 UTLZ-1 的 **68,625 Logic LUT**。

## 三个主要且互不嵌套的模块

| 当前归属 | 实例路径（顶层以下） | 模块 | 总 LUT | Logic LUT |
| --- | --- | --- | ---: | ---: |
| A 采集与前端 | `u_core/source` | `four_mic_top_forward` | 33,688 | 24,830 |
| B 算法后端（含官方 IFFT） | `u_core/backend` | `pcm4_doa_official_entry` | 22,483 | 20,364 |
| C 自有观测记录 | `u_evidence` | `i17_vio_evidence` | 20,132 | 20,044 |

**C 自有观测记录同样是主要热点，需要纳入优化。** 官方 `u_vio` 本身为 351 Logic LUT，`u_ila` 为 739，`dbg_hub` 为 492；不能把 C 自写记录模块的两万 LUT 称为官方 VIO IP 的开销，也不能把全部超限归给 A 或 B。

进一步定位的原有子树如下。下表包含在上表相应父模块内，**不能再次相加**：

| 范围 | 实例路径 | 总 LUT | Logic LUT |
| --- | --- | ---: | ---: |
| A 数值预处理 | `u_core/source/forward_window/u_forward/np` | 10,888 | 6,792 |
| A 诊断记录存储 | `u_core/source/forward_window/u_store` | 7,863 | 4,095 |
| B 原生后端（不含官方 IFFT） | `u_core/backend/native/backend` | 21,316 | 19,510 |
| B 算术 helper | `u_core/backend/native/backend/backend_math` | 3,866 | 3,866 |
| B PHAT helper 子树 | `u_core/backend/native/backend/phat_math` | 7,049 | 7,049 |

原生层级表中普通实例行表示含子模块的子树，括号行表示本层自身。原语统计 TSV 按直接父级统计原语，不能用原语个数直接替代打包后的 LUT 站点数。

## 资源口径和优化边界

完整 opt 基线为总 LUT **80,154 / 53,200（150.67%）**，包含 Logic **68,625**、LUTRAM **10,484**、SRL **1,045**。FF 为63,187，BRAM Tile 为53.5/140，DSP 为80/220。

因此不应只关注原报错中的“Logic 超出15,425”。即使按现表机械扣除整块 C `u_evidence` 的20,132个总 LUT，仍为60,022，超过53,200。这个减法仅用于说明资源口径，**不是删除授权，也不是改版后的资源预测**；必要记录、停止、排空、控制和 ILA 功能要按既定合同保留，实际改动后仍须用新综合结果确认。

A 可沿前端预处理、缓存和诊断存储继续定位；B 沿原生后端、算术和 PHAT 结构定位；C 沿自有观测记录的数据存储及读出路径定位。当前统计支持这样的工作划分，但不证明具体源级修复、算法精度、时延或吞吐已满足要求。

对 C 模块补充源级只读定位：`i17_vio_evidence.sv:106–126` 的 `word_for()` 构造6656位 padded 数据，再用动态地址选择32位字；第212和229行分别用于 ILA dump 和 VIO 单字读取。**推断**该宽类型选择及两条读出路径值得优先核查，但层级报告不能把20,044个 Logic LUT精确分摊到某条表达式。模块还保存6626位 terminal 和其他快照，并参与 core 接收、control 状态与记录释放；不能直接删模块并认为原功能不变。当前 C 源 SHA256 为 `d6b7096d55bdcc44ff275bdad2b208c25092ad6e9668aff4edcd83dcac76fc6a`，与本批身份清单一致。

## 版本和限制

两个读取的 DCP 均来自此前同一次现场综合/实现：

- synth DCP：`d19d159f151f9fc707d494c9364305f691aa9b10553dddc41b3c866a00379330`。
- opt DCP：`80cff1cac27b09b1a583d3689316eb465ce30240aac5369321b498c8f14f8d05`。

导出过程保护50项输入，字节及mtime均未改变。其中45个 `.srcs` 文件由原44项源和 Vivado 另存的旧增量参考 DCP 组成；后者位于 `utils_1/imports/synth_1/i17_vio_board_top.dcp`，不是新增 RTL。没有覆盖旧失败日志或重写原件。

这些报告只完成资源归属定位。`C-IMPL-LUT-001` 仍开放；`C-AB-CTRL-001` 正常启动接合问题仍开放；没有新布局、布线、STA或板级通过结论。
