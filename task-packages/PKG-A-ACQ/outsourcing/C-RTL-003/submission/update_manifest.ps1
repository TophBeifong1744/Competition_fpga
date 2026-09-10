# Run after all package files/logs are final: & ./update_manifest.ps1
# Output: file-manifest.json (excludes itself). Next: review and commit the package.
$ErrorActionPreference = 'Stop'
$manifestRoot = $PSScriptRoot
$entries = @(Get-ChildItem -LiteralPath $manifestRoot -Recurse -File -Force |
    Where-Object { $_.FullName -ne (Join-Path $manifestRoot 'file-manifest.json') } |
    Sort-Object FullName | ForEach-Object {
        [ordered]@{
            path = $_.FullName.Substring($manifestRoot.Length + 1).Replace('\', '/')
            bytes = $_.Length
            sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    })
ConvertTo-Json -InputObject $entries -Depth 3 | Set-Content -LiteralPath (Join-Path $manifestRoot 'file-manifest.json') -Encoding utf8
