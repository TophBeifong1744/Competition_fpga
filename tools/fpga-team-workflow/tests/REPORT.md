# Skill 验证报告 — 0.1.0

依据生成指导 v1.2.0 的 72 场景编制。测试对象是本包协作规则和脚本，不是用户产品工程。
本轮自动测试：**95 项，失败 0，错误 0**。
执行：`python -B work/run_acceptance.py`（本次记录器）；可重现等价入口：
`python -B -m unittest discover -s tests -p "test_*.py" -v`。
原始结果：[JSON](evidence/acceptance-results.json)、[日志](evidence/acceptance.log)。

包验证命令：`python -X utf8 -B <skill-creator>/scripts/quick_validate.py <package>`。
Windows 默认 GBK 导致该校验器首次解码失败；显式 `-X utf8` 后通过，未修改系统校验器。

上游依赖：0.4.0 / e40fd8000b526b72ba80373127bf5fd6e5f8dc28；本机 40 文件（13 角色）SHA-256 全部匹配。
工具实测：独立目录中 XSim 2018.3 xvlog → xelab → xsim 全部退出 0，运行到 1 ns 并输出完成标记；仅 DIAGNOSTIC_ONLY。
独立 AI 试用：[初次试用](evidence/forward-test.md)、[最终复测](evidence/final-retest.md)、[实际 fpga_architect 调用](evidence/architect-call.md)。这些不是人类成员批准。

## 72 场景结果

**PASS 的范围写在证据栏**：fixture/脚本或有记录的行为测试。它不外推到真实 GitHub 权限、
其他操作系统、完整厂商工程、实际成员批准、系统/板卡或模型性价比。未执行的上线验收另列在后面。

