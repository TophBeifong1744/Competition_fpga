# SensorBridge 工作流迁移演练输出 v02

本演练的结论是：A 可以继续包内开发，B 可以立即提交限定范围的准入复核，C 可以开展诊断但不能宣称精度及无中断通过，D 不得由作者助手合入未审 r5，已发布批次仍待收尾。

## 可见评估请求（逐字）

> You are an isolated workflow evaluator. Read ONLY E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-A-SKILLS/payload/skill/soundsight-engineering-workflow/SKILL.md and its linked README/record templates if needed, plus task-packages/PKG-A-SKILLS/evidence/migration-input.md in that repo. Use that Skill to actually answer requests A-D from the input, in Chinese, as a practical engineering handoff. Do not inspect other project docs, active Skill, acceptance-plan or other evaluators. No internet, Git, implementation or hardware actions. Your only write is task-packages/PKG-A-SKILLS/evidence/migration-v02-output.md via apply_patch. Include the exact visible evaluator request (this message) and your answer, source paths/SHA256 and checks actually performed; no hidden reasoning. Treat input state as fictional, never actual remote observation. This is a workflow-use exercise, not a review of the Skill or human technical approval. Return output path and concise result.

## 适用边界与输入

以下交接仅使用虚构 SensorBridge 输入。文中的工程师身份、测试通过、采集记录、审查批准和远端状态均是题设事实，不是本次实际执行或观测。本文没有代签人工技术批准，也没有发送复核消息。证据编号 A/B/C/D 对应 migration-input.md 的 Request A/B/C/D。

### A：Lin 的下一步开发交接

Lin 现在继续 sensor-draft-2 的 CSV 解析器和 TB 包内开发；电源及引脚未知只阻止依赖这些信息的接板工作，不阻止已获授权的软件工作。

1. 在现有工作包内固定 sensor-draft-2：t0/t1 列顺序、signed int16 代码、uint64 sample_id、acquisition_id 重启分段、schema_version、error_flags，以及单位为 code。探头映射和标定字段保留版本及“暂定/未知”状态，不能转换成未经标定的摄氏度。版本变化应显式识别，不静默按新定义读取旧数据。
2. 编写或续写解析和自检 TB，覆盖 int16 的 -32768/32767、正负号、越界、缺列/坏字段、schema_version 不匹配、sample_id 大整数及编号间断、acquisition_id 改变后的重启分段和错误标志传播。错误行及原始编号应可追溯；不得先删掉断点再宣称输入连续。
3. 生成明确标为整数模式的输入及预期输出，在包内保存原始向量、配置、运行入口、日志与首个不一致位置。记录实际使用的工具和版本；题设中的 xc7a35tcpg236-1、2025.2 是已知目标信息，不代表本次已经运行工具。
4. 向现有交接入口提交同一完整工作包的增量结果与未覆盖项。本题没有指定 A 的复核人或包内具体目录，沿用团队已有目录与指定角色，不自行扩大路径权限。

必须等待：板卡供电电压、实际引脚及连接依据确认后，才可讨论相应硬件连接；不得生成可部署的猜测 IO 约束或接板。活动目录集成未获授权，不能覆盖活动源码。温度物理精度、探头映射及系统硬件能力验收等待相关真实证据。当前开发验证均尚未执行，记 NOT_RUN；集成授权和上述板测判定为 BLOCKED，不能据此把包内开发也标成全局 BLOCKED。

### B：提交 Lin 的 r4 限定准入复核文本

复核请求草稿：请指定复核人 Lin 对 Sam 的 CRC/范围筛查模块 r4 进行原型准入复核。申请范围仅为该版本模块在明确输入输出接口下的原型接入，目标活动路径和准确内容哈希应绑定到实际提交包；本文没有收到该哈希或目标路径，不虚构。请核对固定格式、单位/符号、有效性及错误处理、golden 和边界/错误向量、数值范围/溢出行为，以及调度、缓冲和数据搬运预算。Lin 尚未作出决定，当前状态为“作者提供测试结果，待指定复核人判断原型准入”。

