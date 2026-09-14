# 两项Skill分流发布与本机核对

用户授权：提交、推送并发布到main。按现行工作流，分工、验收计划、旧版退役归档及候选索引进入main；未获B独立批准的实现分别提交待审任务分支，不自审自合。此次不是新阶段验收，不改9/14限定结论或C任务。

发布前main、origin/main及直接远端均为`80bd2c723eac803eb8bbbddd96369d8e9d2a543c`，0/0。分工、验收和归档已于9/14推送main，内容提交`ccaeae1c0ac9be07e006ffed09cb7f16bf064906`；随后刷新并直接查询，三者相同、领先/落后0/0。本页补记两条已推送候选的准确身份及发布核对，不代表B已接收或批准。

<a id="skl-001"></a>

## SKL-001：FPGA模块开发与仿真验证

- 待审分支：`codex/toph/skl001-module-verification-20260914`。
- 已直接核实的远端SHA：`c562466805aff08201cd457cc2e6ee7464a3566f`，相对共同父提交`ccaeae1`新增141个文件；没有带入另一Skill的未审变更。
- 固定版本：[源码与使用说明](https://github.com/TophBeifong1744/Competition_fpga/tree/c562466805aff08201cd457cc2e6ee7464a3566f/skill/fpga-module-verification)、[完整包](https://github.com/TophBeifong1744/Competition_fpga/tree/c562466805aff08201cd457cc2e6ee7464a3566f/task-packages/PKG-A-SKILLS)、[B复核要求](https://github.com/TophBeifong1744/Competition_fpga/blob/c562466805aff08201cd457cc2e6ee7464a3566f/task-packages/PKG-A-SKILLS/REVIEW.md)。
- 范围：`skill/fpga-module-verification/`及`task-packages/PKG-A-SKILLS/`；0.3.0作者候选，不含SKL-002或生产RTL变更。
- 原作者证据：XSim 2025.2正常PCM 792比较、elastic 1125检查、两类故障及恢复复测；本次复跑7项运行器测试、结构检查通过，不重跑或冒充B陌生场景验收。
- 原包manifest中的“未发布”字段及作者README是生成时快照；本页记录后续Git发布，不改作者原始清单与哈希。

<a id="skl-002"></a>

## SKL-002：PYNQ Overlay/DMA验证

- 待审分支：`codex/toph/skl002-pynq-validation-20260914`。
- 已直接核实的远端SHA：`55039cf8bfab2bd6112192c8bd646d427a52a642`，相对共同父提交`ccaeae1`修改/新增21个文件；没有带入SKL-001新实现。
- 固定版本：[源码、使用说明及完整证据](https://github.com/TophBeifong1744/Competition_fpga/tree/55039cf8bfab2bd6112192c8bd646d427a52a642/skill/pynq-overlay-dma-validation)、[B复核要求](https://github.com/TophBeifong1744/Competition_fpga/blob/55039cf8bfab2bd6112192c8bd646d427a52a642/skill/pynq-overlay-dma-validation/references/review-handoff.md)。
- 范围：仅`skill/pynq-overlay-dma-validation/`，包括此前未提交整改、完整离线实现及两份证据；不以“此前已有”代替批准。
- 本次复跑50项测试、39个subtest通过，结构检查通过；10份证据绑定源码哈希一致。
- 唯一新增包装配置是`.gitattributes`，固定作者源和证据的实际字节，避免换行转换使原哈希失效；不改脚本/测试逻辑或原始结果。
- 作者说明中的未发布状态保留为2026-09-13生成时事实；后续发布由本页固定SHA。真实PYNQ未准入，禁止去掉board guard执行实板。

## 给B的复核提示

从本页最终记录的两条准确远端SHA分别检出候选，不直接使用共享main的混合未提交工作。SKL-001按其`REVIEW.md`复跑真实XSim正常/故障/恢复，并给作者未用过的模块/未知故障；SKL-002按`references/review-handoff.md`独立复跑golden、缓存/超时/停止/所有权、多profile等。两项分别批准，任何自检或额外代理评估都不代替你的签署。只批准实际范围，未测实板/时序/CDC如实NOT_RUN。通过准确SHA后由复核人按team-workflow限定合入、验证、推送main并核对各自设备。B的9/18算法主线及C不新增任务规则不变。本提示尚未通过聊天工具送达。

## 材料与清理边界

- 旧活动Skill三个文件退役，41份原件及manifest集中到`archive/2026-09-13-before-skl001-technical-upgrade/`，逐字哈希通过；不把旧0.2.0候选归档标成批准。
- 新SKL-001源码/证据140个清单项哈希通过；包括原始`.log`，没有因根忽略规则漏交。
- 不切换或重置脏共享目录；用独立Git索引提交待审分支，不建立另一套活动工程。共享目录仍可能显示与main不同的候选源码：它们须与远端待审SHA逐项一致，不是允许遗漏材料。
- 不删除两条新待审分支、不清理其他长期或在做分支，不更改生产rtl/tb/sim/PS/BD/XDC和冻结阶段快照。
- 完成后核对实际共享main、origin/main、直接远端，以及本批已修改/未跟踪/忽略项；本页不代签B/C电脑状态。最终main提交号由发布回报给出，避免自引用SHA循环。

## 本批实际检查与收尾

| 项目 | 结果 |
| --- | --- |
| 主线发布 | `ccaeae1c0ac9be07e006ffed09cb7f16bf064906`已非强制推送；实际共享main、origin/main、直接远端一致，0/0；本记录补交后再次核对，最终SHA见用户回报 |
| 待审材料入库 | SKL-001的141份及SKL-002的21份文件与各自提交的原始Git blob逐字节相同；两条本地/跟踪/实际远端候选SHA核实一致 |
| 清单与证据 | SKL-001清单140项、旧归档41原件、PYNQ 10份源文件绑定全部通过；旧记录“未发布”只描述作者生成时，不改签其原哈希 |
| 发布前复跑 | SKL-001运行器7项；PYNQ离线50项/39个subtest；两项quick_validate均通过。未新增实板、综合时序或独立B结论 |
| 文档/格式 | 本次主线提交280个本地链接在提交树中可达；活动内容空白检查通过。原件与原始日志按字节保留，不为消除CRLF格式提示重写历史证据；Git长路径读取使用对象ID，避免Windows路径歧义 |
| 本地材料 | main上的162项候选差异均已入对应待审远端；不是遗漏，也不是全仓干净。无额外在做差异、无本批遗漏忽略材料、无遗留暂存；本批未说明/未保存的有用材料为0 |
| 正式工程/历史快照 | 相对发布前，rtl/tb/sim/ps/vivado/hardware/deliverables无改动；未倒填阶段验收 |
| 清理/恢复 | 本轮只移除两份临时Git索引，无额外工程或分支删除；上一轮退役原件已随main归档，可按41项manifest恢复到独立比较目录。两条待审分支保留，不能提前删 |

main中的旧PYNQ基线保留至新候选获批准后替换；旧纯协作Skill已退役，不恢复为活动入口。该分流是执行“未审实现先入待审分支”的既有规则，不是推送失败。B后续按两条候选分别评审并限定合入，不能将本次工作执行发布当成独立技术批准。