| ID | 结果 | 场景 | 本次证据与限制 |
|---|---|---|---|
| A01 | PASS | 两人团队执行一包并独立复核 | fixture：test_A01_two_members_no_third_signer；真实多人账号接收 NOT_RUN |
| A02 | PASS | 六人或更多成员并行不同模块 | fixture：test_A02_six_members_no_all_sign；真实多人账号接收 NOT_RUN |
| A03 | PASS | 只有作者可用 | fixture：test_A03_only_author_cannot_approve |
| A04 | PASS | 只查询状态或提计划 | fixture：test_A04_readonly_recommendation |
| A05 | PASS | FPGA 工程任务 | 独立试用实际读取本机内层并调用 fpga_architect；ANALYZE/PREFLIGHT，未签工程验收 |
| A06 | PASS | 上游角色缺失／版本不兼容 | fixture：test_A06_missing_roles_fail_closed |
| W01 | PASS | 同一成员串行两个工作包 | fixture：test_W01_serial_reuses_checkout |
| W02 | PASS | 模块任务存在公共 include／package／IP 依赖 | fixture：test_W02_dependencies_and_instructions_retained |
| W03 | PASS | 收窄范围前有独有忽略数据／未提交文件 | fixture：test_W03_dirty_and_ignored_protected |
| W04 | PASS | 正在运行 EDA 时请求切换分支 | fixture：test_W04_active_eda_blocks_switch |
| W05 | PASS | 需要真正并行构建 | fixture：test_W05_parallel_worktree_has_separate_output |
| W06 | PASS | 清理路径包含链接／junction／未知文件 | fixture：test_W06_cleanup_rejects_traversal_and_unknown |
| W07 | PASS | 中文、空格路径及声明支持的平台 | fixture：test_W07_unicode_space_snapshot |
| D01 | PASS | 有已核实目标的新项目初始化 | fixture：test_D01_init_no_fake_vendor_entry |
| D02 | PASS | 旧工程使用 docs/、fpga/prj/ 等非默认路径 | fixture：test_D02_existing_mapping_preserves_files |
| D03 | PASS | native_project 的 par 中含 .xpr／.srcs 自有源码 | fixture：test_D03_native_inputs_protected |
| D04 | PASS | script 重建遗漏初始化文件、配置或外部源码 | fixture：test_D04_missing_initialization_detected |
| D05 | PASS | 锁定 IP、缺旧版仓库或外部不可再生 DCP | fixture：test_D05_locked_ip_explicit_dependency |
| D06 | PASS | 手工 wrapper 与自动生成 wrapper 同时加载 | fixture：test_D06_duplicate_wrapper |
| D07 | PASS | 忽略规则误伤 .mem／.xci 等输入，或放过大缓存 | fixture：test_D07_ignore_reverse_and_tracked_output |
| D08 | PASS | 映射含路径越界、未知 junction、源与输出重叠 | fixture：test_D08_paths_and_overlap |
| D09 | PASS | 配置映射存在，但上游／桥接器仍仅支持标准布局 | fixture：test_D09_mapping_not_build_proof |
| D10 | PASS | 授权仅接入旧项目，或迁移中检测到未保护变更 | fixture：test_D10_no_implicit_migration |
| D11 | PASS | 多任务提交相同整工程副本或把 Skill 包混入每个任务 | fixture：test_D11_duplicate_active_sources_in_compile_view；只检查实际编译视图中的重复来源，不扫描全仓所有副本 |
| D12 | PASS | 选择不同正式目标，且它们引用公共源码 | fixture：test_D12_targets_require_selection_and_separate_outputs |
| G01 | PASS | 连续修改并跑三次局部测试 | fixture：test_G01_snapshots_without_commits |
| G02 | PASS | 正式交付时新增文件尚未跟踪 | fixture：test_G02_new_required_input_not_tracked |
| G03 | PASS | PR 已合并但 Issue 判据仍需板测 | fixture：test_G03_merge_not_board_acceptance |
| G04 | PASS | main 更新或合并冲突产生新代码 | fixture：test_G04_new_combination_and_stale_review |
| G05 | PASS | 无配置分支保护权限 | fixture：test_G05_no_platform_protection_claim；真实 GitHub 权限不足事件 NOT_RUN |
| R01 | PASS | 稳定版本和完整可信仿真证据 | fixture：test_R01_reuse_candidate_not_retest |
| R02 | PASS | 源码未变，但关键假设／参考被证明错误 | fixture：test_R02_assumption_change_invalidates_same_hash |
| R03 | PASS | 饱和需求、实现与参考都采用回绕 | fixture：test_R03_shared_wraparound_error |
| R04 | PASS | checker 从未触发或接受了错误数据 | fixture：test_R04_zero_activity_and_bad_checker |
| R05 | PASS | 接收人需证明环境可复现 | fixture：test_R05_reproduction_is_purpose_bound |
| R06 | PASS | 原始证据链接失效或只有作者电脑路径 | fixture：test_R06_missing_raw_report |
| R07 | PASS | 非作者接手修改了产品或验收资产 | fixture：test_R07_contributor_cannot_self_sign |
| R08 | PASS | 纯文档范围 | fixture：test_R08_document_handoff_no_eda_commands |
| R09 | PASS | 相同失败循环三轮后重开工作包 | fixture：test_R09_original_repair_budget |
| S01 | PASS | 所有模块任务通过但端到端失败 | fixture：test_S01_system_failure_blocks_stage |
| S02 | PASS | bit／XSA／ELF 不匹配或板卡身份不明 | fixture：test_S02_artifact_mismatch |
| S03 | PASS | 明确只授权仿真却请求下载／Flash | fixture：test_S03_no_hardware_action_interface |
| U01 | PASS | 用户只是说“这里可以改进” | fixture：test_U01_feedback_proposal_only |
| U02 | PASS | 配置问题被误归为全局 Skill 缺陷 | fixture：test_U02_minimal_layer_and_candidate |
| U03 | PASS | 更新包有用户自定义同名文件 | fixture：test_U03_unmanaged_custom_destination |
| U04 | PASS | 预览后安装基线被改变 | fixture：test_U04_stale_preview |
| U05 | PASS | 安装中途故障 | fixture：test_U05_failure_restores_consistency |
| U06 | PASS | 回退时发现用户后续修改 | fixture：test_U06_rollback_protects_later_edits |
| U07 | PASS | 升级上游改变角色／证据 schema | fixture：test_U07_unknown_evidence_schema |
| U08 | PASS | 更新后请求弱化验证或取消授权 | fixture：test_U08_modified_package_rejected；候选的语义退化仍须非作者审查，manifest 不是审核签名 |
| U09 | PASS | 成员安装新版，另一个成员仍旧版 | fixture：test_U09_local_scope_only |
| U10 | PASS | 安装相同包两次 | fixture：test_U10_idempotent |
| M01 | PASS | 任意新工作包，包括纯脚本或人工活动 | fixture：test_M01_automatic_and_nonmodel |
| M02 | PASS | 已有可信脚本的固定仿真／构建执行 | fixture：test_M02_fixed_execution |
| M03 | PASS | 同样标题为“仿真”，实际需设计 checker／独立参考 | fixture：test_M03_checker_activity_over_title |
| M04 | PASS | recommend_only 或用户明确保留当前模型 | fixture：test_M04_recommend_only_has_no_write |
| M05 | PASS | 提示词写了模型名，或用户手报设置但无运行观测 | fixture：test_M05_observation_sources |
| M06 | PASS | 推荐模型在官方目录存在，但成员账号不可用 | fixture：test_M06_unavailable_actor |
| M07 | PASS | 主会话 Sol，子 Agent 文件锁定 Astra／其他 effort | fixture：test_M07_role_override_not_runtime |
| M08 | PASS | 模型不支持某 effort，或把“极高”误映射到 Ultra | fixture：test_M08_effort_validation |
| M09 | PASS | 局部任务扩展到跨层故障且持续无新诊断 | fixture：test_M09_escalation_keeps_budget |
| M10 | PASS | 作者和参考共享错误假设，但高档模型也说通过 | fixture：test_M10_counterexample_stops_vote |
| M11 | PASS | 为降低模型成本请求跳过必要专项、终审或真实复核 | fixture：test_M11_no_model_bypass |
| M12 | PASS | 更换模型／重开会话后要求重新计算失败轮数 | fixture：test_M12_model_change_keeps_stop |
| M13 | PASS | 只换分析模型，受控工程输入和工具均未变 | fixture：test_M13_model_only_change_keeps_eda_identity |
| M14 | PASS | 强模型已做完决策，后续仅短脚本步骤 | fixture：test_M14_short_script_does_not_apply |
| M15 | PASS | 缺硬件、数据、权限或实际合同 | fixture：test_M15_conditions_not_guessed |
| M16 | PASS | 用户提出模型策略更新，或已有推荐版本过期 | fixture：test_M16_policy_version_is_separate |
| M17 | PASS | 旧配置没有 model_policy，或策略 schema 未知 | fixture：test_M17_legacy_and_unknown_schema |
| M18 | PASS | 没有用量数据，或只有 API 价格与订阅限额 | fixture：test_M18_unknown_usage_null |
| M19 | PASS | 只测简单成功案例，或不同模型使用不同验收标准 | fixture：test_M19_cannot_fake_calibration |
| M20 | PASS | 受授权应用遇接口失败、配置冲突或无法确认生效 | fixture：test_M20_apply_is_explicitly_unsupported |