已提供材料可以支持现在开展复核：列明向量的仿真通过；单包 64 cycles，拟定时钟 50 MHz，256-byte 缓冲和输入 1 kpacket/s。按题设预算推算，纯模块计算时间为 1.28 μs/packet，输入平均间隔为 1 ms，计算占空约 0.128%。这些是理想周期预算推算，未计入完整系统的竞争、突发、阻塞和搬运，也未证明 50 MHz 能在实现后满足时序。256-byte 缓冲是否足够仍需结合包长、突发和背压机制核对，不能仅凭缓冲数字认定通过。

| 证据或判据 | 题设支持的状态与范围 | 缺项影响 |
|---|---|---|
| 已列向量的仿真 | PASS，仅引用作者题设结果；未提供日志及仿真类型，本次没有独立复跑 | 不能宣称独立复核通过，也不能自行扩成完整 RTL 仿真覆盖 |
| 模型或独立参考验证 | 未提供对应独立记录，NOT_RUN（本次） | golden 的存在不等于已执行独立模型验收 |
| 综合、实现、时序 | 最终实现/时序报告缺失；本次均 NOT_RUN，时序通过判定 BLOCKED | 不支持最终资源、时序收敛或整链实时通过；不妨碍先评估有限原型准入 |
| 板测：标定与长稳定性 | 对应报告缺失，能力判定 BLOCKED；本次板测 NOT_RUN | 不支持物理测温精度或真实长稳结论 |
| 原型准入决定 | BLOCKED：待 Lin 对准确版本与限定范围作决定 | 不把作者仿真或本文建议当作准入批准 |

本次只形成可提交的复核请求。Sam 负责补齐现有包内的内容标识、入口和预算依据；Lin 负责复核与明确批准/拒绝范围。缺少最终时序、标定或长稳不是禁止全部研究的理由，仍不能据此承诺未测实时性能。

### C：早期诊断和可使用的性能表述

可以现在诊断连续片段的格式与代码幅值，无需等待长稳验收。探头映射和标定未知限制物理解释，并不阻止读取 signed code 或查编号断点。本文没有原始采集文件，也没有执行新测量、解析或仿真，不能声称已经完成诊断。

后续诊断沿用原始 400 行、sample_id 与断点标记，保留 acquisition_id、通道顺序、schema_version、error_flags、技师声明的来源和采集点。缺失的原件哈希、实际来源/采集点元数据应向原交付核对，未知项保持未知。派生连续片段须能回溯原始行，不重排编号、不填补断点后称作原始连续记录。0.4 秒、配置 1 ksample/s 和 400 行不能单独证明实际采样时间连续，也不能据此反推精确丢样率。

| 判据 | 结论 |
|---|---|
| 独立的 100 个合成向量测试 | 题设 PASS，分母为 100，仅支持这些合成用例；不属于硬件测温精度证据 |
| 真实采集的格式/幅值诊断 | 可开始；本次 NOT_RUN，不能提前填 PASS |
| 温度物理精度 | BLOCKED：映射/标定未知，未记录经标定的参考温度计；没有精度结果不等于测得准确率为零 |
| 本记录的编号连续性 | 按题设为 FAIL：存在一个明确保留的缺失区间；中断发生在传感、传输还是记录环节仍未知 |
| 传感器无中断运行及长期稳定性 | BLOCKED：该短记录及已知断点不足以证明，不能把记录缺口直接定性为传感器本体故障 |

可用报告文字：

> 技师声明提供一份 0.4 秒、双通道、配置采样率为 1 ksample/s 的硬件采集，共 400 行，保留并标记了一个编号缺失区间。现有连续片段可用于格式和代码幅值诊断，尚未在本次执行该诊断。另有 100/100 合成测试向量通过。由于探头映射、标定及参考测温记录缺失，目前不能判定传感器准确度；该记录也不支持无中断运行或长期稳定性通过。

后续若开展精度或长稳验收，须先固定相应判据并取得匹配证据；本次不新增测量任务，不把合成用例改称板测。

### D：版本处置及已发布批次收尾交接

拒绝执行作者助手合并 r5 的请求：审批记录仅将 r4 的 aaaa 批准为研究归档，aaaa 是夹具标识而非真实 SHA。r5 已改变接口且未审，旧的一般 Git 权限不能替代准确版本的技术复核，也不能赋予作者侧助手自批、自合权限。r4 的归档批准同样不授权活动算法替换。

