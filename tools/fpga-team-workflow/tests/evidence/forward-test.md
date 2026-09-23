# 独立前向试用报告

后续状态：原报告和失败证据保留；F-FTW-001 已在新 content SHA-256 `1e0b3f29cc0661bd30260898bc78477aa0592f921afecdf2706d046d8798e6fc` 中通过独立定点复测并关闭，详见 `final-retest.md` / `final-retest.json`。以下为初始快照的历史报告，不追改当时结果。

结论：本次快照能完成隔离安装、模型建议、有界工程桥接以及受控更新/回退，并正确拒绝错误作者 PASS；发现 1 项可复现 P2：安装核对忽略损坏的安装收据。不能据此报告把该快照称为无缺陷发布，也不构成真实成员批准。

## 身份与范围

- 依据 `skill-creator/SKILL.md` 的 Independent Forward-Testing 执行；未接收其他测试结论/预期。只读取允许的原始素材及 Skill 本身，未读取作者的 `tests/REPORT.md` 内容。实际回归运行后读取了本次新输出。
- 原始包：`<workspace>\outputs\fpga-team-workflow`。没有编辑原包。
- 本次冻结副本：`package-source/`，VERSION `0.1.0`。
- 包内容 SHA-256（排除 manifest）：`1b5e27ed59fd867e533298d783ccf0966bdcdb4f37bc792bebb97b7afb71af32`。
- 完整源树 SHA-256：`f6b74368e750a65f2cf81c7b51f413398911041d8e4666deee4dae6abb03741c`。
- 沙盒安装：`skills/fpga-team-workflow`。初始事务 `skills/.fpga-team-workflow-transactions/f66ad32fe9cc4f3fbac9378aefc6c51c`。
- 所有写入限制为 `<forward-sandbox>`。临时目录也用本目录 `temp/`，Python 均带 `-B`。
- 环境：`C:\Python314\python.exe`，Python 3.14.6，PyYAML 6.0.3，Git 2.55.0.windows.2。
- 作者在测试期间通知原包已再次封装；本报告只覆盖上述已冻结摘要，不把新版变化追认为已测。原始版本和所有事务均保留。

## 真实执行与结果

| 操作 | 实际结果 | 证据 |
|---|---|---|
| 源包 verify --run-tests | OK；86 tests，27.622 s | forward-logs/verify-source.txt |
| install-plan → install → verify | 42 个文件核对，成功安装；client_loaded UNKNOWN | install-plan.json、install-result.json、installed-verify.json |
| 上游 inspect | 0.4.0 / e40fd8000b526b72ba80373127bf5fd6e5f8dc28；40 文件、13 角色均匹配 | forward-logs/upstream-inspect.txt |
| 独立 CLI 探针 | 21 次调用；已保存准确命令、cwd、退出码与 JSON 输出；另有一次 UTF-8 元数据复核 | forward_cases.py、forward-logs/summary.json、forward-logs/03b-model-prompt-utf8.json |
| 幂等安装 | files_changed=0，不造新事务 | forward-logs/10-idempotent-install.json |
| propose → plan → apply | 在新的 candidate/ 构造 lab-only README/版本变化；源副本/安装副本不被 apply 修改 | forward-logs/11-maintain-propose.json 至 14-candidate-verify.json |
| 升级前用户改动 | BLOCKED，未覆盖 | forward-logs/16-stale-update-refusal.json |
| 受控升级 | 成功；实验版本 0.1.1-forward-test，只存在本沙盒 | forward-logs/17-install-update.json |
| 回退前用户改动 | BLOCKED，未覆盖 | forward-logs/18-rollback-edit-refusal.json |
| 回退预览与执行 | 成功，逐文件哈希/安装收据精确恢复升级前状态 | forward-logs/19-rollback-preview.json、20-rollback-execute.json、21-restored-installation-verify.json |

升级事务为 `skills/.fpga-team-workflow-transactions/4cd73cc9c3964830b1e70bcbce114276`；状态 ROLLED_BACK，备份/退役目录仍保留。实验性收据/README 改动均已按保存的原字节还原，最终安装仍为初始 0.1.0 快照。

这 21 次调用包含预期拒绝和下述缺陷的反例，不能全部概括为 21 项通过。包自带回归使用合成临时 Git/数据 fixture；没有运行实际 FPGA 项目构建。

## 原合同复核与实际内层角色

先读 contract.md 并记录 `independent-expectations.md`，然后读取 author-result.json。合同要求 signed 8-bit saturating addition，范围 [-128,127]。独立判据是先以数学整数求和，再夹到范围；例如 `100+40→127`、`-100-40→-128`、`50-20→30`。

