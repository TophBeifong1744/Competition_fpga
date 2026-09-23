# 迁移前可恢复基线

准确main：`704407e19f25a5405ef4d8f0272e977224e69b2c`，留在main历史，不改写历史、不删冻结证据。旧规则/分工停用。

旧AGENTS、README、CONTRIBUTING，docs的team-workflow、project-plan、team-tasks、current-status、work-packages、three-handoff-workflow、member-c-operation-sheet、task-package-handoff、git-workflow、phase-closeout、skills-delivery-plan、competition-acceptance，以及旧phase目录，均可由固定Git blob逐字节恢复。

为避免大面积重复，不再复制一套旧md；此页＋固定提交为归档索引。例：`git show 704407e19f25a5405ef4d8f0272e977224e69b2c:docs/project-plan.md`；恢复到新临时位置，不覆盖活动源。旧批准/失败原件原路径和哈希不变。

[迁移记录](../../docs/maintenance/workflow-migration-20260923.md)。