| 对象/动作 | 去向与所需权限 | 本次状态 |
|---|---|---|
| r4 / aaaa | 按已有批准保留在指定研究归档，绑定原批准记录及范围；目标实际路径由现有交接记录确定 | 归档批准仅按题设引用，不扩成生产接入或系统通过 |
| r5 接口变更 | 保留在现有工作包；交项目指定复核人重审接口、预算、golden 和接入范围，并锁定准确内容 | 等待复核；无合并。D 未指定具体复核人，不借用旧例姓名代签 |
| r5 后续合入/发布 | 获准确版本与目标批准后，由指定复核人或获授权发布负责人执行，并验证新位置入口 | 旧泛化 Git 授权不足以单独完成此步 |
| 已批准但被 ignore 遗漏的原始 .bin | 保留原件并定位到该批已批准的交付目的地；核对发布范围和权限后补充纳入，必要时仅对这个文件作显式纳入 | 不以忽略规则掩盖遗漏；本次不改 ignore、不补推 |
| 新的未审 parser | 保留其内容和来源，在已有授权下进入待审任务分支/现有包 | 不混入已批准 r4 批次；没有建分支权限时仅记录待负责人处置 |
| 无关工程师的未完成文件 | 留在其工作位置，记录责任人和与本批无关的差异 | 不清零、不覆盖、不当作本批垃圾删除 |
| 再分发权限未知的 vendor 文件 | 暂不公开发布；在获准受控位置保留原件，登记哈希、用途、责任人和恢复方式，向资料权利负责人核实权限 | 暂存受控原件不是批次收尾完成；权限未明则保留待处理项 |

对已发布 r4 批次只能写“已发布；批次收尾待处理”。L、T、R 不一致以及上述材料去向未落实，使本批不能标为 closed。这里的 L/T/R 完全来自虚构快照，不是本次查询到的实际共享目录或远端值。

下一交接给该批获授权发布负责人：在取得本次演练之外的实际操作授权后，检查真实共享目录的 local main、tracking main、直接查询的 remote main 及 ahead/behind，逐项核对本批已修改、暂存、未跟踪和被忽略的有用文件。差异原因先查明；不能重置脏目录来制造一致。完成被批准遗漏的补充发布后再核对三方状态和材料清单；不能安全同步时记录差异、负责人及下一步。未审代码与其他成员工作继续保留，受控资料按权限处理；仅完成明确获准、可恢复且无独有证据的副本清理。没有这些后续真实结果就不宣布收尾完成。

## 来源路径、SHA-256 与实际检查

所有路径基于 E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/。

| 实际读取的来源 | SHA-256 |
|---|---|
| task-packages/PKG-A-SKILLS/payload/skill/soundsight-engineering-workflow/SKILL.md | 6DE6F3066F94D6BB681395ED725B075EE1A113F666E267051695D03139F594BE |
| task-packages/PKG-A-SKILLS/evidence/migration-input.md | DDA66E02E84F349665A8C3DF1FE5724F7D949D6A17B1C2555DEF4338235F3DE6 |
| task-packages/PKG-A-SKILLS/payload/skill/soundsight-engineering-workflow/references/record-templates.md | 908394FCF9E21CA7BC685FDAD98D5D8D8CA84DF0D1DF26962F80637B8C90158A |

实际检查：对以上三个允许来源执行 Get-Content -Raw -LiteralPath 完整读取，执行 Get-FileHash -Algorithm SHA256 -LiteralPath 计算源文件哈希，均成功。按模板的动作判断、证据边界及准确版本发布字段组织交接；仅使用题设数字作预算算术，未运行工程工具。未读取链接 README，因为本题所需记录模板已足够；未读取其他工程文档、活动技能、acceptance-plan 或其他评估结果，也未使用记忆。

唯一写入：通过 apply_patch 新建 task-packages/PKG-A-SKILLS/evidence/migration-v02-output.md。未修改源码、向量、工程配置、原始输入或审批记录。未执行网络、Git、仿真、综合、实现、板测、消息发送或人工技术审批。本文产物是 A–D 工作交接回答，不是 Skill 评审或功能验收结果。
