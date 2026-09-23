# 2026-09-23 工作流迁移与安全清理

本次依据拓芙直接授权，停止原跨聊天功能探索，改做项目治理迁移、实际进度核对、远端任务建立、本地去重和10/7重排。不是新技术验收，不合入任何未批准产品候选。

## 1. 固定基线与新进展

迁移开始 local main / origin/main / 直接远端 main 均为 `704407e19f25a5405ef4d8f0272e977224e69b2c`，ahead/behind=0/0。共享目录保留未提交材料，用一个隔离稀疏工作树只改管理文件和按原件分发的协作工具。

- A准备包 `7274df873d6a36da8e16ca54f05688d3c7f09689` 已发布；B意见 `696d21000adfb1b39332bb35c1ae7b45d2b75227` 已发布。旧“3c04a8c未推送”不再作为待办。
- C 9/22八段已到B，诊断候选 `b5adf78fdbc66e3a0d55307971597f3ca6f63e00`：原始完整性8/8，错播连续语音，不能冒充指定chirp素材/精确真值；166 fresh为帧数不是正确独立锁定，+45第二段0 fresh。新诊断待A审。
- Skill新候选 `929d737f062adc03dbb8759aafe3584119d65b2a` 已发布待审；不覆盖旧a7e1ea9/3ac597d限定批准。
- S1入口是旧policy与已批准检查器依赖不匹配，需限定适配，不能仅改hash“放行”。16服务实际上界未知，仍REALTIME_BLOCKED。
- 既有FFT、软件闭环、DAS和节点的限定结论复用，未重跑。正式M1、完整H3、稳定定位/音频收益/整机实时未因迁移通过。

## 2. 交付与任务载体

- 配置：`team-workflow.yaml` / `workflow-lock.yaml`；外层fpga-team-workflow0.1.0原件位于`tools/fpga-team-workflow/`，不是本队竞赛Skill。
- 规则：AGENTS、team-workflow、CONTRIBUTING、Issue/PR模板；保留三交接点和六项增量复核，产品仍需合格非作者真人批准。
- A/B/C同等承担工程与复核。旧四类常驻聊天简化为每成员执行/复核两个，当前协调任务保留；用户已删除旧聊天，本次未创建新聊天、未冒称通知已送达。
- 远端已创建4个Milestone、Issue #12—#24并指派实际账号，见[创建回执](workflow-migration-20260923/github-created.json)。指派不是接单；日常状态只在Issue/PR，不要求多份md同步。
- 日期：9/25合同输入、9/29 M1/H3模块、10/3整链/独立复用、10/6冻结、10/7总验收。具体标准见[日历](../project-plan.md)。
- 旧活动阶段页退役为重定向，旧全文由[固定Git基线](../../archive/2026-09-23-before-team-workflow/README.md)恢复。原验收、B复核、任务包、生产RTL/BD/XDC/PS与两项竞赛Skill源码未改。

## 3. 实际检查及未测

[完整命令、cwd、退出码、日志与SHA256](workflow-migration-20260923/management-checks.json)；cwd为本迁移候选根。下列均为管理工具检查，不构成FPGA PASS。

| 检查 | 实际结果 |
| --- | --- |
| 外层包manifest + 原包单元测试 | 退出0；95 tests通过；0.1.0内容摘要与本机来源一致 |
| 内层依赖检查（doctor） | 0.4.0固定e40fd8000b526b72ba80373127bf5fd6e5f8dc28；40文件、13角色一致；客户端加载UNKNOWN |
| layout inspect / doctor总体 | 各退出3，INCONCLUSIVE；0结构错误，但外部one入口未绑定、适配器UNVERIFIED |
| 13项任务模型推荐 | 输出见[确定性推荐](workflow-migration-20260923/model-recommendations.json)；仅建议，实际模型UNKNOWN，未改客户端或全局配置 |
| 文档空白检查 | 自有文档检查退出0；初次全暂存检查报告原包既有双CR/行尾空白，不改写上游原件；随后仅对原包与原始txt关闭空白样式检查，仍以manifest/哈希验证，其他文件正常检查 |

本轮Python为3.14.6；386个本队改动Markdown的本地文件链接检查通过（不含上游工具与锚点验证），见[检查结果](workflow-migration-20260923/doc-links.json)。

