$ErrorActionPreference = 'Stop'
$reviewRoot = [IO.Path]::GetFullPath('F:/NUEC/review-worktrees')
$mainTree = 'F:/NUEC/review-worktrees/member-b-to-a-pkg-b-alg'
$audit = Get-Content -Raw -Encoding utf8 -LiteralPath 'F:/NUEC/review-evidence/skills-b-rereview-20260914/materials-before-cleanup.json' | ConvertFrom-Json
$expected = @{
  'b-skl001-a7e1ea9' = 'a7e1ea976da91ba735af5c0a79fffdc7d10c121f'
  'b-skl002-3ac597d' = '3ac597d1d16982e0a5c5a114202ca8568dc28d8f'
  'b-skl001-c562466' = 'c562466805aff08201cd457cc2e6ee7464a3566f'
  'b-skl002-55039cf' = '55039cf8bfab2bd6112192c8bd646d427a52a642'
}
$deleted = @()
foreach ($name in $expected.Keys) {
  $target = (Resolve-Path -LiteralPath (Join-Path $reviewRoot $name)).Path
  if (-not $target.StartsWith($reviewRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw "Target escaped review root: $target" }
  $head = & git -c "safe.directory=$target" -C $target rev-parse HEAD
  if ($LASTEXITCODE -ne 0 -or $head -ne $expected[$name]) { throw "Unexpected worktree identity: $target" }
  $entry = $audit.worktrees | Where-Object { [IO.Path]::GetFullPath($_.path) -eq $target }
  if (-not $entry -or $entry.ignored_scoped_count -ne 0) { throw "Missing clean materials audit: $target" }
  $state = @(& git -c "safe.directory=$target" -C $target status --porcelain=v1 --untracked-files=all)
  if ($LASTEXITCODE -ne 0 -or $state.Count -ne $entry.files.Count) { throw "New work appeared: $target" }
  foreach ($file in $entry.files) {
    $candidateFile = (Resolve-Path -LiteralPath (Join-Path $target $file.path)).Path
    if (-not $candidateFile.StartsWith($target + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'File escaped worktree' }
    $digest = (Get-FileHash -LiteralPath $candidateFile -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($digest -ne $file.sha256 -or $file.archived_exact_matches.Count -eq 0) { throw 'Unarchived data' }
    $matched = $false
    foreach ($archived in $file.archived_exact_matches) {
      if ((Test-Path -LiteralPath $archived) -and (Get-FileHash -LiteralPath $archived -Algorithm SHA256).Hash.ToLowerInvariant() -eq $digest) { $matched = $true }
    }
    if (-not $matched) { throw 'Archive verification failed' }
    Remove-Item -LiteralPath $candidateFile
  }
  & git -c "safe.directory=$mainTree" -C $mainTree worktree remove -- $target
  if ($LASTEXITCODE -ne 0) { throw "Worktree removal failed: $target" }
  $deleted += @{path=$target; head=$head; archived_extra_files=$entry.files; removed=$true}
}
$deleted | ConvertTo-Json -Depth 12 | Set-Content -Encoding utf8 -LiteralPath 'F:/NUEC/review-evidence/skills-b-rereview-20260914/worktree-cleanup.json'
$deleted | ForEach-Object { Write-Output $_.path }
