[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$errors = [Collections.Generic.List[string]]::new()
function Add-CheckError([string]$Message) { $script:errors.Add($Message) }

$required = @(
    '.codex-plugin/plugin.json', 'skills/run-fpga-workflow/SKILL.md',
    'skills/run-fpga-workflow/agents/openai.yaml', 'skills/run-fpga-workflow/assets/icon.svg',
    'skills/run-fpga-workflow/references/task-profiles.md',
    'skills/run-fpga-workflow/references/improvement-policy.md',
    'skills/run-fpga-workflow/references/improvement-evidence.md',
    'skills/run-fpga-workflow/references/workflow-artifacts.md',
    'skills/run-fpga-workflow/references/temporal-evidence.md',
    'skills/run-fpga-workflow/references/model-card.md',
    'skills/run-fpga-workflow/references/vendor-adapters.md',
    'skills/run-fpga-workflow/references/project-layout.md',
    'skills/run-fpga-workflow/references/project-identity-and-task-delta.md',
    'skills/run-fpga-workflow/references/ip-integration.md',
    'skills/run-fpga-workflow/references/physical-implementation.md',
    'skills/run-fpga-workflow/references/private-fault-library.md',
    'skills/run-fpga-workflow/references/shadow-rollout.md',
    'templates/AGENTS.fpga.md', 'README.md', 'README.zh-CN.md', 'assets/hero.svg', 'LICENSE', 'SECURITY.md',
    'VERSION', 'CHANGELOG.md', 'COMPATIBILITY.md', 'docs/research.md',
    'docs/en/architecture.md', 'docs/en/roles.md', 'docs/en/installation.md',
    'docs/en/usage.md', 'docs/en/safety-and-evidence.md',
    'docs/zh-CN/README.md', 'docs/zh-CN/architecture.md', 'docs/zh-CN/roles.md',
    'docs/zh-CN/installation.md', 'docs/zh-CN/usage.md', 'docs/zh-CN/safety-and-evidence.md',
    'scripts/detect-vendor.ps1', 'scripts/update-filelists.ps1', 'scripts/preflight-project.ps1',
    'scripts/prepare-vendor-libraries.ps1', 'scripts/new-fpga-project.ps1', 'scripts/fault-library.ps1',
    'scripts/validate-simulation-evidence.ps1',
    'templates/fault-library.config.example.json',
    'templates/fpga-project/common/README.md.template',
    'templates/fpga-project/common/AGENTS.md',
    'templates/fpga-project/common/build-run.bat.template',
    'templates/fpga-project/common/simulation-run.bat.template',
    'templates/fpga-project/common/simulation-setting.txt.template',
    'templates/fpga-project/common/vsim.do.template',
    'templates/fpga-project/common/lint-run.bat.template',
    'templates/fpga-project/common/setting.bat.template'
)
foreach ($rel in $required) {
    $path = Join-Path $root ($rel -replace '/', [IO.Path]::DirectorySeparatorChar)
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { Add-CheckError "Missing required file: $rel" }
}

$expectedNames = @('fpga_architect','fpga_engineer','verification_engineer','fpga_temporal_evidence_reviewer','fpga_cdc_timing_reviewer','fpga_interface_architect','fpga_vendor_platform_reviewer','fpga_board_validation_engineer','fpga_reviewer','system_architect','embedded_engineer','hardware_datasheet','independent_reviewer')
$agentFiles = Get-ChildItem -LiteralPath (Join-Path $root '.codex\agents') -File -Filter '*.toml'
if ($agentFiles.Count -ne 13) { Add-CheckError "Expected 13 agent TOML files; found $($agentFiles.Count)." }
$seen = @{}
$readOnlyExpected = @('fpga_architect','fpga_temporal_evidence_reviewer','fpga_cdc_timing_reviewer','fpga_interface_architect','fpga_vendor_platform_reviewer','fpga_board_validation_engineer','fpga_reviewer','system_architect','hardware_datasheet','independent_reviewer')
foreach ($file in $agentFiles) {
    $text = [IO.File]::ReadAllText($file.FullName, [Text.UTF8Encoding]::new($false, $true))
    $match = [regex]::Match($text, '(?m)^name\s*=\s*"([^"]+)"\s*$')
    if (-not $match.Success) { Add-CheckError "Missing name in $($file.Name)"; continue }
    $name = $match.Groups[1].Value
    if ($name -ne $file.BaseName) { Add-CheckError "Name/file mismatch: $($file.Name) -> $name" }
    if ($seen.ContainsKey($name)) { Add-CheckError "Duplicate agent name: $name" } else { $seen[$name] = $true }
    if ($name -in $readOnlyExpected -and $text -notmatch '(?m)^sandbox_mode\s*=\s*"read-only"\s*$') { Add-CheckError "Read-only sandbox missing: $name" }
    if ($name -notin $readOnlyExpected -and $text -match '(?m)^sandbox_mode\s*=\s*"read-only"\s*$') { Add-CheckError "Writer incorrectly read-only: $name" }
}
foreach ($name in $expectedNames) { if (-not $seen.ContainsKey($name)) { Add-CheckError "Missing agent: $name" } }

$expectedVersion = (Get-Content -LiteralPath (Join-Path $root 'VERSION') -Raw).Trim()
if ($expectedVersion -notmatch '^\d+\.\d+\.\d+$') { Add-CheckError "VERSION is not a semantic version: $expectedVersion" }
$plugin = Get-Content -LiteralPath (Join-Path $root '.codex-plugin\plugin.json') -Raw | ConvertFrom-Json
if ($plugin.name -ne 'codex-fpga-engineering-workflow' -or $plugin.version -ne $expectedVersion -or $plugin.license -ne 'MIT') { Add-CheckError 'Plugin identity/version/license mismatch.' }
if ($plugin.skills -ne './skills/') { Add-CheckError 'Plugin skills path mismatch.' }
foreach ($unsupported in @('apps','mcpServers','hooks')) { if ($plugin.PSObject.Properties.Name -contains $unsupported) { Add-CheckError "Unexpected manifest field: $unsupported" } }

$skillText = Get-Content -LiteralPath (Join-Path $root 'skills\run-fpga-workflow\SKILL.md') -Raw
foreach ($reference in @('references/task-profiles.md','references/workflow-artifacts.md','references/temporal-evidence.md','references/model-card.md','references/vendor-adapters.md','references/project-layout.md','references/project-identity-and-task-delta.md','references/ip-integration.md','references/physical-implementation.md','references/private-fault-library.md','references/shadow-rollout.md','references/improvement-policy.md','references/improvement-evidence.md')) { if ($skillText -notmatch [regex]::Escape($reference)) { Add-CheckError "Skill does not reference $reference" } }
if ($skillText -notmatch 'only `fpga_engineer` writes product') { Add-CheckError 'Single product-writer gate is missing from skill.' }
if ($skillText -notmatch 'at most three automatic repair/re-review rounds') { Add-CheckError 'Three-round repair stop is missing from skill.' }
if ($skillText -notmatch 'two consecutive no-progress rounds') { Add-CheckError 'Two-no-progress stop is missing from skill.' }
if ($skillText -notmatch 'codex_out') { Add-CheckError 'codex_out isolation rule is missing from skill.' }
if ($skillText -notmatch 'project/par' -or $skillText -notmatch 'simulation/work') { Add-CheckError 'Formal native output directories are missing from skill.' }
if ($skillText -notmatch 'depth-0' -or $skillText -notmatch 'process PATH') { Add-CheckError 'Depth-0 launcher or command-name runtime contract is missing from skill.' }
if ($skillText -match 'out/codex') { Add-CheckError 'Deprecated out/codex path remains in skill.' }

$schemaFiles = Get-ChildItem -LiteralPath (Join-Path $root 'skills\run-fpga-workflow\references\schemas') -File -Filter '*.schema.json'
if ($schemaFiles.Count -ne 11) { Add-CheckError "Expected 11 workflow JSON Schemas; found $($schemaFiles.Count)." }
foreach ($schema in $schemaFiles) {
    try { $null = Get-Content -LiteralPath $schema.FullName -Raw -Encoding UTF8 | ConvertFrom-Json } catch { Add-CheckError "Invalid JSON Schema: $($schema.Name)" }
}

$parseTargets = Get-ChildItem -LiteralPath $root -Recurse -File | Where-Object { $_.Extension -in @('.ps1','.psd1') }
foreach ($target in $parseTargets) {
    $tokens = $null; $parseErrors = $null
    [void][Management.Automation.Language.Parser]::ParseFile($target.FullName, [ref]$tokens, [ref]$parseErrors)
    foreach ($parseError in $parseErrors) { Add-CheckError "PowerShell parse error in $($target.FullName): $($parseError.Message)" }
}

$batchTemplate = Get-Content -LiteralPath (Join-Path $root 'templates\fpga-project\common\build-run.bat.template') -Raw
$simulationBatchTemplate = Get-Content -LiteralPath (Join-Path $root 'templates\fpga-project\common\simulation-run.bat.template') -Raw
if ($batchTemplate -notmatch [regex]::Escape('%~dp0')) { Add-CheckError 'One-click batch template is not anchored with %~dp0.' }
if ($simulationBatchTemplate -notmatch [regex]::Escape('%~dp0')) { Add-CheckError 'Simulation batch template is not anchored with %~dp0.' }
if ($batchTemplate -match '(?i)pwsh|powershell|\.ps1|\.psd1' -or $simulationBatchTemplate -match '(?i)pwsh|powershell|\.ps1|\.psd1') { Add-CheckError 'Generated user runtime still depends on PowerShell.' }
if ($batchTemplate -match '(?i)VIVADO_BAT|MODELSIM_EXE|[A-Z]:\\[^\r\n"]+\.(exe|bat)' -or $simulationBatchTemplate -match '(?i)VIVADO_BAT|MODELSIM_EXE|[A-Z]:\\[^\r\n"]+\.(exe|bat)') { Add-CheckError 'Generated runtime embeds an absolute executable file.' }
if ($batchTemplate -match 'vendor-build\.bat' -or $simulationBatchTemplate -match 'vendor-sim\.bat') { Add-CheckError 'Deprecated visible vendor BAT wrappers remain in generated runtime.' }
foreach ($removedTemplate in @('templates/fpga-project/common/vendor-build.bat.template','templates/fpga-project/common/vendor-sim.bat.template')) {
    if (Test-Path -LiteralPath (Join-Path $root ($removedTemplate -replace '/', [IO.Path]::DirectorySeparatorChar))) { Add-CheckError "Deprecated template remains: $removedTemplate" }
}
$scaffoldText = Get-Content -LiteralPath (Join-Path $root 'scripts\new-fpga-project.ps1') -Raw
foreach ($canonical in @('project/rtl','project/par','project/script','simulation/script','linter/script','release/output')) {
    if ($scaffoldText -notmatch [regex]::Escape($canonical)) { Add-CheckError "Canonical scaffold path is missing: $canonical" }
}
if ($scaffoldText -match '(?i)(project2|par2|script2)') { Add-CheckError 'Generated scaffold contains a numbered standard directory.' }
if ($scaffoldText -match [regex]::Escape('script\ai_run')) { Add-CheckError 'Generated user runtime still creates script/ai_run.' }
if ($scaffoldText -notmatch 'canonical_project_file') { Add-CheckError 'Scaffold does not report the depth-0 canonical project file.' }
foreach ($nativePath in @('project\script\setting.bat','project\script\src_list.txt','simulation\script\setting.txt','simulation\script\src_list.txt','simulation\script\vsim.do')) {
    if ($scaffoldText -notmatch [regex]::Escape($nativePath)) { Add-CheckError "Scaffold is missing native runtime file: $nativePath" }
}
$temporal = Get-Content -LiteralPath (Join-Path $root '.codex\agents\fpga_temporal_evidence_reviewer.toml') -Raw
foreach ($token in @('STATIC_CYCLE','SIMULATION_EVIDENCE','COMBINED','SHADOW','NEEDS_PARTITION')) { if ($temporal -notmatch $token) { Add-CheckError "Temporal reviewer is missing $token." } }
$verification = Get-Content -LiteralPath (Join-Path $root '.codex\agents\verification_engineer.toml') -Raw
if ($verification -notmatch 'not the independent signer') { Add-CheckError 'Verification-author self-sign boundary is missing.' }

$allTextFiles = Get-ChildItem -LiteralPath $root -File -Recurse | Where-Object { ($_.Extension -in @('.md','.toml','.json','.yaml','.yml','.ps1','.psd1','.svg','.txt','.template','.bat') -or $_.Name -in @('LICENSE','VERSION','.gitignore','.gitattributes')) -and $_.FullName -ne $PSCommandPath }
$privatePattern = '(?i)(' + 'C:' + '\\Users\\' + '|/home/[^/]+/|' + '\.codex\\memories' + '|D:' + '\\PDS|' + 'customer[-_ ]?name\s*[:=])'
$printSpecificPattern = '(?i)(' + 'print' + 'ing head|' + 'print' + 'head|' + [char]0x55B7 + [char]0x5934 + '|' + [char]0x5DE5 + [char]0x4E1A + [char]0x6253 + [char]0x5370 + ')'
$cjkPattern = '[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]'
$deletedReferencePattern = '(?i)(README\.en\.md|CONTRIBUTING\.zh-CN\.md)'
foreach ($file in $allTextFiles) {
    try { $content = [IO.File]::ReadAllText($file.FullName, [Text.UTF8Encoding]::new($false, $true)) } catch { Add-CheckError "Invalid UTF-8: $($file.FullName)"; continue }
    if ($content -match '(?i)(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY|AKIA[0-9A-Z]{16})') { Add-CheckError "Possible secret: $($file.FullName)" }
    if ($content -match $privatePattern) { Add-CheckError "Possible private/absolute path or customer marker: $($file.FullName)" }
    if ($content -match $printSpecificPattern) { Add-CheckError "Industrial-print-specific wording remains: $($file.FullName)" }
    $relativePublicPath = [IO.Path]::GetRelativePath($root, $file.FullName) -replace '\\','/'
    $isChineseDoc = $relativePublicPath -eq 'README.zh-CN.md' -or $relativePublicPath.StartsWith('docs/zh-CN/', [StringComparison]::Ordinal)
    if ($content -match $cjkPattern -and -not $isChineseDoc) { Add-CheckError "CJK Unified Ideograph remains outside localized documentation: $($file.FullName)" }
    if ($content -match $deletedReferencePattern) { Add-CheckError "Reference to a removed localized document remains: $($file.FullName)" }
}

foreach ($removedPath in @('README.en.md', 'CONTRIBUTING.zh-CN.md')) {
    if (Test-Path -LiteralPath (Join-Path $root ($removedPath -replace '/', [IO.Path]::DirectorySeparatorChar))) {
        Add-CheckError "Removed localized path still exists: $removedPath"
    }
}
if ($errors.Count -gt 0) {
    $errors | ForEach-Object { Write-Host "ERROR: $_" -ForegroundColor Red }
    throw "Package validation failed with $($errors.Count) error(s)."
}
Write-Host "Package validation passed for version $expectedVersion`: 13 agents, 10 strict read-only roles, 11 workflow schemas, clean native BAT/DO templates, package PowerShell parse, UTF-8, English runtime content, allowed zh-CN documentation, and public-content scans."
