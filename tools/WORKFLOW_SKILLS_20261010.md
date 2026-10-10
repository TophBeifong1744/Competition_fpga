# SoundSight 新版工作流：成员安装与回执

2026-10-10 用户已授权安装并同步，且仅授权更新工作流分发、锁版本、旧授权说明与接入指南。原工程限制对A/B/C撤销；产品任务仍以其具体范围和现场操作授权为准。

外层 **fpga-team-workflow 0.1.8**；内层 **run-fpga-workflow 本地适配0.4.1**，来源官方0.4.0固定提交，patch_id=SS-HUMAN-20261010-1。13角色保留。内层不是官方0.4.1发布，未适配官方0.4.0不能与本外层混用。

## 下载与内容

[本次分发页](https://github.com/TophBeifong1744/Competition_fpga/releases/tag/workflow-skills-0.1.8-local0.4.1-20261010) · [完整ZIP](https://github.com/TophBeifong1744/Competition_fpga/releases/download/workflow-skills-0.1.8-local0.4.1-20261010/SoundSight-workflow-skills-0.1.8-local0.4.1-20261010.zip)

ZIP SHA256：`4e3298e1c5ad394c96cf51e251fab35783305c2747a50aa06d9627bd06646f48`。解压后两层目录并列，含完整内层安装工具、13角色、来源/许可证、差异及原检查记录。包内候选状态是制作时快照，不代表每台机器的当前安装状态。

包含原MD建议：整批推进、集中非作者复核、三类人工节点、共用准确候选原run、缩短模板、按需角色与模型推荐；再加四项工程权限/预检查/内层适配/ILA集成要求。真实任务试点和改进收益仍未验证。

## 最简单的安装方式

在本次原子步骤结束的安全断点，把下载的ZIP和以下文字交给本人Codex，不打断在途工程：

> 安装SoundSight配套工作流：外层0.1.8、内层本地适配0.4.1，patch_id=SS-HUMAN-20261010-1。先核ZIP SHA256与CRC，读两层README和安装脚本。核现有安装回执/哈希与用户改动，先预览、保留原版及内层安装清单备份；有未知改动停止覆盖。使用包内安装工具安装完整配套Skill和13角色，不改全局模型设置、其他Skill或产品工程。安装后verify、upstream inspect核41文件和13角色，回报准确版本、备份路径、核对结果和客户端加载状态。不要把安装核对当工程或板测PASS。

## Windows 原生入口

前置：PowerShell7、Python3.11+及PyYAML。先确认本人实际USERPROFILE和发现路径；只保留一个活动同名安装。以下在完整ZIP解压根目录执行：

```powershell
$packageRoot = (Get-Location).Path
$outerSource = Join-Path $packageRoot 'fpga-team-workflow'
$innerSource = Join-Path $packageRoot 'run-fpga-workflow'
$skillDestination = Join-Path $env:USERPROFILE '.codex/skills/fpga-team-workflow'
$planPath = Join-Path $env:TEMP ('ftw-plan-' + [guid]::NewGuid().ToString('N') + '.json')
python -X utf8 -B "$outerSource/scripts/skill_maintenance.py" verify --source "$outerSource"
python -X utf8 -B "$outerSource/scripts/skill_maintenance.py" install-plan --source "$outerSource" --target "$skillDestination" --out "$planPath"
pwsh -NoProfile -File "$innerSource/scripts/validate-package.ps1"
pwsh -NoProfile -File "$innerSource/scripts/install.ps1" -Scope User -Force -WhatIf
```

预览前核旧内层manifest中每个文件的真实哈希，另存旧manifest及受控文件；未知改动不能仅凭Force覆盖。WhatIf最后虽打印Installed字样仍只是预览。确认备份与范围后：

```powershell
pwsh -NoProfile -File "$innerSource/scripts/install.ps1" -Scope User -Force
python -X utf8 -B "$outerSource/scripts/skill_maintenance.py" install --plan "$planPath" --execute --authorization-ref '本人授权安装SoundSight配套新版'
pwsh -NoProfile -File "$innerSource/scripts/verify-install.ps1" -Scope User
python -X utf8 -B "$outerSource/scripts/skill_maintenance.py" verify --source "$skillDestination"
python -X utf8 -B "$skillDestination/scripts/team_workflow.py" upstream inspect --skill "$env:USERPROFILE/.agents/skills/run-fpga-workflow" --agents "$env:USERPROFILE/.codex/agents"
```

计划过期/用户改动/安装失败时保持原件，按事务恢复；不能再Force绕过。外层返回事务路径，内层Force保留逐文件backup；额外旧manifest/原41个目的路径状态应成套保留。必要回退按安装后哈希确认无后续修改后，由本人Codex恢复准确旧配套，不直接运行uninstall冒充回退。

## 回执

在同步通知原Issue回复一条即可：成员；外层/内层/patch_id；verify与41文件/13角色核对；旧版备份；新聊天是否已发现/实际加载（未核写UNKNOWN）；在途批是否仍沿旧版本。不发凭据，不另建台账。

A本机安装及文件核对完成，客户端实际加载UNKNOWN。B/C安装待本人回执。95项工具回归与包检查已通过，不等于真实工程仿真、综合/时序、ILA或板测通过。Notion仍由指定主协调写入，本次不改变权限或替工程签PASS。

## 发布权限与范围

本次为用户直接决定的工作流配置/分发同步；不冒称合格非作者成员已批准产品，也不关闭产品任务，不形成以后绕过工程复核的例外。
