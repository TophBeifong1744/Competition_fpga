param(
    [string]$PythonPath = 'python',
    [string]$OutputDirectory = ''
)
# Run from any directory: .\run_all.ps1 -PythonPath 'D:\Python\python.exe'
# Outputs: a new result directory with raw data, plots and verification records.
# Next: compare real purchased hardware parameters with the report before adaptation.
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = Join-Path $PSScriptRoot ('results-reproduced-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
}
& $PythonPath (Join-Path $PSScriptRoot 'simulate.py') --out $OutputDirectory
if ($LASTEXITCODE -ne 0) { throw 'Physical simulation execution failed.' }
& $PythonPath (Join-Path $PSScriptRoot 'validate_control.py') --out $OutputDirectory
if ($LASTEXITCODE -ne 0) { throw 'Supervisory checks failed.' }
$check = Get-Content -LiteralPath (Join-Path $OutputDirectory 'verification.json') -Raw | ConvertFrom-Json
if ($check.position_pass_count -ne $check.case_count -or
    $check.settle_pass_count -ne $check.case_count -or
    $check.sync_margin_pass_count -ne $check.case_count -or
    -not $check.dt_refinement_pass -or -not $check.negative_control_detected -or
    -not $check.controlled_stop_case.pass_position -or -not $check.controlled_stop_case.pass_settle) {
    throw 'One or more physical model acceptance checks failed. Inspect verification.json.'
}
foreach ($item in $check.reversal_cases) {
    if (-not $item.pass_position -or -not $item.pass_settle -or -not $item.model_sync_margin_ok) {
        throw 'Reversal check failed.'
    }
}
if ($check.stopping.total_with_elastic_and_1p5deg_tolerance -ge 10) {
    throw 'Stopping space budget failed.'
}
Write-Output "Model checks passed. Results: $OutputDirectory"