最终暂存核对：98份分发包清单文件、10份原始日志的Git blob SHA256均一致，无产品目录改动，见[字节/范围检查](workflow-migration-20260923/staged-identity-check.json)。`git -c core.whitespace=cr-at-eol diff --cached --check`退出0。外部原件不为格式门重写；对应4份被旧ignore覆盖的工具证据log已按清单精确纳入，不新增广泛ignore豁免。

doctor观察PATH默认指向Vivado/XSim2018.3，**没有执行它们**。项目2025.2要求不变，工程任务须显式核对实际2025.2入口；本次不以PATH发现或配置通过宣称工具/工程兼容。

外层源摘要 `b226438c46b1c4b56f49d4e2c6f0d486235f8b152d9023442f04dfb7651a2f12`。上游原件保留许可/来源，导出比赛包时不把它当本队原创。B/C安装与模型能力未验证；本机安装不等于全员生效。

未执行：Vivado/Vitis工程变更、仿真产品回归、综合/实现、下载、真实DMA、采录、正式阶段验收。实际工程仍按用户操作权限，不因新工作流扩大代操作范围。

## 4. 清理结果与恢复

清理前核对注册工作树、限定C盘Codex项目目录和E盘SoundSight临时目录；检查准确HEAD、全部untracked/ignored、链接和活动EDA进程。没有遍历删除盘根、用户资料、其他项目或源工程。

- **23个**闲置干净工作树已由 `git worktree remove` 非force删除，名义文件内容合计 **28,952,973,176字节**（约28.95GB）；没有测量文件系统实际释放空间。
- **425个**共享目录未跟踪文件与保留的远端候选逐字节一致，已逐文件重查SHA256后删除；共2,265,130字节。不是提交或批准其内容。
- [工作树恢复清单](workflow-migration-20260923/cleanup.json)列每个旧名称、准确SHA和仍保留的远端引用；[逐文件恢复清单](workflow-migration-20260923/removed-published-duplicates.json)列删除文件与候选身份。需要时从准确提交新建任务分支/检出，不再恢复23套长期副本。
- 所有已有候选/长期分支和原证据提交保留；未删除旧PR #5、未合入待审代码。公开/本机原始录音和失败证据未按文件名猜测删除。

**保留项，不声称彻底清空：**

- 五个工作树仍含未提交/忽略材料：C盘 `framer-publication`（仿真含crash/backup日志）、`h3-engineering-publication`（publication-check02）、`ps-bridge-publication`与`psbr`（工程子包/原日志），E盘 `ss-b-checkpoint-bb964cb`（3个B报告/数据变化）。保留先做内容归属核对。
- E盘 `ss-*` / `fft29-coverage-01` 等非Git运行目录的独有原始日志、结果与旧备份未全部证明可再生，**本轮不删除**；不能把“看起来重复”当安全证据。
- 共享main去重后仍有 **1349个**未跟踪文件，主要是continuous调试/导出和未审framer等材料；所核对两个候选范围另有151个ignored文件，均保留。范围与去向见[本地剩余材料清单](workflow-migration-20260923/retained-local-materials.json)，不是本次遗漏待提交的管理文件。
- A-DECISIONS-20260923、CONTINUE-20260923及准备目录README不在已发布候选内，保留，不作为旧候选一并删除。
- 已不存在的旧工作树登记只读保留，不为美观清掉可能帮助恢复的引用。

保留项统一链接Issue #24，按当前任务使用，不自动发起昂贵全量复核。唯一材料先归属/受控保存，再谈进一步去重；不把它们藏进新ignore。

## 5. 发布与收尾方式

本批为用户直接决定的管理迁移，按明确授权提交到main；**不是B/C独立技术批准**，也不形成后续绕过产品PR审批的先例。真实仓库private；读取main保护接口返回403套餐限制，未配置或声称服务端强制审批，不购买套餐、不公开仓库。

发布后在实际共享main快进并核对local/origin/直接remote与ahead/behind；准确最终SHA和本批材料结果追加到[迁移Issue #12](https://github.com/TophBeifong1744/Competition_fpga/issues/12)，避免在提交内反复追写自身SHA。本页是操作/证据快照，动态任务状态仍在GitHub。无权或无法同步时不得写收尾完成。
