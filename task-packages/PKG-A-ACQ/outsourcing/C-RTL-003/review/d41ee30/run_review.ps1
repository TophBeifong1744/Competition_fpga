param([Parameter(Mandatory=$true)][string]$OutputDirectory,[string]$VivadoBin='F:/AMD/2025.2/Vivado/bin')
$ErrorActionPreference='Stop'
$src=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../submission'))
$out=[IO.Path]::GetFullPath($OutputDirectory)
if(Test-Path $out){throw 'Use a new directory'}
if($out.StartsWith($src,[StringComparison]::OrdinalIgnoreCase)){throw 'Output must be outside submission'}
$prior=$env:PROCESSOR_ARCHITECTURE
if(!$prior -and [Environment]::Is64BitOperatingSystem){$env:PROCESSOR_ARCHITECTURE='AMD64'}
try {
 foreach($mode in @('author','independent')){
  New-Item -ItemType Directory -Path "$out/$mode" | Out-Null
  Push-Location "$out/$mode"
  try {
   & "$VivadoBin/xvlog.bat" "$src/rtl/pcm4_signext_pack.v" "$src/tb/tb_pcm4_signext_pack.v"
   if($LASTEXITCODE -ne 0){throw 'Verilog compile failed'}
   $top='tb_pcm4_signext_pack';$marker='ALL TESTS PASS'
   if($mode -eq 'independent'){
    & "$VivadoBin/xvlog.bat" --sv "$PSScriptRoot/tb_review.sv"
    if($LASTEXITCODE -ne 0){throw 'Reviewer TB compile failed'}
    $top='tb_review';$marker='REVIEW ALL PASS'
   }
   & "$VivadoBin/xelab.bat" "work.$top" -s snapshot
   if($LASTEXITCODE -ne 0){throw 'Elaboration failed'}
   & "$VivadoBin/xsim.bat" snapshot -runall -log simulation.log
   if($LASTEXITCODE -ne 0){throw 'Simulation failed'}
   $log=Get-Content simulation.log -Raw
   if(!$log.Contains($marker) -or $log -match '(?im)^\s*(FAIL\b|Fatal:|ERROR:|REVIEW FAIL|REVIEW TIMEOUT)'){throw 'Simulation marker check failed'}
  }finally{Pop-Location}
 }
}finally{$env:PROCESSOR_ARCHITECTURE=$prior}
