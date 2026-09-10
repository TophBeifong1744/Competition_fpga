# Run after finalizing evidence: & ./scripts/update_manifest.ps1
# Output: file-manifest.json. Next: inspect diff and submit for review.
$ErrorActionPreference='Stop'
$package=Split-Path $PSScriptRoot -Parent
$entries=@(Get-ChildItem -LiteralPath $package -Recurse -File -Force |
 Where-Object {$_.FullName -ne (Join-Path $package 'file-manifest.json')} |
 Sort-Object FullName | ForEach-Object {
 [ordered]@{path=$_.FullName.Substring($package.Length+1).Replace('\','/');bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName).Hash.ToLowerInvariant()}
 })
ConvertTo-Json -InputObject $entries -Depth 4 | Set-Content -LiteralPath (Join-Path $package 'file-manifest.json') -Encoding utf8
