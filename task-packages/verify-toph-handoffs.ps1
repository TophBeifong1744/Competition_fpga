param([ValidateSet('WP-A0','WP-S1','3D-P2','3D-P4','REL6-001')][string]$PackageId)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$ids = @('WP-A0','WP-S1','3D-P2','3D-P4','REL6-001')
if ($PackageId) { $ids = @($PackageId) }
$failures = 0
$drifts = 0
function Resolve-SafeFile([string]$Base, [string]$Relative) {
    $root = [IO.Path]::GetFullPath($Base).TrimEnd('\','/')
    $full = [IO.Path]::GetFullPath((Join-Path $root $Relative))
    if (-not $full.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Unsafe path: $Relative"
    }
    return $full
}
foreach ($id in $ids) {
    $packageRoot = Join-Path $PSScriptRoot $id
    $manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $packageRoot 'evidence/files.json') | ConvertFrom-Json
    if ($manifest.package_id -ne $id -or $manifest.reviewer -ne 'hsc119' -or $manifest.status -ne 'pending_review') {
        throw "Invalid package metadata: $id"
    }
    foreach ($required in @('README.md','REVIEW.md','manifest.md','evidence/self-check.md')) {
        if (-not (Test-Path -LiteralPath (Join-Path $packageRoot $required) -PathType Leaf)) { throw "Missing: $id/$required" }
    }
    foreach ($file in $manifest.payload) {
        $path = Resolve-SafeFile $packageRoot $file.package_path
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $failures++; Write-Output "FAIL missing payload: $id/$($file.package_path)"; continue }
        $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
        if ($actual -ne $file.sha256) { $failures++; Write-Output "FAIL payload hash: $id/$($file.package_path)" }
    }
    foreach ($file in $manifest.references) {
        if ($file.snapshot_path) {
            $snapshot = Resolve-SafeFile $packageRoot $file.snapshot_path
            if (-not (Test-Path -LiteralPath $snapshot -PathType Leaf)) {
                $failures++; Write-Output "FAIL missing reference snapshot: $id/$($file.snapshot_path)"
            } elseif ((Get-FileHash -Algorithm SHA256 -LiteralPath $snapshot).Hash.ToLowerInvariant() -ne $file.sha256) {
                $failures++; Write-Output "FAIL reference snapshot hash: $id/$($file.snapshot_path)"
            }
        } else {
            $failures++; Write-Output "FAIL unbundled reference: $($file.path)"
        }
        $path = Resolve-SafeFile $repoRoot $file.path
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $drifts++; Write-Output "REFERENCE MISSING: $($file.path)"; continue }
        $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
        if ($actual -ne $file.sha256) { $drifts++; Write-Output "REFERENCE DRIFT: $($file.path)" }
    }
    Write-Output "CHECKED $id : $(@($manifest.payload).Count) payload, $(@($manifest.references).Count) references; human approval pending"
}
Write-Output "SUMMARY payload_failures=$failures reference_drifts=$drifts"
Write-Output 'Historical manifest anomalies and scientific limitations remain in evidence/self-check.md; this is not human approval.'
if ($failures -gt 0) { exit 1 }
# Source checkout drift is diagnostic only when the exact reviewed snapshot is bundled.
# The historical snapshot's own manifest must still be checked separately.
exit 0
