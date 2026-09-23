# 文件与工作区保留规则

采用 fpga-team-workflow：一个成员默认一个活动checkout；分支不等于新工程副本。只有独立复现或真实并行写入才新增最小worktree，完成后按证据检查退出。

- Issue #26 候选将活动源码/入口归入 project/rtl、simulation/tb、simulation、software、models、data/fixtures；skill 与外部原生 one 不迁移。后续产品只维护一份权威源，任务包仅保留交付索引、配置和必需冻结证据。准确映射及待审边界见[实体迁移](layout-migration.md)。
- 旧 task-packages/、deliverables/、archive/ 的冻结源码/失败日志为历史证据，不全量删重，不当新活动源码。代码接入必须有准确范围的真实成员批准与新入口验证。
- .xpr、.srcs、.bd、.xci、.mem/.coe、锁定IP的DCP及bit/XSA/ELF/HWH不能按后缀当缓存。
- 原录音、旧错误素材、失败日志和唯一测量保留；临时目录名、Git忽略、已合并都不是删除依据。
- 清理先dry-run：解析确切路径、检查junction/链接、写入与EDA占用、Git未提交/未跟踪/忽略文件；每个删项须能从固定Git对象或已校验归档恢复。只删此次项目由工具创建且证实闲置的副本；不扫整个C/E盘。
- 清理目录前先保护独有文件。已批准且入main的干净worktree可以删除；待审分支、未归档独有数据和外部原生工程保留。远端短分支删除与本地证据清理分别判断。
- 历史 .gitignore 有通配二进制/日志规则，不能以status干净断言材料已保存；本批发布必须检查ignored材料，不靠增加忽略项掩盖未提交成果。
- codex_out/ 和 .local/ 是忽略的本机诊断/私有区域；忽略不授权删除。正式工程仍为 existing/UNVERIFIED，不能把诊断输出当 project/par 的正式工程或 simulation/work 的 ModelSim 证据。

本轮实查和清理去向见[迁移记录](../docs/maintenance/workflow-migration-20260923.md)。
