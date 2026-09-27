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
  cases=@(); failure=$null
}
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
    @{name='functional';plusarg=$null;expectedFailure=$null},
    @{name='checker_canary';plusarg='CANARY';expectedFailure='FIXED4_FAIL'},
    @{name='reset_canary';plusarg='ILLEGAL_RESET';expectedFailure='ILLEGAL_RESET_ASSERT'}
  )) {
    $job = Join-Path $out $variant.name
    New-Item -ItemType Directory -Path $job | Out-Null
    $caseRecord=@{name=$variant.name;seed='5a17c0de';status='RUNNING';stages=@();sim_log_sha256=$null;waveform=$null}
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
      if ($variant.expectedFailure) {
        if ($log -notmatch [regex]::Escape($variant.expectedFailure) -or $log -match 'FIXED4_PASS') {
          throw "Negative canary did not fail as expected: $($variant.name)"
        }
        $caseRecord.status='EXPECTED_CANARY_FAILURE'
      } else {
        if ($simStage.exit_code -ne 0 -or $log -notmatch 'FIXED4_PASS checks=' -or $log -match '(?im)(FIXED4_FAIL|FIXED4_TIMEOUT_HANG|ILLEGAL_RESET_ASSERT|^\s*(ERROR:|FATAL:))') {
          throw 'Functional simulation failed or PASS marker absent'
        }
        if (!$caseRecord.waveform -or $caseRecord.waveform.bytes -le 0) { throw 'Functional PASS lacks nonempty native WDB' }
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
}
