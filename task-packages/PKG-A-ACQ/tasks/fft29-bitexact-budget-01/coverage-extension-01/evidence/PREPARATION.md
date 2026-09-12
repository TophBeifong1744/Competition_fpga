# 本轮准备检查（2026-09-12）

- 输入：按旧 selection/check 的准确 case ID 确认历史60帧、余下136帧；B提交固定bff45e7bbedab321fc4815e1432f1575c750edc4。
- 原包155项SHA-256不变；本地HEAD bb82de16a33751fb684243a19132dbb6b5736d91是用户基线e670eef5的后代，旧FFT29任务Git树无变化。
- 余下136个NPZ全部存在，已核对Git blob ID与B manifest SHA-256。
- frames gzip和解压后的原JSON分别按B manifest/packing核对。
- 原9项比较器正负例 + 4项次数/容量/配置复用约束检查通过，见checker-tests-01.log。
- Python源码AST已解析；对新增准备脚本/Tcl文件的git diff --no-index --check无空白问题。
- 未启动Vivado/XSim，未生成本轮新RTL结果，未重复综合/布局布线。
- Tcl入口只做了配置块/禁止综合命令的文本约束测试；附加的独立Tcl解析器探针因Python运行时缺少init.tcl未完成，见tcl-parser-probe-01.log。
  该探针不是Vivado失败证据，不修改全局环境或安装工具；实际Vivado入口由拓芙运行时验证。
- 首轮输入审计误查manifest中已移入packing的原JSON哈希键；错误已修正。
  failed-input-audit-01保留失败版本与同错误再次复现的原始输出，NPZ/golden从未修改。
- 所有其他任务修改保留；不提交、推送、合入；待操作结果回传后整理最终覆盖结果。

待拓芙执行的命令、输出路径及易错点见../README.md。PREPARATION-SHA256.json只冻结本次准备材料，
后续新运行结果使用新的清单，不重写本准备清单或原任务包清单。
