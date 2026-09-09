param([Parameter(Mandatory=$true)][string]$OutputDirectory,[string]$VivadoBin='F:/AMD/2025.2/Vivado/bin')
$ErrorActionPreference='Stop'
if(Test-Path -LiteralPath $OutputDirectory){throw 'Use a new output directory'}
$submission=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../submission'))
$resolvedOutput=[IO.Path]::GetFullPath($OutputDirectory)
if($resolvedOutput.Equals($submission,[StringComparison]::OrdinalIgnoreCase) -or $resolvedOutput.StartsWith($submission.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Output must be outside submission'}
New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
$previous=$env:PROCESSOR_ARCHITECTURE
if(!$previous -and [Environment]::Is64BitOperatingSystem){$env:PROCESSOR_ARCHITECTURE='AMD64'}
Push-Location $OutputDirectory
try {
 & "$VivadoBin/xvlog.bat" "$submission/rtl/stream_error_snapshot.v"
 if($LASTEXITCODE -ne 0){throw 'Verilog compile failed'}
 & "$VivadoBin/xvlog.bat" --sv "$submission/reference/stream_error_stats.sv" "$PSScriptRoot/tb_independent.sv"
 if($LASTEXITCODE -ne 0){throw 'Test compile failed'}
 & "$VivadoBin/xelab.bat" work.tb_independent -s independent -timescale 1ns/1ps
 if($LASTEXITCODE -ne 0){throw 'Elaboration failed'}
 & "$VivadoBin/xsim.bat" independent -runall -log simulation.log
 if($LASTEXITCODE -ne 0){throw 'Simulation failed'}
 $log=Get-Content simulation.log -Raw
 if($log -notmatch 'REVIEW ALL PASS' -or $log -match 'REVIEW FAIL|REVIEW JOINT FAIL|REVIEW TIMEOUT'){throw 'Missing success or detected failure'}
} finally {Pop-Location;$env:PROCESSOR_ARCHITECTURE=$previous}
