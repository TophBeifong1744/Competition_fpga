param(
 [Parameter(Mandatory=$true)][string]$OutputDirectory,
 [string]$VivadoBin='F:/AMD/2025.2/Vivado/bin'
)
$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$out=[IO.Path]::GetFullPath($OutputDirectory)
if(Test-Path -LiteralPath $out){throw 'Use a new output directory; previous evidence is immutable'}
$diagnostics=[IO.Path]::GetFullPath((Join-Path $repo 'codex_out'))
$prefix=$diagnostics.TrimEnd([IO.Path]::DirectorySeparatorChar)+[IO.Path]::DirectorySeparatorChar
if(!$out.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)){throw 'Use a new directory below repository codex_out'}
# Reject junction/symlink ancestors so a lexical child cannot escape codex_out.
$ancestor=[IO.Path]::GetDirectoryName($out)
while($ancestor -and !$ancestor.Equals($repo,[StringComparison]::OrdinalIgnoreCase)){
 if(Test-Path -LiteralPath $ancestor){
  if((Get-Item -LiteralPath $ancestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw "Reparse-point output ancestor is not allowed: $ancestor"}
 }
 $ancestor=[IO.Path]::GetDirectoryName($ancestor)
}
$manifest=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'modules.json') -Raw | ConvertFrom-Json
foreach($file in $manifest.files){
 $path=Join-Path $repo $file.target
 $normal=(Get-Content -LiteralPath $path -Raw).Replace("`r`n","`n")
 $hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($normal))).ToLowerInvariant()
 if($hash -ne $file.normalized_sha256){throw "Source changed: $($file.target); update approved manifest first"}
}
foreach($tool in @('xvlog.bat','xelab.bat','xsim.bat')){if(!(Test-Path -LiteralPath (Join-Path $VivadoBin $tool))){throw "Missing tool $tool"}}
New-Item -ItemType Directory -Path $out | Out-Null
$prior=$env:PROCESSOR_ARCHITECTURE
if(!$prior -and [Environment]::Is64BitOperatingSystem){$env:PROCESSOR_ARCHITECTURE='AMD64'}
$results=@()
$summary=[ordered]@{status='RUNNING';scope='Module source integration regression only';source_commit=$manifest.source_commit;manifest_sha256=(Get-FileHash (Join-Path $PSScriptRoot 'modules.json')).Hash;runner_sha256=(Get-FileHash $PSCommandPath).Hash;vivado_bin=$VivadoBin;not_run=@('synthesis','timing','board','four-channel capture','C004');cases=@()}
function InvokeChecked([string]$tool,[string[]]$toolArgs,[string]$log){
 & (Join-Path $VivadoBin $tool) @toolArgs 2>&1 | Out-File -LiteralPath $log -Encoding utf8
 if($LASTEXITCODE -ne 0){throw "$tool failed; see $log"}
}
try{
 foreach($case in $manifest.cases){
  $dir=Join-Path $out $case.name
  New-Item -ItemType Directory -Path $dir | Out-Null
  Push-Location $dir
  try{
   $v=@($case.sources | Where-Object {$_ -like '*.v'} | ForEach-Object {Join-Path $repo $_})
   $sv=@($case.sources | Where-Object {$_ -like '*.sv'} | ForEach-Object {Join-Path $repo $_})
   if($v.Count){InvokeChecked 'xvlog.bat' $v 'compile-v.txt'}
   if($sv.Count){InvokeChecked 'xvlog.bat' (@('--sv')+$sv) 'compile-sv.txt'}
   InvokeChecked 'xelab.bat' @("work.$($case.top)",'-s','dut_test','-timescale','1ns/1ps') 'elaborate.txt'
   InvokeChecked 'xsim.bat' @('dut_test','-runall','-log','simulation.log') 'simulate.txt'
   $log=Get-Content -LiteralPath 'simulation.log' -Raw
   if(!$log.Contains($case.marker) -or $log -match '(?im)^\s*(FAIL\b|Fatal:|ERROR:|REVIEW FAIL|REVIEW JOINT FAIL|REVIEW TIMEOUT)'){throw "Simulation failed or missing marker: $($case.name)"}
   $results+=[pscustomobject]@{name=$case.name;top=$case.top;status='PASS';marker=$case.marker;log_sha256=(Get-FileHash 'simulation.log').Hash}
   Write-Output "PASS $($case.name)"
  } finally {Pop-Location}
 }
 $summary.status='PASS_MODULE_REGRESSION'
}catch{
 $summary.status='FAILED_OR_BLOCKED'
 $summary.error=$_.Exception.Message
 throw
}finally{
 $summary.cases=$results
 $summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $out 'result.json') -Encoding utf8
 $env:PROCESSOR_ARCHITECTURE=$prior
}
