# 安装

[中文导航](README.md) · [使用](usage.md) · [English installation](../en/installation.md)

## 前置条件

- 支持自定义 agent 和 Skill 的 Codex 环境；
- PowerShell 7，用于包验证、安装和脚手架；
- Git，可选；
- 厂商 EDA 工具只在真实工程运行时需要。

生成后的正式 `run.bat` 不依赖 Codex 私有 PowerShell。

## 验证包

```powershell
pwsh -NoProfile -File .\scripts\validate-package.ps1
```

## 预览安装

```powershell
pwsh -NoProfile -File .\scripts\install.ps1 -Scope User -WhatIf
```

项目级：

```powershell
pwsh -NoProfile -File .\scripts\install.ps1 -Scope Project -ProjectPath C:\path\to\repo -WhatIf
```

## 正式安装和核对

```powershell
pwsh -NoProfile -File .\scripts\install.ps1 -Scope User
pwsh -NoProfile -File .\scripts\verify-install.ps1 -Scope User
```

默认不会覆盖不同内容的已存在文件。使用 `-Force` 前先检查差异；强制替换
会创建时间戳备份。

## 可选 AGENTS 模板

```powershell
pwsh -NoProfile -File .\scripts\install.ps1 -Scope Project -ProjectPath C:\path\to\repo -InstallAgentsTemplate
```

## 新工程脚手架

```powershell
pwsh -NoProfile -File .\scripts\new-fpga-project.ps1 -Destination C:\work\my-fpga -ProjectName my-fpga -TopModule top -Vendor XILINX
```

也支持 `PANGO`、`ANLOGIC`。脚手架记录稳定工程身份，但不会伪造 XPR/PDS/AL。
用户可见仿真脚本固定为 `run.bat/setting.txt/src_list.txt/vsim.do`。

## 升级

1. 阅读 [CHANGELOG](../../CHANGELOG.md) 和 [COMPATIBILITY](../../COMPATIBILITY.md)；
2. 运行新版 package validation；
3. 使用相同 Scope 执行 `-WhatIf`；
4. 审查差异后再决定 `-Force`；
5. 运行 verify-install；
6. 在新会话中做只读行为 canary。

## 卸载

```powershell
pwsh -NoProfile -File .\scripts\uninstall.ps1 -Scope User -WhatIf
pwsh -NoProfile -File .\scripts\uninstall.ps1 -Scope User
```

卸载只删除 manifest 中 hash 未变化的已安装文件；用户修改过的文件会保留。
