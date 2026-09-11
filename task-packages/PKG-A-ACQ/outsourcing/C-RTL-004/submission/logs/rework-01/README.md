# C-RTL-004 R1 本次验证记录（2026-09-11）

状态：路径传参修复已完成；BD 验证 BLOCKED，未整体验收通过。
基线：0d737e3；原交付：99a48b0。Vivado 2025.2 SW Build 6299465，xc7z020clg400-2。
只修改 rebuild_bd.tcl 的 TB 文件参数，使用 [list [file join ...]]。
sources_1 已使用 list；get_files 返回对象列表；其余输出路径为单路径参数，未发现同类文件列表遗漏。
核心、包装、TB 字节未修改；原228次功能检查证据沿用，未重跑。

首次错误：ProjectBase 2-116，无法创建工程目录。传入的 Documents/Codex 路径在错误消息中变为 hsc/Codex；临时目录的 AppData/Local 变为 hsc/Local。
这是实际观察，具体原因尚未确定。改用正斜杠仍失败。短路径 D:/c004-rework-20260911 尝试因目录创建 Access denied，未能加载脚本。
本次未到达 SOURCE_TYPE_PASS、PORTS_PASS、VALIDATE_PASS 或 ALL BD TESTS PASS，不能将本次记录作为 BD 通过证据。
所有 Vivado 原始日志保留，包含 Common 17-1297 TclStore catalog 警告；未重置全局设置、重装工具或修改共享工程。

运行入口（PowerShell，在含空格路径的 submission 目录执行；需可创建工程的本机环境）：
```powershell
$bdScript = (Resolve-Path '.\scripts\rebuild_bd.tcl').Path
$bdRun = Join-Path ([IO.Path]::GetTempPath()) ('C004 rework ' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $bdRun | Out-Null
Push-Location $bdRun
try {
    & 'C:\AMDDesignTools\2025.2\Vivado\bin\vivado.bat' -mode batch -source $bdScript -log bd.log -nojournal -tclargs (Join-Path $bdRun 'project')
    if ($LASTEXITCODE -ne 0) { throw 'BD failed; preserve bd.log' }
} finally { Pop-Location }
```
预期：project/c004_bd_probe.xpr、BD、evidence/ports-32.txt、ports-3.txt、两个 BD Tcl 及 bd.log。
下一步：在可正常创建项目的环境按入口运行，获得全部 PASS 标记后补交端口表及日志，再申请独立验收。
旧 file-manifest.json 原样保存在 evidence-history/manifest-before-rework-01.json；当前清单覆盖修复脚本、本次失败证据及保留的历史证据，不含自身。