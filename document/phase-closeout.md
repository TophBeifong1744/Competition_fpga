# 每次阶段验收的收尾

适用9/10及以后所有正式阶段。当前日期只看[统一日历](project-plan.md)，原快照按实际日期原样保留。9/23治理迁移不是技术验收。

1. 固定阶段集成SHA/工具/合同，分列已批准、作者自测、待审和未完成；包完成不等于系统完成。
2. 按批准准确范围将需长期维护的源码/测试接入project/rtl、simulation/tb、simulation、models、software等唯一活动入口；诊断结果按[总结与必要原件](git-workflow.md#failure-retention)留档，不要求保留完整失败现场，不强搬、不夹带未审代码。
3. 最终加载位置作相称验证，记录实际/复用/未测。索引变化不重跑全套；接口/约束/工具/冲突变化按影响补测，约定系统与长稳判据不减免。
4. deliverables/phase-YYYY-MM-DD保留最小快照、证据索引、CLOSEOUT.md：批准、源→活动路径、命令/结果、未接入原因/owner、版本和回退。正式发布按[Git管理流程](git-workflow.md)绑定准确候选、带注释Tag/Release、构建配置及匹配产物；未达到验收标准的候选明确测试/预发布状态。不复制另一套活动工程，不倒填旧记录。
5. 阶段Issue记录裁决和发布；真实非作者批准后由获授权成员合入，不必仅复核人点击。核对实际共享main/origin/remote与本批modified/untracked/ignored材料，再按[清理规则](generated-artifacts.md)处理闲置副本。

GitHub为权威，不强制多份md抄同一进度。发布收尾限本批，不每次全仓整治。缺板测/独有材料则如实部分完成；归位/merge不代表实板、整机或阶段PASS。精细非阻塞风险不因收尾重新变成开工门槛。
