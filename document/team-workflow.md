# SoundSight 团队工作流

生效：2026-09-23。采用用户指定的fpga-team-workflow 0.1.0；替代旧固定四类聊天和多层任务包转交。完整规则使用锁版本Skill，不在这里再复制一份。配置唯一入口：[team-workflow.yaml](../team-workflow.yaml)；版本：[workflow-lock.yaml](../workflow-lock.yaml)。

## 日常最短闭环

1. 在[Issue](https://github.com/TophBeifong1744/Competition_fpga/issues)认领当前完整工作包，核对owner/reviewer、准确基线、完成定义与授权。
2. 默认复用一个活动checkout，任务开始建短分支；小实验连续做，有价值检查点commit。真实工程按锁定内层Skill执行，不另造重复技术角色组。
3. 正式交审推送准确SHA；PR给一页范围、原合同、实际/复用/未测与原始证据。纯数据在Issue交付，不造空PR。
4. 非作者先独立核对前提，再审差异/证据，决定必要补测；真实成员对准确SHA和范围批准。
5. 获授权集成人合入准确范围并作相称验证；本批收尾完成才清理停用副本。仍待板测/完整定义时Issue保持打开。

作者完成、成员接收、系统阶段通过三种结论分开。main可以集成已批准模块，不能借此宣布整机通过。

## 三人和聊天

A采集/PS/PL/集成，B算法/定点/golden，C外设/驱动/采录/系统测试；三人同一质量与授权规则。C可以写RTL/软件、设计方案和做合格独立复核，不再限为按单操作。

当前聊天作为项目协调；每人默认两个任务：执行（plan/work/integrate）和复核（review）。外包也是Issue工作包，不强制多开一个聊天。长工程上下文确有需要才从执行任务拆工程专项，写入所有权不重叠；不为13个内层角色开13个常驻聊天。具体首轮任务和可复制提示词见[启动指南](chat-start-prompts.md)。

## 权威事实与版本

任务/阶段以[Issue](https://github.com/TophBeifong1744/Competition_fpga/issues)及[Milestone](https://github.com/TophBeifong1744/Competition_fpga/milestones)为准；源码/合同在唯一受控路径；实际运行在原生证据；批准在真实GitHub事件或可核对的既有成员报告。旧报告继续按原准确范围复用，不倒造GitHub review。

本地状态页是标注日期的核查快照和入口，不要求每次动作同步多份md。旧任务包/分支不是另一套活动源。历史PR #5与其他旧候选由[保留项](https://github.com/TophBeifong1744/Competition_fpga/issues/24)按证据处理，不能因未合并就盲合入。

<a id="review-efficiency"></a>
## 增量复核与降耗

保留六项规则：首次完整审申请范围；返修只审差异和受影响回归；脚本执行/摘要优先；合并后相称验证；单一交付入口；完整包交叉复核并把技术判断与发布收尾分开。

复用时检查合同/前提、源码/输入/参数、checker/golden、工具及真实入口，写“复用，未重跑”。参考错误或checker未真正执行会使旧PASS失效；不能只看退出0。新补测说明消除何种不确定性。确定错误足以阻断时集中反馈，不继续无关昂贵回归。同一问题最多三轮自动返修，连续两轮无进展停止。

<a id="batch-closeout"></a>
## 每批发布后的本地与远端核对

在**实际活动共享目录**读取local main、origin/main、直接远端main及ahead/behind；有并发远端变化先复核，不强推。检查本批modified/untracked/ignored材料，逐项已入main、待审分支或可恢复受控存储；不是把资料藏进.gitignore。其他未完成工作保留，无法安全同步说明原因/责任人。

本轮授权采用最少副本，不自动为发布新建worktree；脏共享目录/独立验证确需隔离时才例外。清理规则见[文件保留](generated-artifacts.md)。阶段收尾另见[phase-closeout](phase-closeout.md)。

## 安装与工程依赖

分发源：[tools/fpga-team-workflow](../tools/fpga-team-workflow/README.md)，逐字节保留0.1.0、manifest与来源说明；这是协作工具，不是本队SKL-001/002。源码包散列见锁文件。B/C自行安装到自己的用户Skill目录，安装前读包README/CLI并先verify和install-plan；不把本机安装状态推及全员。

工程依赖run-fpga-workflow 0.4.0固定e40fd8000b526b72ba80373127bf5fd6e5f8dc28，必须完整安装Skill和13角色，不只拷SKILL.md。A本机40文件/13角色已核对一致；B/C未核对。实际工程入口existing映射仍UNVERIFIED；检查器结构通过不是Vivado/板级兼容通过。

## 模型与平台限制

每包用现有CLI自动推荐，配置仅在team-workflow.yaml:model_policy；实际设置UNKNOWN就如实记录，不能伪造切换。升级/降级按具体风险，不按每个命令切模型；不修改上游角色或计费。三人成员批准仍保留。

本仓库为私有仓库；9/23读取分支保护接口返回403（套餐限制），未宣称平台已强制至少一人批准。采用流程约束，并在权限允许时配置平台保护；不为此购买套餐或公开仓库。治理迁移可依据用户本轮直接决定发布，但不替任何产品批准，不作为以后绕过PR复核的先例。