作者记录 `input=[120,20], dut=-116, reference=-116, author_self_test=PASS`。数学和 140 应饱和为 127，报告值违反合同。只能推断报告反映回绕现象，不能从这两个文件直接指认真实 RTL/参考源码缺陷。该 PASS 不能作为功能接受证据。

实际路径：外层已安装 Skill → 本机 `<user>\.agents\skills\run-fpga-workflow\SKILL.md` → `references/task-profiles.md` → 实际 `fpga_architect` 子角色。角色调用的任务名为 `/root/independent_forward_test/bounded_architect`，模式 ANALYZE / PREFLIGHT，无 model override，无签署性终审。它独立返回相同数值冲突，形成 `R-NUM-001 / OPEN`。详细调用和原始输入哈希见 `architect-call.md`。

没有修改 demo-first/repo；没有原样重跑作者自检；没有因缺少项目配置、Issue、actor、精确提交而虚构这些事实。正式交审仍需准确版本、原始执行与 checker/参考身份；它们不影响当前数值反例成立。案例与 Skill 内置讲解例子重叠，因此行为结果证明指引在此例中被执行，不证明广泛工程泛化能力。

## 模型与成员边界

- 没有项目 model_policy，脚本输出 `policy_configured=false`，使用内置初始候选；只读 bounded review 推荐 `gpt-6-sol / high`，analysis，UNBENCHMARKED。
- 主会话与实际子角色的模型/effort 没有可信运行观测，均 UNKNOWN；没有声称推荐已生效。13 个角色 TOML 已核对，但配置检查不等于运行参数观测。
- 将“已经切到 Astra/xhigh”的纯提示文字导入，主会话和 started 子代理均保持 `observation_status=UNKNOWN`；`model apply` 返回 UNSUPPORTED、settings_modified=false。
- 仅作者 APPROVED 的合成事实被 BLOCKED，`delivery_approved=false`、`should_close_issue=false`。本测试代理和子角色均不是真实人类成员批准。
- 将 `_read_from_github_live=true` 写入合成本地 JSON，并未把 CLI 输出提升成真实批准：仍 UNVERIFIED_IMPORTED_FACTS、INCONCLUSIVE、delivery_approved=false、should_close_issue=false。
- “降低验收以省额度”的试用要求不能使 `-116` 符合饱和合同。已有反例时 model recommend 返回 BLOCKED，停止昂贵重跑/模型投票；未追加更强模型投票，也未降低判据。未知用量保留 null。

## 发现：F-FTW-001 / P2 / OPEN

**安装收据损坏时 verify 仍返回 OK，和安装核对承诺不符。**

复现完全在沙盒内：

1. 正常完成 install-plan/install，保存安装目录 `.ftw-install.json` 原字节。
2. 将该文件替换为 `{"schema_version":1,"name":"fpga-team-workflow","installed_files":{}}`。
3. 运行源包命令 `python -B package-source/scripts/skill_maintenance.py verify --source skills/fpga-team-workflow`。
4. 实际 exit 0，status OK，errors=[]；应识别收据内容缺失/与安装内容不符。
5. 相同状态运行 install-plan 则正确 BLOCKED，说明核对入口之间不一致。
6. 已恢复收据原字节，后续正常升级和精确回退成功。

根因：`package-source/scripts/skill_maintenance.py` 的 `verify_package` 构造 actual 时排除 `.ftw-install.json`，之后没有读取/校验它。`install_plan` 才核对 installed_files。README 明确写“已安装目录中的 verify 会核对管理文件”，此处有可观察的误报。

证据：`forward-logs/07-corrupt-receipt-verify.json`、`forward-logs/08-corrupt-receipt-install-plan.json`；完整自动复现操作在 `forward_cases.py` 的收据测试段。建议在 verify 检测安装收据存在时验证其 schema/name/version/installed_files 与实际受管内容一致，并保持源包无收据时的验证行为。没有修改 Skill 实现。

影响限于错误的核对成功结论；本次没有观察到 install-plan/rollback 绕过后续修改保护，也没有发生产品或用户文件丢失。

## 未验证与最终边界

未验证新 Codex 任务的原生 Skill 自动发现/刷新、真实模型切换/计费、多模型同门槛成本、实际 GitHub 身份与事件、Vivado/Vitis/仿真器入口、CDC/STA、板卡或工程签署性终审。所有相关执行为 NOT_RUN 或 UNKNOWN。

没有写全局安装/config/角色、真实产品仓库、远端或硬件；没有下载、Flash、merge、push、评论或真实批准。所有已执行变更都是指定 sandbox 的测试安装、候选和报告。本报告的 Skill 行为结论与真实成员批准、FPGA 技术验收严格分开。
