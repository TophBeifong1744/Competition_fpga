# fpga-team-workflow 0.1.8 (本地候选)

根据用户提供的生成指导 v1.2.0 实现的多人 FPGA 协作外层。工程依赖固定为
本地适配 `run-fpga-workflow 0.4.1`，原始上游为0.4.0 @ e40fd8000b526b72ba80373127bf5fd6e5f8dc28；详见内层ADAPTATION.json。
两者实际共同使用，外层没有复制工程角色。源码就是本目录，可整目录分发。

0.1.7 增量：[文件、路径与读取防错](references/execution-accuracy.md)。真实路径取值、允许写入范围、修改前断言和收尾差异检查；不把未读内容当作事实，不误修产品、不顺手移动/删除。版本切换避开在途任务，不新增逐动作审批或全量重测。

0.1.1 增量：[Notion 单一主协调写入规则](references/notion-coordination.md)。项目入口由项目配置提供；CLI 不自动同步任务或更改账号权限。旧测试报告保留原日期，不能当作本版本的新成员批准。

0.1.2 增量：成果优先、阶段内连续实施与整批复核，删除重复收件/审查门槛；详见 [主规则](SKILL.md#成果优先与相称流程)。按本项目入口同步，成员在安全断点安装，不打断现有任务或替其他成员授权。

0.1.3 增量：用户授权的尽早短时上板路线，保留重大风险核心检查，登记延期软件测试，允许据实核对厂商原件而不等待辅助工具完美适配；短测通过与完整验收分开。

0.1.4 增量：项目可启用指定AI代表成员批准，无需真人逐项确认；保留非作者资格、准确版本/范围和原结论，登记为AI代理批准。示例项目默认不代替用户启用或指定代理。

## 本包能做什么

0.1.5/0.1.6 增量：整个项目跨成员交接明确、直接、整批推进；一次给齐当前输入、集中非作者复核、问题回原责任人，不增加中转审批、不重复派工。适用于设计、代码、测试、数据、集成和发布，数据归属只是一个例子。详见 [跨成员交接](SKILL.md#跨成员交接明确快速整批推进)。成员角色和任务入口逐项目配置。

- status/plan、work、review、integrate、maintain 的按需规则与中文交接模板。
- 源码/生成物检查、旧布局映射、完整输入快照、保守工作区计划和执行。
- 证据身份/活动/反例检查、交付准入的机械检查；只核机械条件；成员或指定AI的批准须有可核实的原结论。
- 项目策略自动推荐具体模型和 effort、阶段差异、能力过期/不可用、角色覆盖检查。
- 维护提案、准确基线的候选改动、包验证、安装预览、事务备份/恢复/回退。

边界：模型仅推荐；无自动切换和可信客户端运行观测适配器。无 GitHub 写入代理、
无板卡动作、无自动清理删除。GitHub 权威事实由当前可用工具/真实成员核对。
文件/fixture 验证不等于 Vivado 功能、时序、CDC 或板级验收。

## 安装与核对

前置：Python 3.11+、PyYAML 6.x；工作区操作需要 Git；Windows 占用检测使用 tasklist.exe。
本次实际 Python/Windows 测试情况见 [兼容性](COMPATIBILITY.md) 和 [测试报告](tests/REPORT.md)。
缺 PyYAML 时由用户在选定 Python 环境安装 `python -m pip install -r requirements.txt`。
不要因此修改全局 PATH 或覆盖已有 Python 环境。

在本包目录打开 PowerShell。先运行：

```powershell
python -B scripts/skill_maintenance.py verify --source . --run-tests
```

指定一个安装作用域。示例为 `~/.codex/skills/fpga-team-workflow`，符合本机 Skill
制作约定；官方通用发现目录还包括 `~/.agents/skills` 和项目 `.agents/skills`。
只保留一个活动同名安装，先检查当前客户端实际发现路径。不要复制两份碰运气。

```powershell
$skillDestination = Join-Path $env:USERPROFILE '.codex/skills/fpga-team-workflow'
$planPath = Join-Path $env:TEMP ('ftw-plan-' + [guid]::NewGuid().ToString('N') + '.json')
python -B scripts/skill_maintenance.py install-plan --source . --target "$skillDestination" --out "$planPath"
python -B scripts/skill_maintenance.py install --plan "$planPath" --execute --authorization-ref '本次用户安装请求'
```

`--out` 必须放包目录之外（上面的示例已使用独立临时路径）；
它是显式写入，不覆盖已有文件。使用 `--dry-run` 或省略 `--execute` 只预览。
为避免手误，实际使用建议见 [CLI 示例](references/cli.md) 的包外计划路径。
安装只写这一 Skill 目录和其父目录下的 `.fpga-team-workflow-transactions`，
不改 AGENTS.md、config.toml、上游角色、凭据或产品源码。
已有未管理同名目录、用户改动、过期预览会被阻止。

安装后开一个新任务，确认列表出现 `fpga-team-workflow`，再执行：

```text
使用 $fpga-team-workflow，只读查看当前项目配置和一个工作包，给出模型建议、
缺项及工程子 Skill 的实际路径。不要构建、修改模型设置或写 GitHub。
```

文件安装成功不证明旧任务已刷新。独立成员应自己核对安装/角色/工具，不发送凭据。
已安装目录中的 `verify` 会核对管理文件；不要在包内生成临时输出或 __pycache__。

## 上游依赖：完整安装，禁止只拷贝 SKILL.md

本候选必须使用完整ZIP内与外层并列的`run-fpga-workflow/`本地适配0.4.1目录。
[固定上游提交](https://github.com/prasetyarobert205-jpg/codex-fpga-engineering-workflow/tree/e40fd8000b526b72ba80373127bf5fd6e5f8dc28)仅用于核对来源，直接下载的官方0.4.0不是本候选的配套依赖。
阅读随包安装脚本后按原生入口验证/预览/安装，不对移动main自动更新：

```powershell
pwsh -NoProfile -File scripts/validate-package.ps1
pwsh -NoProfile -File scripts/install.ps1 -Scope User -WhatIf
# 上面命令在随ZIP提供的本地适配run-fpga-workflow目录执行。安装有不同文件时先核备份计划；安装授权不由本说明产生。
pwsh -NoProfile -File scripts/verify-install.ps1 -Scope User
```

本外层的核对命令（在外层目录执行）：

```powershell
python -B scripts/team_workflow.py upstream inspect --skill "$env:USERPROFILE/.agents/skills/run-fpga-workflow" --agents "$env:USERPROFILE/.codex/agents"
```

它用当前锁定本地适配包的 41 个文件 SHA-256 核对内容和 13 角色；字节不一致会报告差异，
不静默把 CRLF 差异或本地修改当成已验证兼容。角色/工具当前已加载仍需实际任务验证。
上游一些参考提及其源码仓库 scripts；这些脚本未由上游安装器部署进 Skill 目录。
需要此类辅助脚本时从随ZIP提供的同一完整本地适配源码目录取用，不能声称安装目录内存在它们。

## 0.1.8 人机协作候选

Codex默认承担授权范围内工程修改、自测修复和简短中文注释；关键取舍列选项供人选择。人工操作前交实际检查、准确入口与截图/原报告保存点。ILA按具体判据核原始导出，限定通过和必要非作者接受后推进总工程接入。内层已同步做本地适配，不能与未适配官方0.4.0混用。

本包尚未发布/安装，不覆盖当前工程或成员电脑。先核候选与原授权，再在安全断点采用；当前只读任务仍只读。

## 项目接入与日常用法

新项目用 assets/project.example.yaml；旧项目用 project-existing.example.yaml，核对实际路径。
填写项目、成员、目标和依赖；只建需要的目录。`layout init` 只建文档/受控目录，
真实器件、IP、入口和工具流程交内层建立，不伪造 .xpr 或占位 bitstream。

```text
使用 $fpga-team-workflow plan：依据现有 Issue 拆一个可独立交付的工作包，给出模型建议。
使用 $fpga-team-workflow work：在该包已授权范围完成实现与交付，复用活动工作区。
使用 $fpga-team-workflow review：只读复核 PR 的准确提交，先核查原合同再决定补测。
使用 $fpga-team-workflow integrate：检查候选集成版本及完整完成定义，报告缺证据。
使用 $fpga-team-workflow maintain：为这个具体流程缺陷生成提案，先不覆盖安装。
```

工作区 `apply` 会再次核对基线与依赖；任何脏/未跟踪/忽略内容都会保守阻止切换。
这可能要求先在已授权范围归档或隔离当前数据；脚本不会代你清理。
工作区占用输入来自已核实事实，本地锁只约束使用本工具的进程，不是跨机器锁。

## 更新与回退

按 `maintain propose → plan → apply → verify → publish/安装` 使用，不要求七次确认。
`apply` 只在新的候选目录构造变化，校验准确基线和逐文件哈希；不直接编辑安装副本。
发布由有权 GitHub 工具/成员执行；CLI publish 只生成发布要求与材料状态。

安装返回事务路径，回退时使用**源码包**中的工具：

```powershell
python -B scripts/skill_maintenance.py rollback --transaction '<安装返回的事务目录>' --dry-run
python -B scripts/skill_maintenance.py rollback --transaction '<安装返回的事务目录>' --execute --authorization-ref '<回退请求>'
```

升级失败自动恢复；异常中断使用 `recover`，未知后续变化会阻止覆盖。备份不会自动删除。
Windows 目录替换是经过测试的分步 rename + 恢复事务，**不声称整个切换是单个原子操作**。
进程被强杀可能留下安装锁；先确认锁中 PID/事务已无活动写入、核对事务内容后，
按明确授权移除该单个失效锁，再 recover；不能删除整个事务根。

模型策略仍是 `UNBENCHMARKED`。路由测试只验证策略行为；没有实际多模型同质量门槛
实验，就不宣称最优性价比或节省百分比。
