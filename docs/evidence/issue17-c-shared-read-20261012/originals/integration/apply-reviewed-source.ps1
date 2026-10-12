# 中文用途：单文件接入已复核的证据选字修复；不启动EDA、不编辑XPR或其他源。
# Run: powershell -NoProfile -ExecutionPolicy Bypass -File apply-reviewed-source.ps1
# Outputs: backup/, before.json, after.json, process-before.json, process-after.json, integration-receipt.json.
# Next: use the existing XPR; integrate current A/B increments before one coordinated human whole-project synthesis.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$taskRoot = 'C:\Users\hsc\Desktop\fpga_clone\Competition_fpga\codex_out\i17-evidence-shared-read-20261012\integration'
$repoRoot = 'C:\Users\hsc\Desktop\fpga_clone\Competition_fpga'
$nativeRoot = 'D:\vavido_project\i17_live_loop\project\par\i17_live_loop'
$candidate = Join-Path $repoRoot 'project\rtl\c_board\i17_vio_evidence.sv'
$nativeSource = Join-Path $nativeRoot 'i17_live_loop.srcs\sources_1\imports\i17-i19-live-loop-c-20261010\board-prep\rtl\i17_vio_evidence.sv'
$xpr = Join-Path $nativeRoot 'i17_live_loop.xpr'
$beforeSha = '135271131d893eba2b8e22a7b596c78292de4050a69855f131b5fe5a582fdfd6'
$candidateSha = 'a3cc8415a9d6875f94433319f71c0b861a3cc0c705a408d10af49863941e1fef'
function Sha([string]$path) { (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Processes {
    @(Get-CimInstance Win32_Process | Where-Object {
        $_.ProcessId -ne $PID -and ($_.Name -match '^(vivado|xvlog|xelab|xsim|rdi|loader).*\.exe$' -or
        ($_.Name -match '^(cmd|cscript|wscript)\.exe$' -and $_.CommandLine -like '*i17_live_loop.runs*'))
    } | Select-Object ProcessId,ParentProcessId,Name,CommandLine)
}
function Assert-NoBuild($processes) {
    $blocking = @($processes | Where-Object { $null -ne $_ -and -not ($_.Name -eq 'vivado.exe' -and $_.CommandLine -like '*-gui_launcher_event*') })
    if ($blocking.Count -ne 0) { throw ('Active build/simulator process detected: '+($blocking|ConvertTo-Json -Compress)) }
}
function Inventory {
    # 完整清点原工程（含IP/XDC/runs）和仓库RTL；只备份目标源与XPR。
    $paths = @(Get-ChildItem -LiteralPath $nativeRoot -Recurse -File -Force | ForEach-Object FullName)
    $paths += @(Get-ChildItem -LiteralPath (Join-Path $repoRoot 'project\rtl') -Recurse -File -Force | ForEach-Object FullName)
    @($paths | Sort-Object -Unique | ForEach-Object {
        $item = Get-Item -LiteralPath $_
        [pscustomobject]@{path=$item.FullName; bytes=$item.Length; mtime_utc=$item.LastWriteTimeUtc.ToString('o'); sha256=(Sha $item.FullName)}
    })
}
if (Test-Path -LiteralPath (Join-Path $taskRoot 'before.json')) {throw 'This receipt exists; refuse to overwrite the integration baseline.'}
if ((Sha $candidate) -ne $candidateSha) {throw 'Candidate differs from accepted SHA.'}
if ((Sha $nativeSource) -ne $beforeSha) {throw 'D source differs from reviewed preimage.'}
$expectedReference = '<File Path="$PSRCDIR/sources_1/imports/i17-i19-live-loop-c-20261010/board-prep/rtl/i17_vio_evidence.sv">'
if (-not (Get-Content -LiteralPath $xpr -Raw).Contains($expectedReference)) {throw 'Existing XPR reference changed.'}
$processBefore = @(Processes)
Assert-NoBuild $processBefore
ConvertTo-Json -InputObject @($processBefore) -Depth 4 | Set-Content -LiteralPath (Join-Path $taskRoot 'process-before.json') -Encoding UTF8
$before = Inventory
ConvertTo-Json -InputObject @($before) -Depth 5 | Set-Content -LiteralPath (Join-Path $taskRoot 'before.json') -Encoding UTF8
$backup = Join-Path $taskRoot 'backup'
New-Item -ItemType Directory -Path $backup -ErrorAction Stop | Out-Null
Copy-Item -LiteralPath $nativeSource -Destination (Join-Path $backup 'i17_vio_evidence.sv')
Copy-Item -LiteralPath $xpr -Destination (Join-Path $backup 'i17_live_loop.xpr')
if ((Sha (Join-Path $backup 'i17_vio_evidence.sv')) -ne $beforeSha) {throw 'Backup mismatch.'}
if ((Sha (Join-Path $backup 'i17_live_loop.xpr')) -ne (Sha $xpr)) {throw 'XPR backup mismatch.'}
# 复制前二次核活动进程和全体mtime/hash，防止与其他写入方并行更新。
Assert-NoBuild (Processes)
$stable = Inventory
if ((ConvertTo-Json -InputObject @($stable) -Depth 5 -Compress) -cne (ConvertTo-Json -InputObject @($before) -Depth 5 -Compress)) {throw 'Native or protected input changed while preparing backup.'}
$copyUtc = [DateTime]::UtcNow.ToString('o')
Copy-Item -LiteralPath $candidate -Destination $nativeSource -Force
if ((Sha $nativeSource) -ne $candidateSha) {throw 'Copied bytes do not match accepted candidate.'}
$after = Inventory
ConvertTo-Json -InputObject @($after) -Depth 5 | Set-Content -LiteralPath (Join-Path $taskRoot 'after.json') -Encoding UTF8
$beforeByPath = @{}
foreach ($item in $before) {$beforeByPath[$item.path]=$item}
$changed = @()
foreach ($item in $after) {
    if (-not $beforeByPath.ContainsKey($item.path)) {throw ('New unexpected file: '+$item.path)}
    $previous = $beforeByPath[$item.path]
    if ($item.sha256 -ne $previous.sha256 -or $item.mtime_utc -ne $previous.mtime_utc -or $item.bytes -ne $previous.bytes) {$changed += $item.path}
}
if ($before.Count -ne $after.Count -or $changed.Count -ne 1 -or $changed[0] -ne $nativeSource) {throw ('Unexpected differences: '+($changed -join ', '))}
$processAfter = @(Processes)
Assert-NoBuild $processAfter
ConvertTo-Json -InputObject @($processAfter) -Depth 4 | Set-Content -LiteralPath (Join-Path $taskRoot 'process-after.json') -Encoding UTF8
$receipt = [ordered]@{
    finding='C-EVID-SHARED-001'; primary_mode='RELEASE_PACKAGING'; operation='Accepted exact-byte single-file integration, no build';
    review='Independent PASS_WITH_SCOPE by /root/c_mux_review; bounded simulation and same-condition OOC resource improvement only; not A/B member approval';
    copy_utc=$copyUtc; xpr=$xpr; target=$nativeSource; source=$candidate;
    before_sha256=$beforeSha; after_sha256=$candidateSha; protected_inventory_count=$before.Count;
    changed_paths=@($changed); every_other_inventory_hash_and_mtime_unchanged=$true;
    xpr_sha256=(Sha $xpr); backup_source_sha256=(Sha (Join-Path $backup 'i17_vio_evidence.sv'));
    original_test_manifest_sha256='ac2298ddad9a34e3970ca98d9c1087e2526589b7b72bc38506e044c074b0fa28';
    open_findings=@('C-IMPL-LUT-001','C-AB-CTRL-001'); low_followup='C-EVID-SHARED-REV-001'; info_scope_limit='C-META-SH-001';
    eda_started=$false; board_action=$false; xpr_modified=$false; native_runs_modified=$false;
    source_registration='Existing XPR already references this same native file; no registration/topology change.'
}
$receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskRoot 'integration-receipt.json') -Encoding UTF8
$receipt | ConvertTo-Json -Depth 5
