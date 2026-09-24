# 实体目录迁移（Issue #26）

## 2026-09-24 发布收尾

B 已对准确候选 `12eaee2bf469c64f5d486bedcac4057ceec25e32` 提交真实限定批准，[PR #27](https://github.com/TophBeifong1744/Competition_fpga/pull/27) 已合入 `main`，合入提交为 `52069408aa34048d0736422c01a1bb068d3ea29c`；原项目共享目录已安全快进并采用新布局。临时迁移分支及工作树已清理，独有运行材料已保留。完整核对见[本轮收尾](../docs/maintenance/layout-migration-20260923/CLOSEOUT-20260924.md)。批准仅限目录迁移和诊断入口，不扩大功能或系统验收。

以下保留9月23日交审时的候选快照；其中“待审/未合入”为当时状态，当前发布状态以上述记录和PR真实事件为准。

基线 `0a5f544893cff1094bcd1bad5346a1cf05790707`，工作分支 `codex/26-layout-migration`。用户授权移动仓库活动文件并修复路径；本批主模式 BUILD_FLOW。当前为独立工作树中的待审候选，未获得 B 对本批的真实成员批准，不表示共享 main 已完成迁移。

## 路径与唯一来源

| 旧路径 | 新活动路径 |
| --- | --- |
| rtl/ | project/rtl/ |
| tb/ | simulation/tb/ |
| sim/modules.json、run_regression.ps1、run_servo.ps1、README.md、.gitattributes | simulation/ 下同名文件 |
| sim/add_sources.tcl | project/add_sources.tcl |
| vivado/README.md | project/README.md |
| ps/README.md | software/README.md |
| model/ | models/ |
| examples/h1/ | data/fixtures/h1/ |
| docs/ 根层31份活动 Markdown | document/ 下同名文件 |

[机器清单](layout-migration-map.json)逐项列出62个 old/new、迁移前文件SHA-256与字节不变要求。新 docs/README.md 仅解释历史区，不复制活动正文。根 README 给出实际目录树；没有内容的标准目录不创建占位文件。

HDL、TB、H1 fixture 与模型 .py/.m 主体保持原字节。modules.json 仅改 files[].target 和 cases[].sources，来源 source/source_commit/original_sha256、哈希与批准状态不改。MAX_ANGLE_DEG 舵机候选仍待独立复核。接口、采样、延迟、吞吐、时钟、复位、CDC/RDC、寄存器/IRQ/DMA和错误语义无变更；Cycle Contract Delta 不适用。

layout 继续 existing/native_project，project_entry=null、adapter_status=UNVERIFIED。现有 XSim/PowerShell 是诊断入口，formal_simulation=null；不伪造 ModelSim/Questa BAT 或 .xpr。外部 one、Vivado/Vitis、BD、IP、XDC与硬件均不在本次写入范围。10/7总验收、ABC平等职责和H1/H2/H3保持不变。

## 当前入口与历史复现

- [统一模块诊断](../simulation/README.md)：从新活动路径加载7组，run_regression 只允许 codex_out 下全新目录，拒绝覆盖已有证据及 reparse 输出祖先。run_servo 保留原行为和参数。
- [H1 fixture 检查](../scripts/check_h1_fixtures.py)：只调整 fixture 根路径；检查逻辑不改，不代表 B 的生产 reader 测试或 H1 新批准。
- [Skill 示例适配](../scripts/run_module_skill_examples.py)：在 codex_out 新目录生成派生 case，PCM4 DUT 映射到 project/rtl；原 case、contract、TB、run_xsim.py 原字节不动。只复跑 pcm4/elastic 正例用于路径诊断；原 run_examples.py 的正负例完整演示按旧 SHA 复现。
- [模型说明](../models/python/README.md)：新入口为 models/python，旧源码内复现文字及旧结果仍属历史；本次不改数学行为、不新增四麦模拟、不以目录检查复核声学结果。

task-packages/、deliverables/、archive/、skill/、tools/ 与 docs/ 下 reviews/maintenance/phases/templates 等子目录冻结保留。旧报告中的源码位置、准确命令、哈希与批准绑定原提交：先按报告给出的完整 SHA 读取/检出依赖，再在隔离输出目录复现。只读旧材料不要求另造副本；真正运行旧入口时才建立最小隔离检出。回看迁移前活动路径可使用上述完整基线，但它不自动代替更早报告自身的输入版本。

特别是 `task-packages/PKG-A-ACQ/evidence/input-boundary-v0.1/check_input_boundary.py` 钉住旧 docs 下两份合同及哈希；architecture 在迁移基线就不再匹配该旧 hash。应按该证据的准确旧输入版本复现，不替换固定哈希、不复制双份合同，也不用 stub/junction 假兼容。迁移不会将这个既有失配变成通过。

新任务使用新活动路径；旧任务分支合入前检查移动路径引用与 rename 冲突，不为兼容恢复第二份 rtl/tb/model 活动源码。B 对本批应审准确候选 SHA、移动身份、路径差异和受影响入口证据；不重审全仓、不重跑未受影响声学全套。发布、真实成员技术批准与系统阶段接受分别记录。

## 本机材料与验证边界

协调器已将共享仓库根的9个 continuous-export11/work04/work05/work06/work07/work08/work09/work10/work12 本机实验目录集中到 `results/tmp/layout-migration-control-20260923/retained-local/`：2746文件、298540157字节，逐文件SHA-256前后相同；原文件删除0。仅删除两个已核实为空的目录 -p 与 .Xil。原记录位于同一 control 根下的 local-retention-dry-run.json 与 local-retention-result.json；保留清单SHA-256为 `fe17fb432cdaa9da926f3270f1a178d03a589b75c693c4c342842ce2599aa24a`。这是本机保留整理，非入库、非批准、非源码发布；实际 one 和其他未审 candidate 原位不动，299MB材料不复制进Git。

写批静态自检：18/18必保文件（11份HDL/TB、5份fixture、2份模型主体）迁移前后SHA-256及Git归一化blob相同；manifest反向还原target/sources后与基线对象一致；62个迁移输入无ignore命中；git diff --check退出0，仅普通文档有既有LF/CRLF转换提示。53份活动说明的链接核对没有新增断链，仍有基线已有的4个六麦WAV未纳入Git树；官方PDF在Git树存在但本次稀疏检出未展开。不补造缺失文件或声称未读取材料已验证可取。

独立诊断已完成：7组模块回归、1MHz舵机入口、H1数据读取和两个Skill正例退出0；三个输出保护负例按预期拒绝；37个运行输入前后稳定。实际版本、完整命令、cwd、退出码、加载路径和哈希见[本轮证据入口](../docs/maintenance/layout-migration-20260923/README.md)。原生输出位于 `codex_out/layout-validation-01`，原始文字证据已独立归档，未上传可重建编译缓存。结论限定 DIAGNOSTIC_ONLY，不能重签模块、Skill或成员批准。

综合/实现/STA、正式 ModelSim/Questa、实际 Tcl 导入、固件构建、下载及板测均 NOT_RUN；工程 adapter UNVERIFIED；功耗 NOT_APPLICABLE。任何后续路径修复按稳定 finding ID 返修，再复核受影响输入；最终待合格非作者对准确提交批准。
