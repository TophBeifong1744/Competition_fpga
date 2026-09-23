# Git与发布补充

规则见[team-workflow](team-workflow.md)，版本/归属见[配置](../team-workflow.yaml)。

- main为集成基线；新任务codex/<issue>-<slug>，旧返修留原PR/分支及问题ID。
- 每人默认一个checkout；脏或构建中不切换，独立复现才增最小worktree，不复制工程。
- 检查点commit，交审push准确SHA；真实非作者批准后合入，默认squash，核对组合输入和身份。不凭缺祖先关系就认定squash漏合。
- 不reset/clean/强推，不盲合旧分支，不伪造成员批准。
- 每批[batch-closeout](team-workflow.md#batch-closeout)。完成且独有材料受控才删短分支；已受控闲置checkout可以先释放，待审branch/准确提交保留可恢复。
- 9/23私有仓库保护接口403，平台强制保护未建立/未验证；不得为此擅自改套餐或公开仓库。