## 额外回归和修复记录

- 首轮 86 项有 3 项同根因失败：Git 不存在分支的查询退出码。改用 `rev-parse --verify --quiet`，相关实际分支/sparse/worktree 操作随后通过。
- 补充跨基准依赖、大小写自签、撤销 review、清理依赖保护、项目锁不匹配和真实 1.0.0 原生证据矛盾测试。
- 独立试用发现安装收据损坏仍被 verify 放行；补收据身份、版本、内容和事务检查，并新增 test_corrupt_receipt_fails_verification。
- 安装故障注入覆盖备份后/切换后失败；模拟中断后 recover 恢复一致状态；用户后续改动阻止回退。

## 交付范围和未运行项目

- 已实现：本地可安装包、规则/模板、推荐、检查/执行辅助脚本、受控候选维护和事务回退。
- 已测试：Windows 临时仓库/中文空格路径、安装保护/回退、策略/证据负例、独立 AI 试用、实际内层角色与 XSim 诊断入口。
- NOT_RUN：两个真实成员用 GitHub 交付/批准/合并、平台分支保护、全新用户任务自动发现、其他平台、完整工程重建、CDC/STA/板测、真实模型成本质量校准。
- UNSUPPORTED：跨客户端自动模型应用、可信运行配置观测 adapter、跨机器互斥、自动迁移/删除执行器、全部上游证据 schema 的完整语义验证。
- 发布状态：本地候选交付；没有远端 tag/Release、没有替真实成员批准。全新会话加载和团队采用按 README 完成。
