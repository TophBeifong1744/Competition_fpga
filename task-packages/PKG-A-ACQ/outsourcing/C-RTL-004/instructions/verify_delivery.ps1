param([Parameter(Mandatory=$true)][string]$SubmissionDirectory)
$ErrorActionPreference = 'Stop'
$base = (Resolve-Path -LiteralPath $SubmissionDirectory).Path.TrimEnd('\','/')
$manifestPath = Join-Path $base 'file-manifest.json'
$entries = @(Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json)
if ($entries.Count -eq 0) { throw 'Empty manifest' }
$paths = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$issues = [Collections.Generic.List[string]]::new()
foreach ($entry in $entries) {
    $relative = [string]$entry.path
    if ([string]::IsNullOrWhiteSpace($relative) -or [IO.Path]::IsPathRooted($relative)) {
        $issues.Add("Invalid path: $relative"); continue
    }
    $full = [IO.Path]::GetFullPath((Join-Path $base $relative))
    if (!$full.StartsWith($base + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        $issues.Add("Outside submission: $relative"); continue
    }
    if ($full -eq $manifestPath) { $issues.Add('Manifest must not include itself'); continue }
    $relative = $relative.Replace('\','/')
    if (!$paths.Add($relative)) { $issues.Add("Duplicate path: $relative") }
    if (!(Test-Path -LiteralPath $full -PathType Leaf)) { $issues.Add("Missing: $relative"); continue }
    $file = Get-Item -LiteralPath $full
    $hash = (Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash
    if ($file.Length -ne $entry.bytes -or $hash -ine $entry.sha256) { $issues.Add("Mismatch: $relative") }
}
foreach ($file in Get-ChildItem -LiteralPath $base -Recurse -File -Force) {
    if ($file.FullName -eq $manifestPath) { continue }
    $relative = $file.FullName.Substring($base.Length + 1).Replace('\','/')
    if (!$paths.Contains($relative)) { $issues.Add("Unlisted: $relative") }
}
if ($issues.Count) { throw ($issues -join [Environment]::NewLine) }
Write-Output "DELIVERY_MANIFEST_PASS files=$($entries.Count)"
