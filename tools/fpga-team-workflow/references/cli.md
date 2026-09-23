# CLI 与数据接口

运行目录为本包；Windows 命令参数使用双引号包裹空格路径。推荐 `python -B`，不生成包内 pycache。
JSON 是 YAML 子集；`.yaml` 可保存 JSON。PyYAML safe_load 不执行 YAML 对象。
退出码：0=OK，2=BLOCKED，3=INCONCLUSIVE，4=NEEDS_USER_ACTION。它们不是 FPGA 技术 PASS。
无 `--execute` 默认只读/预览；`--out` 是单独明确的写文件请求，必须使用包外新路径。
`--authorization-ref` 仅记录已有用户授权，不自行授予权限。

## 一次生成可运行的本地示例

```powershell
$packagePath = (Get-Location).Path
$demoPath = Join-Path $env:TEMP ('fpga-team-demo-' + [guid]::NewGuid().ToString('N'))
python -B scripts/demo.py --destination "$demoPath"
python -B scripts/team_workflow.py model recommend --config "$demoPath/team-workflow.yaml" --task "$demoPath/task.json"
python -B scripts/team_workflow.py model inspect --roles "$env:USERPROFILE/.codex/agents"
```

demo 只写新的显式目录，生成小型人工 fixture、交接/规则演示与安装回退记录；
不创建远端 Issue、不代表真实成员批准或 EDA 通过。
demo 与 maintain apply 从本次交付的源码包运行；已安装副本用于日常调用与核对，不能当作候选源码基线。

## 仓库检查与工作区

```powershell
python -B scripts/team_workflow.py doctor --root '<repo>' --config '<repo>/team-workflow.yaml' --skill '<installed-inner>' --agents '<installed-role-dir>'
python -B scripts/team_workflow.py layout inspect --root '<repo>' --config '<repo>/team-workflow.yaml'
python -B scripts/team_workflow.py layout init --root '<new-empty-root>' --config '<filled-config.yaml>' --execute --authorization-ref '<request>'
python -B scripts/team_workflow.py workspace plan --root '<repo>' --config '<config>' --task '<task.json>' --occupancy '<occupancy.json>' --out '<outside-repo>/workspace-plan.json'
python -B scripts/team_workflow.py workspace apply --plan '<plan.json>' --config '<config>' --occupancy '<fresh-occupancy.json>' --dry-run
python -B scripts/team_workflow.py workspace apply --plan '<plan.json>' --config '<config>' --occupancy '<fresh-occupancy.json>' --execute --authorization-ref '<request>'
```

工作包脚本输入（Skill 根据 Issue 自动提取，成员不手填复杂评分）：

```json
{"schema_version":1,"task_ref":"#42","actor_ref":"member-one","phase":"implementation","base_commit":"<40/64位已解析提交>","branch":"task/42-module","activity":"implementation","execution_kind":"model_assisted","contract_trusted":true,"dependency_files":[],"dependency_closure_ref":"<真实入口验证依据>","sparse_requested":false,"parallel_write":false,"repair":{"finding_id":"F-01","rounds":0,"consecutive_no_progress":0}}
```

占用输入：`{"schema_version":1,"writer_clear":true,"active":false,"source_ref":"<当前成员/进程核对记录>"}`。
执行前重新获得，占用记录不是跨机器原子锁。检测到本机 Vivado/仿真进程会保守阻止切换。
`--destination <new-external-dir>` 用于计划已经要求的独立 worktree；不是默认复制。
新分支按准确基准建立，已存在目标分支偏离预览基准会停止。

布局除指导字段外支持 `required_inputs`（实际必要 .mem/DCP/外部依赖的已取得相对路径）和
`regenerable_output_roots`（已证明可再生的输出），用于 source/ignore 反查。源码例外优先保护。
filelist 当前支持仓库根相对的一行一文件、引号路径、`+incdir+`、`+define+`、`-f <嵌套清单>`。
literal include 会追加；宏/Tcl/XML 工程加载语义不做猜测，不支持行会报告。
真实 vendor source view、条件编译、外部许可/数据访问仍需相应适配验证。
多目标用 `targets: [{id: ..., layout: {...}}, ...]` 显式选择 `--target`；所有路径相对仓库根。
跨目标可变输出重叠会阻止；自动生成多目标工程不支持。

## 快照与证据

```powershell
python -B scripts/team_workflow.py snapshot --root '<repo>' --inputs '<inputs.json>' --out '<start.json>'
# 在授权范围执行实际工具；退出后生成 end snapshot 并与 start 比较。
python -B scripts/team_workflow.py snapshot --root '<repo>' --inputs '<inputs.json>' --previous '<start.json>' --out '<end.json>'
python -B scripts/team_workflow.py evidence inspect --index '<index.json>' --current '<current.json>' --evidence-root '<received-archive>'
python -B scripts/team_workflow.py handoff render --facts '<facts.json>' --config '<config>' --task '<task.json>'
```

