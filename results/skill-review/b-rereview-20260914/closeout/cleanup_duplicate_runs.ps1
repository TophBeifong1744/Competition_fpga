$ErrorActionPreference = 'Stop'
$rawRoot = (Resolve-Path -LiteralPath 'F:/NUEC/review-evidence/skills-b-rereview-20260914').Path
$archiveRoot = (Resolve-Path -LiteralPath 'F:/NUEC/review-worktrees/member-b-to-a-pkg-b-alg/results/skill-review/b-rereview-20260914').Path
$names = @('d-independent','independent-d','skl002-units','skl002-receive','skl002-timeout','skl002-structure','skl002-postmerge-units','s-independent','independent-s','skl001-units','skl001-structure','skl001-examples','xsim-examples','skl001-result-audit','skl001-result-audit-r2','skl001-postmerge-units','skl001-postmerge-examples','xsim-postmerge')
$records = @()
foreach ($name in $names) {
  $target = (Resolve-Path -LiteralPath (Join-Path $rawRoot $name)).Path
  if (-not $target.StartsWith($rawRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw "Delete target escaped evidence root: $target" }
  $verified = 0; $rebuildable = @()
  foreach ($file in Get-ChildItem -LiteralPath $target -Recurse -File -Force) {
    $relative = $file.FullName.Substring($target.Length + 1)
    $archived = Join-Path (Join-Path $archiveRoot $name) $relative
    if (Test-Path -LiteralPath $archived -PathType Leaf) {
      if ((Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $archived -Algorithm SHA256).Hash) { throw "Archive byte mismatch: $relative" }
      $verified++
    } elseif (($relative.Split([IO.Path]::DirectorySeparatorChar) -contains 'work') -and $file.Extension -notin @('.log','.jou','.tcl')) {
      $rebuildable += @{path=$relative; bytes=$file.Length; sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant(); type='Generated simulator cache or duplicate work input; rerun archived case and sources'}
    } else { throw "Unique unarchived material: $relative" }
  }
  Remove-Item -LiteralPath $target -Recurse
  $records += @{path=$target; archived_at=(Join-Path $archiveRoot $name); verified_files=$verified; removed_rebuildable=$rebuildable; removed=$true}
}
$records | ConvertTo-Json -Depth 12 | Set-Content -Encoding utf8 -LiteralPath (Join-Path $rawRoot 'duplicate-run-cleanup.json')
$records | ForEach-Object { Write-Output ($_.path + ': ' + $_.verified_files) }
