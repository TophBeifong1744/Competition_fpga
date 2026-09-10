param([Parameter(Mandatory=$true)][string]$VivadoBin,
 [string]$RunDirectory = (Join-Path ([IO.Path]::GetTempPath()) ('c004-sim-'+[guid]::NewGuid().ToString('N'))))
# Outputs: NEW external run directory with original logs. Next: review ALL TESTS PASS.
$ErrorActionPreference='Stop'
$package=Split-Path $PSScriptRoot -Parent
$run=[IO.Path]::GetFullPath($RunDirectory)
if ($run.StartsWith($package.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase) -or $run -eq $package) { throw 'Use a directory outside submission' }
if (Test-Path -LiteralPath $run) { throw 'Run directory must be new' }
if ((Get-FileHash -LiteralPath (Join-Path $package 'reference/stream_error_stats.sv')).Hash -ne '333dc4d193169982a6609c886a48968e87ef2631496d0c90137d24f228a94afe') { throw 'Core hash mismatch' }
New-Item -ItemType Directory -Path $run | Out-Null
$previousArchitecture=$env:PROCESSOR_ARCHITECTURE
if (!$env:PROCESSOR_ARCHITECTURE -and [Runtime.InteropServices.RuntimeInformation]::OSArchitecture -eq 'X64') { $env:PROCESSOR_ARCHITECTURE='AMD64' }
$started=Get-Date -Format o
function Invoke-Tool([string]$name,[string[]]$toolArgs) {
 & (Join-Path $VivadoBin $name) @toolArgs
 if ($LASTEXITCODE -ne 0) { throw "$name exit=$LASTEXITCODE" }
}
Push-Location $run
try {
 Invoke-Tool 'xvlog.bat' @('--sv',(Join-Path $package 'reference/stream_error_stats.sv'),'-log','compile-core.log')
 Invoke-Tool 'xvlog.bat' @((Join-Path $package 'rtl/stream_error_stats_bd.v'),'-log','compile-wrapper.log')
 Invoke-Tool 'xvlog.bat' @('--sv',(Join-Path $package 'tb/tb_stream_error_stats_bd.sv'),'-log','compile-tb.log')
 Invoke-Tool 'xelab.bat' @('work.tb_stream_error_stats_bd','-s','c004_test','-timescale','1ns/1ps','-log','elaborate.log')
 Invoke-Tool 'xsim.bat' @('c004_test','-runall','-log','simulate.log')
 $sim=Get-Content -Raw -LiteralPath 'simulate.log'
 if ($sim -notmatch 'ALL TESTS PASS' -or $sim -match '(?im)^\s*(FAIL\b|FATAL\b|ERROR\b|TIMEOUT\b)') { throw 'Simulation evidence failed' }
 @("Started=$started","Ended=$(Get-Date -Format o)",'RESULT=PASS',"RunDirectory=$run") | Set-Content -LiteralPath 'summary.txt'
 Write-Output "VERIFIED: $run"
} catch {
 @("Started=$started","Ended=$(Get-Date -Format o)","RESULT=FAIL $_") | Set-Content -LiteralPath 'summary.txt'
 throw
} finally { Pop-Location; $env:PROCESSOR_ARCHITECTURE=$previousArchitecture }