inputs：`{"schema_version":1,"files":["project/rtl/module.sv","data/fixtures/rom.mem"],"context":{"parameters":{},"tool":"<实际版本>"}}`。
新增文件进入哈希，不能仅记录 HEAD。前后匹配只证明捕获点一致，运行期间写入互斥仍需实际保持。

evidence index 是外层引用/判断视图，不写入上游原生 schema。`identities` 的键为
`requirements/sources/constraints/parameters/dependencies/checker/reference/input_data/tool/entry`，
值为相关身份或明确无约束的受控标记；null 表示未知。current 提供当前相同键。
index 另有 `profile`, `run_result`, `run_inputs_stable`, `independent_basis_ref`,
`checker_activity`, `negative_canary` 和 `raw_records: [{schema_version:1,local_path:...,sha256:...}]`。
外层索引支持明确标注的 1 / 1.0 引用记录；原生 run-manifest、snapshot-manifest、
simulation-evidence 支持锁定上游的 1.0.0，读取真实 run/snapshot、退出码、活动和负例边界，
发现摘要 PASS 与原件失败矛盾时阻断；遇到其他版本/类型显示不支持。
**不声称完整解析全部上游 proof schema**。原生文件保留，运行/语义由实际内层和复核成员判断。
`assumption_conflicts` 或 `checker_invalid` 使旧 PASS 失效。远程证据未取得/未核对返回 UNKNOWN；
CLI 不自动联网下载私有证据，不拿作者本地路径冒充接收人访问证明。

delivery facts 是从真实 PR/Issue 提取的临时视图：author, contributors, head_commit,
evidence_commit, candidate_commit, tested_candidate_commit, reviews[{actor,state,commit}],
required_checks_status, needs_board, board_pass, stage, system_pass, limitations。
导入 JSON 不能认证 GitHub 身份，所以脚本即使机械条件全满足也不会输出“交付批准”。
真实 GitHub review 事件由已配置连接器/gh 只读读取并由当前成员确认，不伪造事件。

## 模型建议和观测

activity：fixed_execution / implementation / proven_local_fix / diagnosis / checker_design /
reference_design / review / architecture / documentation。标题不参与低价分流。
phase_facts 可以对连续阶段给有限覆盖；public_interface/cross_clock/high_impact/assumption_conflict
触发 decision；complex_cross_layer 加 specific_uncertainty 才允许 deep。
missing_conditions、已成立的 blocking_counterexample、原问题返修上限触发停止。

capabilities：schema_version=1、actor_ref、source_ref、ISO checked_at、models（ID→efforts 列表）；
complete 表示当前清单完整，默认有效期24小时。它只是一条有来源的能力观察，不是账号授权。
支持 `approved_alternatives`，必须带 `quality_evidence_ref` 且当前成员实际可用；没有依据不降档。
主会话 metadata 和子 Agent observations 从文件导入时不自动可信；手报标 USER_REPORTED，
配置/提示词/未认证元数据标 UNKNOWN。只有将来实测可信 adapter 才能产生 VERIFIED。
`model apply` 返回 UNSUPPORTED 与手动入口，即使 policy 写 apply_authorized 也不会改设置。

## 维护

```powershell
$packagePath = (Get-Location).Path
$planPath = Join-Path $env:TEMP ('ftw-install-plan-' + [guid]::NewGuid().ToString('N') + '.json')
$skillDestination = Join-Path $env:USERPROFILE '.codex/skills/fpga-team-workflow'
python -B scripts/skill_maintenance.py install-plan --source "$packagePath" --target "$skillDestination" --out "$planPath"
python -B scripts/skill_maintenance.py install --plan "$planPath" --execute --authorization-ref '<用户安装请求>'
```

propose/plan 输入 assets/change-request-template.yaml（真实 problem/requested_behavior 和 kind）；
plan 返回当前源树，可据其 `digest` 确定 apply 基线。候选申请增加 `base_tree_sha256`、
`changes: [{path, base_sha256, content}]`；scope.include 必须逐项列出准确文件。
`apply --source <base> --request <request> --target <new-candidate> --execute --authorization-ref <request>`
只改新候选，输出 diff；接着 verify --run-tests，再做非作者行为测试。
`seal --execute` 只更新候选 manifest，**不证明审核通过**；发布还需要实际独立复核。
安装必须从完整源包运行，备份/事务路径由目标父目录推导并核验，不接受任意恢复目的路径。
恢复保护未知变化；包版本/源码摘要与客户端生效是不同事实。

cleanup plan 使用 inventory.items，其中每项必须给 path、owner、regenerable、recipe_ref、
active=false、unique_data=false、failed_evidence=false。只列候选，不实现删除命令。
还需 `owned_files` 提供目录内相对文件到 SHA-256 的归属清单；未知/变动文件、真实依赖与
保护路径重叠会保留。不能只填一个 owner 字符串就把整目录认作可清理缓存。
