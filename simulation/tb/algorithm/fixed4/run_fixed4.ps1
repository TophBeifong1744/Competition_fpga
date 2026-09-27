param(
  [Parameter(Mandatory=$true)][string]$OutputDirectory,
  [string]$VivadoBin = 'F:/AMD/2025.2/Vivado/bin'
)
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))
$diag = [IO.Path]::GetFullPath((Join-Path $repo 'codex_out'))
$out = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $out) { throw 'OutputDirectory must be new; existing evidence is immutable' }
if (![IO.Path]::GetFileName($out).StartsWith('i14-fixed4-evidence-repair-',[StringComparison]::OrdinalIgnoreCase)) {
  throw 'OutputDirectory name must start i14-fixed4-evidence-repair-'
}
if (!$out.StartsWith($diag.TrimEnd('\','/')+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {
  throw 'OutputDirectory must be a child of repository codex_out'
}
$walk = [IO.Path]::GetDirectoryName($out)
while ($walk -and !$walk.Equals($repo,[StringComparison]::OrdinalIgnoreCase)) {
  if ((Test-Path -LiteralPath $walk) -and ((Get-Item -LiteralPath $walk -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    throw "Reparse point in output path: $walk"
  }
  $walk = [IO.Path]::GetDirectoryName($walk)
}
$rtl = Join-Path $repo 'project/rtl/algorithm/fixed4/fixed4_leaf.sv'
$tb = Join-Path $PSScriptRoot 'tb_fixed4.sv'
$fixture = Join-Path $PSScriptRoot 'fixed4_145_inputs.svh'
$expectedRtlHash = '1F2A47956B34872F2625FCB262166EEE73D88044C84415C8DEDB0E3258254EFA'
$expectedFixtureHash = 'B33788B9D4A42DAA9925DD637340275B918CFF3EE1F3C41C615AE0A2B4FB6598'
if ((Get-FileHash -LiteralPath $rtl -Algorithm SHA256).Hash -ne $expectedRtlHash) { throw 'Frozen fixed4 RTL hash changed' }
foreach ($path in @($rtl,$tb,$fixture,$PSCommandPath)) { if (!(Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing source: $path" } }
if ((Get-FileHash -LiteralPath $fixture -Algorithm SHA256).Hash -ne $expectedFixtureHash) { throw 'Prepared input fixture hash changed' }
foreach ($name in @('xvlog.bat','xelab.bat','xsim.bat')) {
  if (!(Test-Path -LiteralPath (Join-Path $VivadoBin $name) -PathType Leaf)) { throw "Missing Vivado tool: $name" }
}
New-Item -ItemType Directory -Path $out | Out-Null
$manifest = [ordered]@{
  claim_stage='FUNCTIONAL_SIM'; status='RUNNING'; cwd=$out; vivado_bin=[IO.Path]::GetFullPath($VivadoBin)
  source_files=@(@{path=$rtl;sha256=(Get-FileHash $rtl -Algorithm SHA256).Hash},@{path=$tb;sha256=(Get-FileHash $tb -Algorithm SHA256).Hash},@{path=$fixture;sha256=(Get-FileHash $fixture -Algorithm SHA256).Hash},@{path=$PSCommandPath;sha256=(Get-FileHash $PSCommandPath -Algorithm SHA256).Hash})
  prepared_inputs=@{count=145;origin_commit='cb9118582f3ea09c47cb53e9141f395cbb3ee832';origin_blob='41c6e4ccbde45310a79dac844fb6312a5694e9fe';fixture_sha256=$expectedFixtureHash;use='input_s29 only'}
  tool_files=@(@('xvlog.bat','xelab.bat','xsim.bat') | ForEach-Object { $p=Join-Path $VivadoBin $_; @{path=$p;sha256=(Get-FileHash $p -Algorithm SHA256).Hash} })
  cases=@(); verdict_probes=@(); failure=$null
}
function Assert-NegativeEvidence([string]$caseName,[string]$checker,[string]$nativeLog,[object[]]$stageExits) {
  if ($stageExits.Count -ne 3 -or @($stageExits | Where-Object { $_ -ne 0 }).Count -ne 0) {
    throw "Tool stage failed in $caseName"
  }
  if ($nativeLog -match 'FIXED4_PASS') { throw "PASS marker in negative case $caseName" }
  $mark = "CANARY_INJECT case=$caseName checker=$checker"
  if ($nativeLog -notmatch [regex]::Escape($mark)) { throw "Missing injection identity in $caseName" }
  $first = [regex]::Match($nativeLog,'(?m)^(?:FIXED4_FAIL.*|Fatal:.*|ERROR:.*)$')
  if (!$first.Success) { throw "Missing first native failure in $caseName" }
  if ($caseName -eq 'reset') {
    if ($first.Value -notmatch '^Fatal: ILLEGAL_RESET_ASSERT case=reset checker=ILLEGAL_RESET_ASSERT\b') { throw "Wrong first checker in $caseName" }
    if ($nativeLog -notmatch '(?m)^Fatal: ILLEGAL_RESET_ASSERT case=reset checker=ILLEGAL_RESET_ASSERT') { throw 'Missing native reset Fatal' }
  } else {
    if ($first.Value -notmatch "^FIXED4_FAIL case=$([regex]::Escape($caseName)) checker=$([regex]::Escape($checker))\b") { throw "Wrong first checker in $caseName" }
    if ($nativeLog -notmatch '(?m)^Fatal: FIXED4_FAIL\s*$') { throw "Missing native FIXED4_FAIL Fatal in $caseName" }
  }
  $injectAt=$nativeLog.IndexOf($mark,[StringComparison]::Ordinal)
  $failureAt=$nativeLog.IndexOf($first.Value,[StringComparison]::Ordinal)
  if ($injectAt -lt 0 -or $injectAt -ge $failureAt) { throw "Injection did not precede first failure in $caseName" }
  return $first.Value.Trim()
}
function Assert-ProbeRejected([string]$name,[string]$log,[object[]]$exits) {
  try { [void](Assert-NegativeEvidence 'numeric' 'm_re' $log $exits) }
  catch { $manifest.verdict_probes += @{name=$name;result='REJECTED';reason=$_.Exception.Message}; return }
  throw "Verdict probe was falsely accepted: $name"
}
$probeMark='CANARY_INJECT case=numeric checker=m_re cycle=4'
Assert-ProbeRejected 'marker_only_normal_exit' $probeMark @(0,0,0)
Assert-ProbeRejected 'wrong_checker_first' "$probeMark`nFIXED4_FAIL case=numeric checker=m_valid cycle=4`nFatal: FIXED4_FAIL" @(0,0,0)
Assert-ProbeRejected 'tool_stage_failed' "$probeMark`nFIXED4_FAIL case=numeric checker=m_re cycle=4`nFatal: FIXED4_FAIL" @(0,1,0)
function RecordStage([string]$exe,[string[]]$argv,[string]$logPath,[hashtable]$caseRecord) {
  $record=[ordered]@{tool=$exe;args=$argv;cwd=(Get-Location).Path;log=$logPath;exit_code=$null;log_sha256=$null}
  $caseRecord.stages += $record
  & (Join-Path $VivadoBin $exe) @argv *> $logPath
  $record.exit_code=$LASTEXITCODE
  if (Test-Path -LiteralPath $logPath) { $record.log_sha256=(Get-FileHash -LiteralPath $logPath -Algorithm SHA256).Hash }
  if ($LASTEXITCODE -ne 0) { throw "$exe failed with exit $LASTEXITCODE; $logPath" }
}
try {
  foreach ($variant in @(
    @{name='functional';plusarg='CASE_FUNCTIONAL';checker=$null},
    @{name='numeric_canary';plusarg='CASE_NUMERIC';checker='m_re'},
    @{name='sideband_canary';plusarg='CASE_SIDEBAND';checker='m_numeric_valid'},
    @{name='timing_canary';plusarg='CASE_TIMING';checker='m_valid'},
    @{name='tag_canary';plusarg='CASE_TAG';checker='m_bin'},
    @{name='fault_canary';plusarg='CASE_FAULT';checker='fault_bin'},
    @{name='snapshot_canary';plusarg='CASE_SNAPSHOT';checker='terminal_causes'},
    @{name='ack_retire_canary';plusarg='CASE_ACK_RETIRE';checker='terminal_saved'},
    @{name='commit_canary';plusarg='CASE_COMMIT';checker='manager_commit_gate'},
    @{name='reset_canary';plusarg='CASE_RESET';checker='ILLEGAL_RESET_ASSERT'}
  )) {
    $job = Join-Path $out $variant.name
    New-Item -ItemType Directory -Path $job | Out-Null
    $caseRecord=@{name=$variant.name;seed='5a17c0de';status='RUNNING';stages=@();sim_log_sha256=$null;waveform=$null;first_failure=$null}
    $manifest.cases += $caseRecord
    Push-Location $job
    try {
      RecordStage 'xvlog.bat' @('--sv','-i',$PSScriptRoot,$rtl,$tb) (Join-Path $job 'compile.log') $caseRecord
      $elabArgs=@('work.tb_fixed4','-s','fixed4_test','-timescale','1ns/1ps')
      if ($variant.name -eq 'functional') { $elabArgs+=@('--debug','typical') }
      RecordStage 'xelab.bat' $elabArgs (Join-Path $job 'elaborate.log') $caseRecord
      $elabText=Get-Content -LiteralPath (Join-Path $job 'elaborate.log') -Raw
      $banner=[regex]::Match($elabText,'(?im)^.*Vivado Simulator v20\d\d\.\d.*$')
      $caseRecord.tool_version_banner=if($banner.Success){$banner.Value.Trim()}else{'UNVERIFIED; inspect elaborate.log'}
      $simLog=Join-Path $job 'simulation.log'
      $args=@('fixed4_test')
      if ($variant.name -eq 'functional') {
        $tcl=Join-Path $job 'waves.tcl'
        Set-Content -LiteralPath $tcl -Encoding ascii -Value @('log_wave -r /tb_fixed4/*','run -all','quit')
        $wdb=Join-Path $job 'fixed4.wdb'
        $caseRecord.tcl=@{path=$tcl;sha256=(Get-FileHash $tcl -Algorithm SHA256).Hash}
        $args+=@('-tclbatch','waves.tcl','-wdb','fixed4.wdb','-log','simulation.log')
      } else {
        $args+=@('-runall','-log','simulation.log')
      }
      if ($variant.plusarg) { $args+=@('-testplusarg',$variant.plusarg) }
      $simStage=[ordered]@{tool='xsim.bat';args=$args;cwd=$job;log=(Join-Path $job 'run.log');exit_code=$null;log_sha256=$null}
      $caseRecord.stages += $simStage
      & (Join-Path $VivadoBin 'xsim.bat') @args *> $simStage.log
      $simStage.exit_code=$LASTEXITCODE
      if (Test-Path -LiteralPath $simStage.log) { $simStage.log_sha256=(Get-FileHash $simStage.log -Algorithm SHA256).Hash }
      if (!(Test-Path -LiteralPath $simLog)) { throw "Missing simulator log: $job" }
      $caseRecord.sim_log_sha256=(Get-FileHash $simLog -Algorithm SHA256).Hash
      $log=(Get-Content -LiteralPath $simLog -Raw)+(Get-Content -LiteralPath $simStage.log -Raw)
      $simBanner=[regex]::Match($log,'(?im)^.*xsim v20\d\d\.\d.*$')
      $caseRecord.sim_version_banner=if($simBanner.Success){$simBanner.Value.Trim()}else{'UNVERIFIED; inspect run.log'}
      if ($variant.name -eq 'functional' -and (Test-Path -LiteralPath $wdb -PathType Leaf)) {
        $caseRecord.waveform=@{path=$wdb;bytes=(Get-Item -LiteralPath $wdb).Length;sha256=(Get-FileHash $wdb -Algorithm SHA256).Hash}
      }
      if ($variant.checker) {
        $caseKey=$variant.name -replace '_canary$',''
        $caseRecord.first_failure=Assert-NegativeEvidence $caseKey $variant.checker (Get-Content -LiteralPath $simLog -Raw) @($caseRecord.stages | ForEach-Object { $_.exit_code })
        $caseRecord.status='EXPECTED_CANARY_FAILURE'
      } else {
        if ($simStage.exit_code -ne 0 -or $log -notmatch 'FIXED4_PASS checks=' -or $log -match '(?im)(FIXED4_FAIL|FIXED4_TIMEOUT_HANG|ILLEGAL_RESET_ASSERT|^\s*(ERROR:|FATAL:))') {
          throw 'Functional simulation failed or PASS marker absent'
        }
        if (!$caseRecord.waveform -or $caseRecord.waveform.bytes -le 0) { throw 'Functional PASS lacks nonempty native WDB' }
        $csv=Join-Path $job 'cycle-proof.csv'
        if (!(Test-Path -LiteralPath $csv -PathType Leaf)) { throw 'Missing cycle-proof.csv' }
        $rows=Import-Csv -LiteralPath $csv
        $required=@('first_beat','stall_before_resume','resume_e_old_t_new_s','fault_commit','first_ack_retire','kill_retire','last_beat_cancel')
        foreach ($window in $required) {
          if (@($rows | Where-Object { $_.window -eq $window -and $_.phase -eq 'pre' }).Count -lt 1 -or
              @($rows | Where-Object { $_.window -eq $window -and $_.phase -eq 'post' }).Count -lt 1) {
            throw "Incomplete cycle proof window: $window"
          }
        }
        foreach ($row in $rows) {
          foreach ($base in @('s_ready','m_valid','causes','fault','commit','t','s_transfer',
                               'ctx_active','active_ctx','terminal_saved','terminal_cancelled',
                               'terminal_n','terminal_p','terminal_untransferred','terminal_t_bin',
                               'data_done','terminal_ctx')) {
            if ($row."${base}_actual" -ne $row."${base}_expected") { throw "Cycle proof mismatch $($row.window)/$($row.phase)/$base" }
          }
          if ($row.m_valid_actual -eq '1') {
            foreach ($base in @('m_ctx','m_bin','m_re','m_im')) {
              if ($row."${base}_actual" -ne $row."${base}_expected") { throw "Cycle proof mismatch $($row.window)/$($row.phase)/$base" }
            }
          }
        }
        $caseRecord.cycle_proof=@{path=$csv;rows=@($rows).Count;sha256=(Get-FileHash $csv -Algorithm SHA256).Hash;windows=$required}
        $ledger=Join-Path $job 'transaction-ledger.csv'
        if (!(Test-Path -LiteralPath $ledger -PathType Leaf)) { throw 'Missing transaction-ledger.csv' }
        $transactions=@(Import-Csv -LiteralPath $ledger)
        if ($transactions.Count -lt 1025) { throw "Too few transaction comparisons: $($transactions.Count)" }
        foreach ($tx in $transactions) {
          if ([int]$tx.accepted_cycle -lt 0 -or [int]$tx.due_cycle -ne ([int]$tx.accepted_cycle+1) -or [int]$tx.observed_cycle -lt [int]$tx.due_cycle) { throw "Bad transaction edge: ctx=$($tx.ctx) bin=$($tx.bin)" }
          foreach ($base in @('re','im','numeric_valid','ov_re')) {
            if ($tx."expected_$base" -ne $tx."actual_$base") { throw "Transaction mismatch: ctx=$($tx.ctx) bin=$($tx.bin) field=$base" }
          }
        }
        $caseRecord.transaction_ledger=@{path=$ledger;rows=$transactions.Count;sha256=(Get-FileHash $ledger -Algorithm SHA256).Hash}
        $acceptedPath=Join-Path $job 'accepted-ledger.csv'
        if (!(Test-Path -LiteralPath $acceptedPath -PathType Leaf)) { throw 'Missing accepted-ledger.csv' }
        $accepted=@(Import-Csv -LiteralPath $acceptedPath)
        if ($accepted.Count -lt 1029) { throw "Too few accepted-input records: $($accepted.Count)" }
        foreach ($entry in $accepted) {
          if ([int]$entry.accepted_cycle -lt 0 -or [int]$entry.due_cycle -ne ([int]$entry.accepted_cycle+1) -or [int]$entry.observed_cycle -lt 0 -or
              $entry.result -notin @('MATCH','CANCELLED_PHYSICAL','CANCELLED_UNTRANSFERRED','CANCELLED_AT_ACCEPT')) {
            throw "Undrained/bad accepted token: ctx=$($entry.ctx) bin=$($entry.bin)"
          }
          if ($entry.result -in @('MATCH','CANCELLED_PHYSICAL') -and [int]$entry.observed_cycle -lt [int]$entry.due_cycle) {
            throw "Output earlier than due edge: ctx=$($entry.ctx) bin=$($entry.bin)"
          }
        }
        $caseRecord.accepted_ledger=@{path=$acceptedPath;rows=$accepted.Count;sha256=(Get-FileHash $acceptedPath -Algorithm SHA256).Hash}
        $caseRecord.status='SELF_CHECKED_PASS_PENDING_INDEPENDENT_REVIEW'
      }
    } finally { Pop-Location }
  }
  $manifest.status='SELF_CHECKED_PASS_PENDING_INDEPENDENT_REVIEW'
} catch {
  $manifest.status='FAILED_OR_INCONCLUSIVE'; $manifest.failure=$_.Exception.Message
  throw
} finally {
  $manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $out 'run-manifest.json') -Encoding utf8
  $functional=@($manifest.cases | Where-Object { $_.name -eq 'functional' }) | Select-Object -First 1
  $negative=@($manifest.cases | Where-Object { $_.name -ne 'functional' })
  $evidence=[ordered]@{
    schema_version='1.0.0';run_id=[IO.Path]::GetFileName($out);snapshot_id='e3483410077fbfbf87cac62fccec916144b84286'
    evidence_profile='FUNCTIONAL_ACCEPTANCE';classification='INCONCLUSIVE'
    compile_exit_code=if($functional -and $functional.stages.Count -ge 1){[int]$functional.stages[0].exit_code}else{-1}
    elaboration_exit_code=if($functional -and $functional.stages.Count -ge 2){[int]$functional.stages[1].exit_code}else{-1}
    run_exit_code=if($functional -and $functional.stages.Count -ge 3){[int]$functional.stages[2].exit_code}else{-1}
    tests_discovered=10;tests_executed=@($manifest.cases | Where-Object { $_.status -ne 'RUNNING' }).Count
    scoreboard_drained=($manifest.status -eq 'SELF_CHECKED_PASS_PENDING_INDEPENDENT_REVIEW')
    comparisons=if($functional -and $functional.accepted_ledger){@($accepted | ForEach-Object { @{tag="$($_.ctx):$($_.bin)";accepted_cycle=[int]$_.accepted_cycle;expected_cycle=[int]$_.due_cycle;observed_cycle=[int]$_.observed_cycle;result=$_.result;expected_re=$_.expected_re;expected_im=$_.expected_im;expected_numeric_valid=$_.expected_numeric_valid;expected_ov_re=$_.expected_ov_re;expected_ov_im=$_.expected_ov_im} })}else{@()}
    negative_canaries=@($negative | ForEach-Object { @{fault=$_.name;detected=($_.status -eq 'EXPECTED_CANARY_FAILURE');first_failure=$_.first_failure} })
    proof_packet=if($functional -and $functional.cycle_proof){@($functional.cycle_proof.path,$functional.accepted_ledger.path,$functional.transaction_ledger.path,$functional.waveform.path)}else{@()}
    first_failure=@{classification='INCONCLUSIVE';reason='Acceptance assets and native evidence require independent read-only review';runner_failure=$manifest.failure}
  }
  $evidence | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $out 'simulation-evidence.json') -Encoding utf8
}
