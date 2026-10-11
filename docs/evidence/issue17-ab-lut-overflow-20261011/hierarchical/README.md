# 现有检查点的完整层级资源报告

已用 Vivado 2025.2 从现有检查点直接导出，原生命令退出0。没有重跑综合、opt、place或route，没有修改工程、RTL、约束、IP或DCP。50项受保护输入（两个DCP、XPR、两个原run日志及45项.srcs文件）的原字节和mtime在导出后全部保持。

## 首选基线：已有 opt 检查点

`opt_utilization_hierarchical.rpt`：完整902行层级，无黑盒，Design State=Optimized。对应已完成 opt_design、随后 place 前 UTLZ-1 阻断的检查点，**不是布局/布线结果**。

| 资源 | 使用 / 可用 | 利用率 |
|---|---:|---:|
| Slice LUT | 80,154 / 53,200 | 150.67% |
| LUT as Logic | 68,625 / 53,200 | 128.99% |
| LUT as Memory（含SRL） | 11,529 / 17,400 | 66.26% |
| FF | 63,187 / 106,400 | 59.39% |
| Block RAM Tile | 53.5 / 140 | 38.21% |
| DSP | 80 / 220 | 36.36% |

以上直接来自 `opt_utilization_total.rpt`，Logic LUT 与已有 UTLZ-1 的68,625完全一致。完整层级分列 LUTRAM=10,484、SRL=1,045，两者合计为上述 LUT as Memory。

| 互不嵌套的主要路径 | 总LUT | Logic LUT |
|---|---:|---:|
| u_core/source | 33,688 | 24,830 |
| u_core/backend | 22,483 | 20,364 |
| u_evidence | 20,132 | 20,044 |

继续向下定位可见：B `native/backend` 为21,316总LUT/19,510 Logic；其 `backend_math` 3,866，`phat_math` 7,049。前端 `np` 为10,888总LUT/6,792 Logic；`u_store` 为7,863总LUT/4,095 Logic。这些是嵌套行，不得再与父行相加。此表只交代当前网表资源归属，不是批准删除模块或预计优化收益。

## 综合阶段对照

`synth_utilization_hierarchical.rpt`：完整68行层级，四个未链接黑盒为FFT、IFFT、VIO、ILA，见 `synth_blackboxes.tsv`。其77,456总LUT/66,996 Logic未包括四IP，不能替代opt完整基线。原生加载时四条 black box critical warnings 已保留，未用stub填充或重新生成IP。

## 输出与身份

- 每阶段均有 `*_utilization_hierarchical.rpt`、`*_utilization_total.rpt`、`*_utilization_hierarchical.json`、`*_blackboxes.tsv`、`*_primitive_counts_by_parent.tsv`。
- JSON逐行复制原报告数字，保留源行号、层级路径和local/subtree区别。TSV由原生 `get_cells/get_property` 按直接PARENT与REF_NAME统计；原语数量不等于打包后的LUT站点数。synth/opt分别162,880/174,443个原语。
- 本机官方帮助说明 XLSX 导出仅支持GUI。本轮遵守只读批处理范围，交付完整原报告、精确值JSON及TSV，不打开GUI导出。
- `input-manifest.json`：全部原件路径、大小、mtime和SHA256。synth DCP：`d19d159f151f9fc707d494c9364305f691aa9b10553dddc41b3c866a00379330`；opt DCP：`80cff1cac27b09b1a583d3689316eb465ce30240aac5369321b498c8f14f8d05`。
- `run-manifest.json`：实际命令、退出、工具版本、输出SHA256及原件未变断言；`export_reports.log/.jou` 保留完整原生执行证据。

实际报告入口（已执行，不需要为收件重跑）：
`vivado -mode batch -source export_reports.tcl -log export_reports.log -journal export_reports.jou`

cwd为本目录；工具根 `C:/AMDDesignTools/2025.2/Vivado` 仅加入当前进程PATH，补齐经系统确认的AMD64环境。核心命令为 `open_checkpoint` 和 `report_utilization -hierarchical -hierarchical_depth 0 -hierarchical_min_primitive_count 0`。下一责任人A/M可直接按原报判断资源归属；本次未给时序、功能或上板接受结论。
