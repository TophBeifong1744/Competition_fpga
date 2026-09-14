# 文件映射与版本边界

完整包版本0.2.0。MANIFEST.json逐文件绑定本包除清单自身外的所有文件，含payload、原始可见评估输出、验证器和报告材料；外部交付回报给出MANIFEST.json SHA-256防止自我认证。

## 申请合入目标

| 候选路径（包内） | 总工程目标 | 操作 |
|---|---|---|
| payload/skill/soundsight-engineering-workflow/SKILL.md | skill/soundsight-engineering-workflow/SKILL.md | 修改：动作依赖替代串行总门禁 |
| payload/skill/soundsight-engineering-workflow/README.md | skill/soundsight-engineering-workflow/README.md | 修改：可复用用法、历史状态、实际效果及边界 |
| payload/skill/soundsight-engineering-workflow/references/record-templates.md | skill/soundsight-engineering-workflow/references/record-templates.md | 修改：保留必要证据模板，增加独立动作和准确版本发布状态 |
| payload/skill/README.md | skill/README.md | 修改：修正过期SKL-001状态和事实，第二Skill只链接、不复制或批准 |

其他本包文件仅是交付/测试/报告记录，不作为核心工程源文件安装。无删除目标，无新增板级接口结论。

## 外部依赖和起始状态

`evidence/source-snapshot.json`保存读取的规则/状态、活动Skill、PYNQ起始文件大小和原字节SHA。规则/状态是该时点输入，后续更新不能倒灌为旧测试输入。当前源HEAD为80bd2c723eac803eb8bbbddd96369d8e9d2a543c；未读取远端，不把它称为远端最新。

payload中独立Skill的链接均在自身目录可用。根索引的PYNQ及docs链接是目标工程依赖，暂存区未复制；链接检查采用payload优先、总工程相同目标路径补充的投影，并分别报告。部署时保持skill层级，复核人重新确认外部依赖存在和未被未审内容替换。

PYNQ在本包起始时有8项已跟踪修改及1项未跟踪状态记录；当时对整个PYNQ目录10个文件取哈希，只作保全核对，不把这些未审字节编入Skill升级或认证它们。完成期间该任务仍有新文件出现，后续状态以交接时实际目录为准，不能要求它回退到起始快照。其后续工作仍归原任务；本次不迁移、不删除、不签通过。

无需要上传的WAV/BIN/供应商原件或受控外部数据副本。真实案例只引用现行规则和限定复核记录，没有复制整仓、bitstream、实录。独立样例是明确标注的虚构温度网关；临时清单测试字节自动在系统临时目录创建/清理，不是原始物理证据。
