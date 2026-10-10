[CmdletBinding(SupportsShouldProcess)]
param(
    [ValidateSet('User', 'Project')][string]$Scope = 'User',
    [string]$ProjectPath,
    [switch]$InstallAgentsTemplate,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-NormalizedRoot {
    param([string]$SelectedScope, [string]$SelectedProject)
    if ($SelectedScope -eq 'User') { return [IO.Path]::GetFullPath($env:USERPROFILE) }
    if ([string]::IsNullOrWhiteSpace($SelectedProject)) { throw '-ProjectPath is required for Project scope.' }
    if (-not (Test-Path -LiteralPath $SelectedProject -PathType Container)) { throw "Project path does not exist: $SelectedProject" }
    return [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $SelectedProject).Path)
}

function Get-RelativePortablePath {
    param([string]$Base, [string]$Path)
    return ([IO.Path]::GetRelativePath($Base, $Path) -replace '\\', '/')
}

$packageRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$targetRoot = Get-NormalizedRoot -SelectedScope $Scope -SelectedProject $ProjectPath
$manifestRelative = '.codex/codex-fpga-engineering-workflow.install.json'
$manifestPath = Join-Path $targetRoot ($manifestRelative -replace '/', [IO.Path]::DirectorySeparatorChar)

$mappings = [Collections.Generic.List[object]]::new()
$agentSource = Join-Path $packageRoot '.codex\agents'
Get-ChildItem -LiteralPath $agentSource -File -Filter '*.toml' | Sort-Object Name | ForEach-Object {
    $mappings.Add([pscustomobject]@{ Source = $_.FullName; Relative = ".codex/agents/$($_.Name)" })
}
$skillSource = Join-Path $packageRoot 'skills\run-fpga-workflow'
Get-ChildItem -LiteralPath $skillSource -File -Recurse | Sort-Object FullName | ForEach-Object {
    $rel = Get-RelativePortablePath -Base $skillSource -Path $_.FullName
    $mappings.Add([pscustomobject]@{ Source = $_.FullName; Relative = ".agents/skills/run-fpga-workflow/$rel" })
}
if ($InstallAgentsTemplate) {
    $agentsTarget = if ($Scope -eq 'User') { '.codex/AGENTS.md' } else { 'AGENTS.md' }
    $mappings.Add([pscustomobject]@{ Source = (Join-Path $packageRoot 'templates\AGENTS.fpga.md'); Relative = $agentsTarget })
}

if (($mappings | Where-Object { $_.Relative -like '.codex/agents/*.toml' }).Count -ne 13) {
    throw 'Package must contain exactly 13 agent TOML files.'
}

$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$plan = foreach ($mapping in $mappings) {
    $destination = Join-Path $targetRoot ($mapping.Relative -replace '/', [IO.Path]::DirectorySeparatorChar)
    $sourceHash = (Get-FileHash -LiteralPath $mapping.Source -Algorithm SHA256).Hash
    $existing = Test-Path -LiteralPath $destination -PathType Leaf
    $same = $existing -and ((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash -eq $sourceHash)
    if ($existing -and -not $same -and -not $Force) {
        throw "Refusing to overwrite different content: $destination. Re-run with -Force to back up first."
    }
    [pscustomobject]@{
        Source = $mapping.Source
        Relative = $mapping.Relative
        Destination = $destination
        SourceHash = $sourceHash
        Same = $same
        Backup = if ($existing -and -not $same) { "$destination.backup-$timestamp" } else { $null }
    }
}

$installed = [Collections.Generic.List[object]]::new()
foreach ($item in $plan) {
    if (-not $item.Same -and $PSCmdlet.ShouldProcess($item.Destination, 'Install workflow file')) {
        $parent = Split-Path -Parent $item.Destination
        if (-not (Test-Path -LiteralPath $parent -PathType Container)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
        if ($null -ne $item.Backup) { Copy-Item -LiteralPath $item.Destination -Destination $item.Backup }
        Copy-Item -LiteralPath $item.Source -Destination $item.Destination
    }
    if (-not $WhatIfPreference) {
        $installed.Add([pscustomobject]@{
            relativePath = $item.Relative
            sha256 = $item.SourceHash
            backupPath = if ($null -ne $item.Backup) { Get-RelativePortablePath -Base $targetRoot -Path $item.Backup } else { $null }
        })
    }
}

if (-not $WhatIfPreference -and $PSCmdlet.ShouldProcess($manifestPath, 'Write install manifest')) {
    $manifestParent = Split-Path -Parent $manifestPath
    if (-not (Test-Path -LiteralPath $manifestParent -PathType Container)) { New-Item -ItemType Directory -Path $manifestParent -Force | Out-Null }
    $manifest = [ordered]@{
        schemaVersion = 1
        package = 'codex-fpga-engineering-workflow'
        packageVersion = (Get-Content -LiteralPath (Join-Path $packageRoot 'VERSION') -Raw).Trim()
        scope = $Scope
        installedAtUtc = [DateTime]::UtcNow.ToString('o')
        files = $installed
    }
    $json = $manifest | ConvertTo-Json -Depth 6
    [IO.File]::WriteAllText($manifestPath, $json + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
}

Write-Host "Installed $($mappings.Count) files for $Scope scope. Start a new Codex session, then run verify-install.ps1."
