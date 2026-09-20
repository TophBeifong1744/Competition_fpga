param([string]$Repo, [string]$Output)
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $Output) { throw 'Output exists' }
Set-Location -LiteralPath $Repo
$before = git rev-parse HEAD
$target = git rev-parse origin/main
$tree = @{}
git -c core.quotePath=false ls-tree -r $target | ForEach-Object {
    if ($_ -match '^\d+ blob ([0-9a-f]+)\t(.+)$') { $tree[$Matches[2]] = $Matches[1] }
}
$rows = @()
git -c core.quotePath=false diff --name-only --diff-filter=A $before $target | ForEach-Object {
    $rel = $_
    if (Test-Path -LiteralPath $rel -PathType Leaf) {
        $hash = git hash-object --no-filters -- $rel
        if ($LASTEXITCODE -ne 0) { throw "Hash failed: $rel" }
        $rows += [ordered]@{ path=$rel; local_blob=$hash; target_blob=$tree[$rel]; exact=($hash -eq $tree[$rel]); sha256=(Get-FileHash -LiteralPath $rel -Algorithm SHA256).Hash }
    }
}
$report = [ordered]@{ before=$before; target=$target; collisions=$rows.Count; unequal=@($rows | Where-Object {-not $_.exact}).Count; files=$rows }
$report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $Output -Encoding utf8
[pscustomobject]$report | Select-Object before,target,collisions,unequal | ConvertTo-Json
